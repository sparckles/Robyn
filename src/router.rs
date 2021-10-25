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
    fn get_relevant_map_str(&self, route: &str) -> Option<&Arc<RwLock<Node<(PyFunction, u8)>>>> {
        let method = match Method::from_bytes(route.as_bytes()) {
            Ok(res) => res,
            Err(_) => return None,
        };

        self.get_relevant_map(method)
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(
        &self,
        route_type: &str,
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

    pub fn get_route(
        &self,
        route_method: Method,
        route: &str,
    ) -> Option<((PyFunction, u8), HashMap<String, String>)> {
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

// #[cfg(test)]
// mod router_test {
//     use super::*;
//     #[test]
//     fn test_no_route() {
//         let router = Router::new();
//         assert_eq!(router.get_route(Method::GET, "/").is_none(), true);
//         // let handler = Python::with_gil(|py| {
//         //     let dict = pyo3::types::PyDict::new(py);
//         //     assert!(dict.is_instance::<PyAny>().unwrap());
//         //     let any: Py<PyAny> = dict.into_py(py);
//         //     any
//         // });
//         // router.add_route("GET", "/", handler, false);
//         // assert_eq!(router.get_route(Method::GET, "/").is_some(), true);
//     }
// }
