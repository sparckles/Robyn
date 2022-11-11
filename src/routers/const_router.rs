use std::collections::HashMap;
use std::str::FromStr;
use std::sync::Arc;
use std::sync::RwLock;
// pyo3 modules
use crate::executors::execute_function;
use anyhow::Context;
use log::debug;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;

use anyhow::{Error, Result};

use super::Router;

type RouteMap = RwLock<matchit::Router<String>>;

/// Contains the thread safe hashmaps of different routes
pub struct ConstRouter {
    routes: HashMap<Method, Arc<RouteMap>>,
}

impl Router<String, Method> for ConstRouter {
    /// Doesn't allow query params/body/etc as variables cannot be "memoized"/"const"ified
    fn add_route(
        &self,
        route_type: &str, // we can just have route type as WS
        route: &str,
        function: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        event_loop: Option<&PyAny>,
    ) -> Result<(), Error> {
        let table = self
            .get_relevant_map_str(route_type)
            .context("No relevant map")?
            .clone();

        let route = route.to_string();
        let event_loop =
            event_loop.context("Event loop must be provided to add a route to the const router")?;

        pyo3_asyncio::tokio::run_until_complete(event_loop, async move {
            let output = execute_function(function, number_of_params, is_async)
                .await
                .unwrap();
            debug!("This is the result of the output {:?}", output);
            table
                .write()
                .unwrap()
                .insert(route, output.get("body").unwrap().to_string())
                .unwrap();
            Ok(())
        })?;

        Ok(())
    }

    fn get_route(&self, route_method: Method, route: &str) -> Option<String> {
        let table = self.routes.get(&route_method)?;
        let route_map = table.read().ok()?;

        match route_map.at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        }
    }
}

impl ConstRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(Method::GET, Arc::new(RwLock::new(matchit::Router::new())));
        routes.insert(Method::POST, Arc::new(RwLock::new(matchit::Router::new())));
        routes.insert(Method::PUT, Arc::new(RwLock::new(matchit::Router::new())));
        routes.insert(
            Method::DELETE,
            Arc::new(RwLock::new(matchit::Router::new())),
        );
        routes.insert(Method::PATCH, Arc::new(RwLock::new(matchit::Router::new())));
        routes.insert(Method::HEAD, Arc::new(RwLock::new(matchit::Router::new())));
        routes.insert(
            Method::OPTIONS,
            Arc::new(RwLock::new(matchit::Router::new())),
        );
        routes.insert(
            Method::CONNECT,
            Arc::new(RwLock::new(matchit::Router::new())),
        );
        routes.insert(Method::TRACE, Arc::new(RwLock::new(matchit::Router::new())));
        Self { routes }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&Arc<RouteMap>> {
        match route {
            "WS" => None,
            _ => self.routes.get(&Method::from_str(route).ok()?),
        }
    }
}
