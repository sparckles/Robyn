use parking_lot::RwLock;
use std::collections::HashMap;
use std::sync::Arc;

use crate::executors::execute_http_function;
use crate::types::function_info::FunctionInfo;
use crate::types::request::Request;
use crate::types::response::Response;
use crate::types::HttpMethod;
use anyhow::Context;
use log::debug;
use matchit::Router as MatchItRouter;
use pyo3::{Bound, PyErr, Python};

use anyhow::{Error, Result};

use crate::routers::Router;

type RouteMap = RwLock<MatchItRouter<Response>>;

/// Contains the thread safe hashmaps of different routes
pub struct ConstRouter {
    routes: HashMap<HttpMethod, Arc<RouteMap>>,
}

impl Router<Response, HttpMethod> for ConstRouter {
    /// Doesn't allow query params/body/etc as variables cannot be "memoized"/"const"ified
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
            debug!("This is the result of the output {:?}", output);
            // Const routes only support standard responses, not streaming
            match output {
                crate::types::response::ResponseType::Standard(response) => {
                    table.write().insert(route, response).unwrap();
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
        let table = self.routes.get(route_method)?;
        let route_map = table.read();

        match route_map.at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        }
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
}
