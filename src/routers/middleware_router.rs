use std::collections::HashMap;
use std::sync::RwLock;

use anyhow::{Context, Error, Result};
use matchit::Router as MatchItRouter;
use pyo3::types::PyAny;

use crate::routers::Router;
use crate::types::function_info::{FunctionInfo, MiddlewareType};

type RouteMap = RwLock<MatchItRouter<FunctionInfo>>;

/// Contains the thread safe hashmaps of different routes
pub struct MiddlewareRouter {
    globals: HashMap<MiddlewareType, RwLock<Vec<FunctionInfo>>>,
    routes: HashMap<MiddlewareType, RouteMap>,
}

impl Router<(FunctionInfo, HashMap<String, String>), MiddlewareType> for MiddlewareRouter {
    fn add_route(
        &self,
        route_type: &MiddlewareType,
        route: &str,
        function: FunctionInfo,
        _event_loop: Option<&PyAny>,
    ) -> Result<(), Error> {
        let table = self.routes.get(route_type).context("No relevant map")?;

        table.write().unwrap().insert(route.to_string(), function)?;

        Ok(())
    }

    fn get_route(
        &self,
        route_method: &MiddlewareType,
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
        let mut globals = HashMap::new();
        globals.insert(MiddlewareType::BeforeRequest, RwLock::new(vec![]));
        globals.insert(MiddlewareType::AfterRequest, RwLock::new(vec![]));
        let mut routes = HashMap::new();
        routes.insert(
            MiddlewareType::BeforeRequest,
            RwLock::new(MatchItRouter::new()),
        );
        routes.insert(
            MiddlewareType::AfterRequest,
            RwLock::new(MatchItRouter::new()),
        );
        Self { globals, routes }
    }

    pub fn add_global_middleware(
        &self,
        middleware_type: &MiddlewareType,
        function: FunctionInfo,
    ) -> Result<()> {
        self.globals
            .get(middleware_type)
            .context("No relevant map")?
            .write()
            .unwrap()
            .push(function);
        Ok(())
    }

    pub fn get_global_middlewares(&self, middleware_type: &MiddlewareType) -> Vec<FunctionInfo> {
        self.globals
            .get(middleware_type)
            .unwrap()
            .read()
            .unwrap()
            .to_vec()
    }
}
