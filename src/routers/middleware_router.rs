use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use matchit::Router;

use anyhow::{bail, Error, Result};

use super::router::RouteType;

/// Contains the thread safe hashmaps of different routes

pub struct MiddlewareRouter {
    before_request: RwLock<Router<(PyFunction, u8)>>,
    after_request: RwLock<Router<(PyFunction, u8)>>,
}

impl MiddlewareRouter {
    pub fn new() -> Self {
        Self {
            before_request: RwLock::new(Router::new()),
            after_request: RwLock::new(Router::new()),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: RouteType) -> Option<&RwLock<Router<(PyFunction, u8)>>> {
        match route {
            RouteType::BeforeRequest => Some(&self.before_request),
            RouteType::AfterRequest => Some(&self.after_request),
        }
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(
        &self,
        route_type: RouteType, // we can just have route type as WS
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
    ) -> Result<(), Error> {
        let table = match self.get_relevant_map(route_type) {
            Some(table) => table,
            None => bail!("No relevant map"),
        };

        let function = if is_async {
            PyFunction::CoRoutine(handler)
        } else {
            PyFunction::SyncFunction(handler)
        };

        table
            .write()
            .unwrap()
            .insert(route.to_string(), (function, number_of_params))?;

        Ok(())
    }

    pub fn get_route(
        &self,
        route_method: RouteType,
        route: &str, // check for the route method here
    ) -> Option<((PyFunction, u8), HashMap<String, String>)> {
        // need to split this function in multiple smaller functions
        let table = self.get_relevant_map(route_method)?;

        match table.read().unwrap().at(route) {
            Ok(res) => {
                let mut route_params = HashMap::new();

                for (key, value) in res.params.iter() {
                    route_params.insert(key.to_string(), value.to_string());
                }

                Some((res.value.clone(), route_params))
            }
            Err(_) => None,
        }
    }
}
