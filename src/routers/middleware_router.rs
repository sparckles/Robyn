use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use anyhow::{Context, Error, Result};

use crate::routers::types::MiddlewareRoute;

use super::Router;

type RouteMap = RwLock<matchit::Router<(PyFunction, u8)>>;

/// Contains the thread safe hashmaps of different routes
pub struct MiddlewareRouter {
    routes: HashMap<MiddlewareRoute, RouteMap>,
}

impl MiddlewareRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(
            MiddlewareRoute::BeforeRequest,
            RwLock::new(matchit::Router::new()),
        );
        routes.insert(
            MiddlewareRoute::AfterRequest,
            RwLock::new(matchit::Router::new()),
        );
        Self { routes }
    }
}

impl Router<((PyFunction, u8), HashMap<String, String>), MiddlewareRoute> for MiddlewareRouter {
    fn add_route(
        &self,
        route_type: &str,
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        _event_loop: Option<&PyAny>,
    ) -> Result<(), Error> {
        let table = self
            .routes
            .get(&MiddlewareRoute::from_str(route_type))
            .context("No relevant map")?;

        let function = match is_async {
            true => PyFunction::CoRoutine(handler),
            false => PyFunction::SyncFunction(handler),
        };

        table
            .write()
            .unwrap()
            .insert(route.to_string(), (function, number_of_params))?;

        Ok(())
    }

    fn get_route(
        &self,
        route_method: MiddlewareRoute,
        route: &str,
    ) -> Option<((PyFunction, u8), HashMap<String, String>)> {
        let table = self.routes.get(&route_method)?;

        let table_lock = table.read().ok()?;
        let res = table_lock.at(route).ok()?;
        let mut route_params = HashMap::new();
        for (key, value) in res.params.iter() {
            route_params.insert(key.to_string(), value.to_string());
        }

        Some((res.value.to_owned(), route_params))
    }
}
