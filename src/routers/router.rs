use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Node;

/// Contains the thread safe hashmaps of different routes

pub struct Router {
    get_routes: RwLock<Node<(PyFunction, u8)>>,
    post_routes: RwLock<Node<(PyFunction, u8)>>,
    put_routes: RwLock<Node<(PyFunction, u8)>>,
    delete_routes: RwLock<Node<(PyFunction, u8)>>,
    patch_routes: RwLock<Node<(PyFunction, u8)>>,
    head_routes: RwLock<Node<(PyFunction, u8)>>,
    options_routes: RwLock<Node<(PyFunction, u8)>>,
    connect_routes: RwLock<Node<(PyFunction, u8)>>,
    trace_routes: RwLock<Node<(PyFunction, u8)>>,
}

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: RwLock::new(Node::new()),
            post_routes: RwLock::new(Node::new()),
            put_routes: RwLock::new(Node::new()),
            delete_routes: RwLock::new(Node::new()),
            patch_routes: RwLock::new(Node::new()),
            head_routes: RwLock::new(Node::new()),
            options_routes: RwLock::new(Node::new()),
            connect_routes: RwLock::new(Node::new()),
            trace_routes: RwLock::new(Node::new()),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: Method) -> Option<&RwLock<Node<(PyFunction, u8)>>> {
        match route {
            Method::GET => Some(&self.get_routes),
            Method::POST => Some(&self.post_routes),
            Method::PUT => Some(&self.put_routes),
            Method::PATCH => Some(&self.patch_routes),
            Method::DELETE => Some(&self.delete_routes),
            Method::HEAD => Some(&self.head_routes),
            Method::OPTIONS => Some(&self.options_routes),
            Method::CONNECT => Some(&self.connect_routes),
            Method::TRACE => Some(&self.trace_routes),
            _ => None,
        }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&RwLock<Node<(PyFunction, u8)>>> {
        if route != "WS" {
            let method = match Method::from_bytes(route.as_bytes()) {
                Ok(res) => res,
                Err(_) => return None,
            };

            return self.get_relevant_map(method);
        } else {
            return None;
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
        let table = match self.get_relevant_map_str(route_type) {
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

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn get_route(
        &self,
        route_method: Method,
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
