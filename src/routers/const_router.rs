use actix_http::StatusCode;
use actix_web::{web::Bytes, HttpResponse, HttpResponseBuilder};
use parking_lot::RwLock;
use std::collections::HashMap;
use std::sync::Arc;

use crate::executors::execute_http_function;
use crate::types::cookie::Cookies;
use crate::types::function_info::FunctionInfo;
use crate::types::headers::Headers;
use crate::types::request::Request;
use crate::types::response::Response;
use crate::types::HttpMethod;
use anyhow::Context;
use matchit::Router as MatchItRouter;
use pyo3::{Bound, PyErr, Python};

use anyhow::{Error, Result};

use crate::routers::Router;

/// Pre-built response for const routes — zero per-request allocation.
/// Headers (including global response headers) are baked in at startup.
#[derive(Clone)]
pub struct CachedResponse {
    pub status: StatusCode,
    pub headers: Arc<Vec<(String, String)>>,
    pub body: Bytes,
    route_header_count: usize,
}

impl CachedResponse {
    fn from_response(response: &Response) -> Self {
        let mut headers = Vec::new();
        for entry in response.headers.headers.iter() {
            let (key, values) = entry.pair();
            for value in values {
                headers.push((key.clone(), value.clone()));
            }
        }
        for (name, cookie) in &response.cookies.cookies {
            if let Ok(header_value) = cookie.to_header_value(name) {
                headers.push(("set-cookie".to_string(), header_value));
            }
        }
        let route_header_count = headers.len();
        Self {
            status: StatusCode::from_u16(response.status_code)
                .unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            headers: Arc::new(headers),
            body: Bytes::from(response.description.clone()),
            route_header_count,
        }
    }

    #[inline(always)]
    pub fn to_http_response(&self) -> HttpResponse {
        let mut builder = HttpResponseBuilder::new(self.status);
        for (k, v) in self.headers.as_ref() {
            builder.append_header((k.as_str(), v.as_str()));
        }
        builder.body(self.body.clone())
    }

    #[inline(always)]
    pub fn to_http_response_without_global_headers(&self) -> HttpResponse {
        let mut builder = HttpResponseBuilder::new(self.status);
        for (k, v) in self.headers.as_ref().iter().take(self.route_header_count) {
            builder.append_header((k.as_str(), v.as_str()));
        }
        builder.body(self.body.clone())
    }
}

type RouteMap = RwLock<MatchItRouter<CachedResponse>>;

/// Fast const-route lookup table: exact path → CachedResponse.
/// Uses a simple HashMap (no regex, no path params, no RwLock per lookup).
type FastMap = RwLock<HashMap<String, CachedResponse>>;

pub struct ConstRouter {
    routes: HashMap<HttpMethod, Arc<RouteMap>>,
    fast_routes: HashMap<HttpMethod, Arc<FastMap>>,
}

impl Router<Response, HttpMethod> for ConstRouter {
    fn add_route<'py>(
        &self,
        _py: Python,
        route_type: &HttpMethod,
        route: &str,
        function: FunctionInfo,
        event_loop: Option<Bound<'py, pyo3::PyAny>>,
    ) -> Result<(), Error> {
        let table = Arc::clone(self.routes.get(route_type).context("No relevant map")?);
        let fast_table = Arc::clone(
            self.fast_routes
                .get(route_type)
                .context("No relevant fast map")?,
        );

        let route = route.to_string();
        let event_loop =
            event_loop.context("Event loop must be provided to add a route to the const router")?;

        pyo3_async_runtimes::tokio::run_until_complete(event_loop, async move {
            let output = execute_http_function(&Request::default(), &function, None)
                .await
                .unwrap();
            match output {
                crate::types::response::ResponseType::Standard(response) => {
                    let cached = CachedResponse::from_response(&response);
                    table.write().insert(route.clone(), cached.clone()).unwrap();
                    fast_table.write().insert(route, cached);
                }
                crate::types::response::ResponseType::Streaming(_) => {
                    return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "Streaming responses are not supported for const routes",
                    )
                    .into());
                }
            }
            Ok(())
        })?;

        Ok(())
    }

    fn get_route(&self, route_method: &HttpMethod, route: &str) -> Option<Response> {
        let cached = self.get_cached_route(route_method, route)?;
        let mut resp = Response {
            status_code: cached.status.as_u16(),
            response_type: "text".to_string(),
            headers: Headers::new(None),
            description: cached.body.to_vec(),
            file_path: None,
            cookies: Cookies::new(),
        };
        for (k, v) in cached.headers.as_ref() {
            resp.headers.set(k.clone(), v.clone());
        }
        Some(resp)
    }
}

impl ConstRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        let mut fast_routes = HashMap::new();
        for method in [
            HttpMethod::GET,
            HttpMethod::POST,
            HttpMethod::PUT,
            HttpMethod::DELETE,
            HttpMethod::PATCH,
            HttpMethod::HEAD,
            HttpMethod::OPTIONS,
            HttpMethod::CONNECT,
            HttpMethod::TRACE,
        ] {
            routes.insert(method.clone(), Arc::new(RwLock::new(MatchItRouter::new())));
            fast_routes.insert(method, Arc::new(RwLock::new(HashMap::new())));
        }
        Self {
            routes,
            fast_routes,
        }
    }

    /// Bake global response headers into all cached responses.
    /// Called once at server start, after global headers are set.
    pub fn bake_global_headers(&self, global_headers: &Headers) {
        let mut extra_headers: Vec<(String, String)> = Vec::new();
        for entry in global_headers.headers.iter() {
            let (key, values) = entry.pair();
            for value in values {
                extra_headers.push((key.clone(), value.clone()));
            }
        }
        if extra_headers.is_empty() {
            return;
        }
        for (method, fast_table) in &self.fast_routes {
            let mut map = fast_table.write();
            for cached in map.values_mut() {
                let mut combined = cached.headers.as_ref().clone();
                combined.extend(extra_headers.iter().cloned());
                cached.headers = Arc::new(combined);
            }

            if let Some(route_table) = self.routes.get(method) {
                let mut new_router = MatchItRouter::new();
                for (route, cached) in map.iter() {
                    let _ = new_router.insert(route.clone(), cached.clone());
                }
                *route_table.write() = new_router;
            }
        }
    }

    /// Fast lookup: tries exact HashMap first, falls back to matchit for parameterized/wildcard routes.
    #[inline(always)]
    pub fn get_cached_route(
        &self,
        route_method: &HttpMethod,
        route: &str,
    ) -> Option<CachedResponse> {
        let fast_table = self.fast_routes.get(route_method)?;
        {
            let map = fast_table.read();
            if let Some(cached) = map.get(route) {
                return Some(cached.clone());
            }
        }

        let route_table = self.routes.get(route_method)?;
        let router = route_table.read();
        router.at(route).ok().map(|matched| matched.value.clone())
    }
}
