use std::collections::HashMap;
use std::sync::{Arc, RwLock};
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Node;

/// Contains the thread safe hashmaps of different routes

pub struct Router {
    get_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    post_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    put_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    delete_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    patch_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    head_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    options_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    connect_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    trace_routes: Arc<RwLock<Node<(PyFunction, u8)>>>,
    web_socket_routes: Arc<RwLock<HashMap<String, HashMap<String, (PyFunction, u8)>>>>,
}

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: Arc::new(RwLock::new(Node::new())),
            post_routes: Arc::new(RwLock::new(Node::new())),
            put_routes: Arc::new(RwLock::new(Node::new())),
            delete_routes: Arc::new(RwLock::new(Node::new())),
            patch_routes: Arc::new(RwLock::new(Node::new())),
            head_routes: Arc::new(RwLock::new(Node::new())),
            options_routes: Arc::new(RwLock::new(Node::new())),
            connect_routes: Arc::new(RwLock::new(Node::new())),
            trace_routes: Arc::new(RwLock::new(Node::new())),
            web_socket_routes: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: Method) -> Option<&Arc<RwLock<Node<(PyFunction, u8)>>>> {
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
    pub fn get_web_socket_map(
        &self,
    ) -> &Arc<RwLock<HashMap<String, HashMap<String, (PyFunction, u8)>>>> {
        &self.web_socket_routes
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&Arc<RwLock<Node<(PyFunction, u8)>>>> {
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
    pub fn add_websocket_route(
        &self,
        route: &str,
        connect_route: (Py<PyAny>, bool, u8),
        close_route: (Py<PyAny>, bool, u8),
        message_route: (Py<PyAny>, bool, u8),
    ) {
        let table = self.get_web_socket_map();
        let (connect_route_function, connect_route_is_async, connect_route_params) = connect_route;
        let (close_route_function, close_route_is_async, close_route_params) = close_route;
        let (message_route_function, message_route_is_async, message_route_params) = message_route;

        let insert_in_router =
            |handler: Py<PyAny>, is_async: bool, number_of_params: u8, socket_type: &str| {
                let function = if is_async {
                    PyFunction::CoRoutine(handler)
                } else {
                    PyFunction::SyncFunction(handler)
                };

                println!("socket type is {:?} {:?}", table, route);

                table
                    .write()
                    .unwrap()
                    .entry(route.to_string())
                    .or_default()
                    .insert(socket_type.to_string(), (function, number_of_params))
            };

        insert_in_router(
            connect_route_function,
            connect_route_is_async,
            connect_route_params,
            "connect",
        );

        insert_in_router(
            close_route_function,
            close_route_is_async,
            close_route_params,
            "close",
        );

        insert_in_router(
            message_route_function,
            message_route_is_async,
            message_route_params,
            "message",
        );
    }

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
