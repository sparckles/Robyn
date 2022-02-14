use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Node;

/// Contains the thread safe hashmaps of different routes

pub struct MiddlewareRouter {
    before_request: RwLock<Node<(PyFunction, u8)>>,
    after_request: RwLock<Node<(PyFunction, u8)>>,
}

impl MiddlewareRouter {
    pub fn new() -> Self {
        Self {
            before_request: RwLock::new(Node::new()),
            after_request: RwLock::new(Node::new()),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: &str) -> Option<&RwLock<Node<(PyFunction, u8)>>> {
        match route {
            "BEFORE_REQUEST" => Some(&self.before_request),
            "AFTER_REQUEST" => Some(&self.after_request),
            _ => None,
        }
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(
        &self,
        route_type: &str, // we can just have route type as WS
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
    ) {
        let table = match self.get_relevant_map(route_type) {
            Some(table) => table,
            None => return,
        };

        let function = if is_async {
            PyFunction::CoRoutine(handler)
        } else {
            PyFunction::SyncFunction(handler)
        };

        table
            .write()
            .unwrap()
            .insert(route.to_string(), (function, number_of_params))
            .unwrap();
    }

    pub fn get_route(
        &self,
        route_method: &str,
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
