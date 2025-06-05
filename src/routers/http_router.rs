use parking_lot::RwLock;
use pyo3::{Bound, Python};
use std::collections::HashMap;

use matchit::Router as MatchItRouter;

use anyhow::{Context, Result};

use crate::routers::Router;
use crate::types::function_info::FunctionInfo;
use crate::types::HttpMethod;

type RouteMap = RwLock<MatchItRouter<FunctionInfo>>;

/// Contains the thread safe hashmaps of different routes
pub struct HttpRouter {
    routes: HashMap<HttpMethod, RouteMap>,
}

impl Router<(FunctionInfo, HashMap<String, String>), HttpMethod> for HttpRouter {
    fn add_route<'py>(
        &self,
        _py: Python,
        route_type: &HttpMethod,
        route: &str,
        function: FunctionInfo,
        _event_loop: Option<Bound<'py, pyo3::PyAny>>,
    ) -> Result<()> {
        let table = self.routes.get(route_type).context("No relevant map")?;

        // try removing unwrap here
        table.write().insert(route.to_string(), function)?;

        Ok(())
    }

    fn get_route(
        &self,
        route_method: &HttpMethod,
        route: &str,
    ) -> Option<(FunctionInfo, HashMap<String, String>)> {
        let table = self.routes.get(route_method)?;

        let table_lock = table.read();
        let res = table_lock.at(route).ok()?;
        let mut route_params = HashMap::new();
        for (key, value) in res.params.iter() {
            route_params.insert(key.to_string(), value.to_string());
        }

        let function_info = Python::with_gil(|_| res.value.to_owned());

        Some((function_info, route_params))
    }
}

impl HttpRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(HttpMethod::GET, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::POST, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::PUT, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::DELETE, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::PATCH, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::HEAD, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::OPTIONS, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::CONNECT, RwLock::new(MatchItRouter::new()));
        routes.insert(HttpMethod::TRACE, RwLock::new(MatchItRouter::new()));
        Self { routes }
    }
}
