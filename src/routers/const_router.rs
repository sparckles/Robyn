use actix_http::StatusCode;
use actix_web::{HttpResponse, HttpResponseBuilder, web::Bytes};
use parking_lot::RwLock;
use std::collections::HashMap;
use std::sync::Arc;

use crate::executors::execute_http_function;
use crate::types::function_info::FunctionInfo;
use crate::types::request::Request;
use crate::types::response::Response;
use crate::types::headers::Headers;
use crate::types::HttpMethod;
use anyhow::Context;
use matchit::Router as MatchItRouter;
use pyo3::{Bound, PyErr, Python};

use anyhow::{Error, Result};

use crate::routers::Router;

/// Pre-built response for const routes, avoids DashMap clone per request
#[derive(Clone)]
pub struct CachedResponse {
    pub status: StatusCode,
    pub headers: Arc<Vec<(String, String)>>,
    pub body: Bytes,
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
        Self {
            status: StatusCode::from_u16(response.status_code)
                .unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            headers: Arc::new(headers),
            body: Bytes::from(response.description.clone()),
        }
    }

    #[inline]
    pub fn to_http_response(&self, global_headers: &Headers) -> HttpResponse {
        let mut builder = HttpResponseBuilder::new(self.status);
        for (k, v) in self.headers.as_ref() {
            builder.append_header((k.as_str(), v.as_str()));
        }
        for entry in global_headers.headers.iter() {
            let (key, values) = entry.pair();
            for value in values {
                builder.append_header((key.as_str(), value.as_str()));
            }
        }
        builder.body(self.body.clone())
    }
}

type RouteMap = RwLock<MatchItRouter<CachedResponse>>;

pub struct ConstRouter {
    routes: HashMap<HttpMethod, Arc<RouteMap>>,
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

        let route = route.to_string();
        let event_loop =
            event_loop.context("Event loop must be provided to add a route to the const router")?;

        pyo3_async_runtimes::tokio::run_until_complete(event_loop, async move {
            let output = execute_http_function(&Request::default(), &function)
                .await
                .unwrap();
            match output {
                crate::types::response::ResponseType::Standard(response) => {
                    let cached = CachedResponse::from_response(&response);
                    table.write().insert(route, cached).unwrap();
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
        None
    }
}

impl ConstRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(HttpMethod::GET, Arc::new(RwLock::new(MatchItRouter::new())));
        routes.insert(
            HttpMethod::POST,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(HttpMethod::PUT, Arc::new(RwLock::new(MatchItRouter::new())));
        routes.insert(
            HttpMethod::DELETE,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(
            HttpMethod::PATCH,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(
            HttpMethod::HEAD,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(
            HttpMethod::OPTIONS,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(
            HttpMethod::CONNECT,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        routes.insert(
            HttpMethod::TRACE,
            Arc::new(RwLock::new(MatchItRouter::new())),
        );
        Self { routes }
    }

    /// Fast lookup for const routes — returns a CachedResponse without deep cloning
    #[inline]
    pub fn get_cached_route(
        &self,
        route_method: &HttpMethod,
        route: &str,
    ) -> Option<CachedResponse> {
        let table = self.routes.get(route_method)?;
        let route_map = table.read();
        match route_map.at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        }
    }
}
