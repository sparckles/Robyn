use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::FunctionInfo;
use anyhow::{Context, Error, Result};
use matchit::Router as MatchItRouter;
use pyo3::types::PyAny;

use crate::routers::types::MiddlewareRoute;

use super::Router;

type RouteMap = RwLock<MatchItRouter<FunctionInfo>>;

/// Contains the thread safe hashmaps of different routes
pub struct MiddlewareRouter {
    routes: HashMap<MiddlewareRoute, RouteMap>,
}

impl Router<(FunctionInfo, HashMap<String, String>), MiddlewareRoute> for MiddlewareRouter {
    fn add_route(
        &self,
        route_type: &str,
        route: &str,
        function: FunctionInfo,
        _event_loop: Option<&PyAny>,
    ) -> Result<(), Error> {
        let table = self
            .routes
            .get(&MiddlewareRoute::from_str(route_type))
            .context("No relevant map")?;

        table.write().unwrap().insert(route.to_string(), function)?;

        Ok(())
    }

    fn get_route(
        &self,
        route_method: &MiddlewareRoute,
        route: &str,
    ) -> Option<(FunctionInfo, HashMap<String, String>)> {
        let table = self.routes.get(route_method)?;

        let table_lock = table.read().ok()?;
        let res = table_lock.at(route).ok()?;
        let mut route_params = HashMap::new();
        for (key, value) in res.params.iter() {
            route_params.insert(key.to_string(), value.to_string());
        }

        Some((res.value.to_owned(), route_params))
    }
}

impl MiddlewareRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(
            MiddlewareRoute::BeforeRequest,
            RwLock::new(MatchItRouter::new()),
        );
        routes.insert(
            MiddlewareRoute::AfterRequest,
            RwLock::new(MatchItRouter::new()),
        );
        Self { routes }
    }
}
