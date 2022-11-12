use std::sync::RwLock;
use std::{collections::HashMap, str::FromStr};
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Router as MatchItRouter;

use anyhow::{Context, Result};

use super::Router;

type RouteMap = RwLock<MatchItRouter<(PyFunction, u8)>>;

/// Contains the thread safe hashmaps of different routes
pub struct HttpRouter {
    routes: HashMap<Method, RouteMap>,
}

impl Router<((PyFunction, u8), HashMap<String, String>), Method> for HttpRouter {
    fn add_route(
        &self,
        route_type: &str, // We can just have route type as WS
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        _event_loop: Option<&PyAny>,
    ) -> Result<()> {
        let table = self
            .get_relevant_map_str(route_type)
            .context("No relevant map")?;

        let function = match is_async {
            true => PyFunction::CoRoutine(handler),
            false => PyFunction::SyncFunction(handler),
        };

        // try removing unwrap here
        table
            .write()
            .unwrap()
            .insert(route.to_string(), (function, number_of_params))?;

        Ok(())
    }

    fn get_route(
        &self,
        route_method: Method,
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

impl HttpRouter {
    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(Method::GET, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::POST, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::PUT, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::DELETE, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::PATCH, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::HEAD, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::OPTIONS, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::CONNECT, RwLock::new(MatchItRouter::new()));
        routes.insert(Method::TRACE, RwLock::new(MatchItRouter::new()));
        Self { routes }
    }

    #[inline]
    fn get_relevant_map_str(
        &self,
        route: &str,
    ) -> Option<&RwLock<MatchItRouter<(PyFunction, u8)>>> {
        match route {
            "WS" => None,
            _ => self.routes.get(&Method::from_str(route).ok()?),
        }
    }
}
