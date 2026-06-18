use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::RwLock;

use anyhow::{Context, Error, Result};
use matchit::Router as MatchItRouter;
use pyo3::{Bound, Python};

use crate::routers::Router;
use crate::types::function_info::{FunctionInfo, MiddlewareType};

// A route may carry more than one middleware of the same kind (e.g. an
// `auth_required` handler plus a custom `@before_request`), so each route
// template maps to a *list* of middlewares run in registration order (#1158,
// #828). matchit stores a single value per template, hence the Vec.
type RouteMap = RwLock<MatchItRouter<Vec<FunctionInfo>>>;

pub struct MiddlewareRouter {
    globals: HashMap<MiddlewareType, RwLock<Vec<FunctionInfo>>>,
    routes: HashMap<MiddlewareType, RouteMap>,
    has_middleware: AtomicBool,
}

impl Router<(Vec<FunctionInfo>, HashMap<String, String>), MiddlewareType> for MiddlewareRouter {
    fn add_route<'py>(
        &self,
        _py: Python,
        route_type: &MiddlewareType,
        route: &str,
        function: FunctionInfo,
        _event_loop: Option<Bound<'py, pyo3::PyAny>>,
    ) -> Result<(), Error> {
        let table = self.routes.get(route_type).context("No relevant map")?;
        let mut table = table.write().unwrap();

        // Append to the existing chain if this route template is already
        // registered, otherwise start a new one. Registering the same route
        // template twice used to panic on the matchit insert conflict (#1158).
        if table.at(route).is_ok() {
            table.at_mut(route).unwrap().value.push(function);
        } else {
            table.insert(route.to_string(), vec![function])?;
        }
        self.has_middleware.store(true, Ordering::Release);

        Ok(())
    }

    fn get_route(
        &self,
        route_method: &MiddlewareType,
        route: &str,
    ) -> Option<(Vec<FunctionInfo>, HashMap<String, String>)> {
        let table = self.routes.get(route_method)?;

        let table_lock = table.read().ok()?;
        let res = table_lock.at(route).ok()?;
        let mut route_params = HashMap::new();
        for (key, value) in res.params.iter() {
            route_params.insert(key.to_string(), value.to_string());
        }

        let functions = Python::with_gil(|_| res.value.to_owned());

        Some((functions, route_params))
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
        Self {
            globals,
            routes,
            has_middleware: AtomicBool::new(false),
        }
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
        self.has_middleware.store(true, Ordering::Release);
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

    pub fn has_any_middleware(&self) -> bool {
        self.has_middleware.load(Ordering::Acquire)
    }
}
