use dashmap::DashMap;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;
use std::sync::{Arc, RwLock};

use actix_web::http::Method;

use matchit::Node;

#[derive(Clone)]
pub struct Routing {
    get_routes: Node<PyFunction>,
    post_routes: Node<PyFunction>,
    put_routes: Node<PyFunction>,
    delete_routes: Node<PyFunction>,
    patch_routes: Node<PyFunction>,
    head_routes: Node<PyFunction>,
    options_routes: Node<PyFunction>,
    connect_routes: Node<PyFunction>,
    trace_routes: Node<PyFunction>,
}

impl Routing {
    pub fn new(router: &Router) -> Routing {
        let get_routes = Router::protocol_to_tree(&router.get_routes);
        let post_routes = Router::protocol_to_tree(&router.post_routes);
        let put_routes = Router::protocol_to_tree(&router.put_routes);
        let delete_routes = Router::protocol_to_tree(&router.delete_routes);
        let patch_routes = Router::protocol_to_tree(&router.patch_routes);
        let head_routes = Router::protocol_to_tree(&router.head_routes);
        let options_routes = Router::protocol_to_tree(&router.options_routes);
        let connect_routes = Router::protocol_to_tree(&router.connect_routes);
        let trace_routes = Router::protocol_to_tree(&router.trace_routes);

        Self {
            get_routes,
            post_routes,
            put_routes,
            delete_routes,
            patch_routes,
            head_routes,
            options_routes,
            connect_routes,
            trace_routes,
        }
    }

    #[inline(always)]
    fn get_relevant_map(&self, route: &Method) -> Option<&Node<PyFunction>> {
        match route {
            &Method::GET => Some(&self.get_routes),
            &Method::POST => Some(&self.post_routes),
            &Method::PUT => Some(&self.put_routes),
            &Method::PATCH => Some(&self.patch_routes),
            &Method::DELETE => Some(&self.delete_routes),
            &Method::HEAD => Some(&self.head_routes),
            &Method::OPTIONS => Some(&self.options_routes),
            &Method::CONNECT => Some(&self.connect_routes),
            &Method::TRACE => Some(&self.trace_routes),
            _ => None,
        }
    }

    #[inline(always)]
    pub fn get_route(&self, route_method: &Method, route: &str) -> Option<PyFunction> {
        println!("Hello world how are your");
        let table = &self.get_relevant_map(route_method)?;

        let x = match table.at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        };

        x
    }
}

// Contains the thread safe hashmaps of different routes
pub struct Router {
    get_routes: DashMap<String, PyFunction>,
    post_routes: DashMap<String, PyFunction>,
    put_routes: DashMap<String, PyFunction>,
    delete_routes: DashMap<String, PyFunction>,
    patch_routes: DashMap<String, PyFunction>,
    head_routes: DashMap<String, PyFunction>,
    options_routes: DashMap<String, PyFunction>,
    connect_routes: DashMap<String, PyFunction>,
    trace_routes: DashMap<String, PyFunction>,
}

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: DashMap::new(),
            post_routes: DashMap::new(),
            put_routes: DashMap::new(),
            delete_routes: DashMap::new(),
            patch_routes: DashMap::new(),
            head_routes: DashMap::new(),
            options_routes: DashMap::new(),
            connect_routes: DashMap::new(),
            trace_routes: DashMap::new(),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: &Method) -> Option<&DashMap<String, PyFunction>> {
        match route {
            &Method::GET => Some(&self.get_routes),
            &Method::POST => Some(&self.post_routes),
            &Method::PUT => Some(&self.put_routes),
            &Method::PATCH => Some(&self.patch_routes),
            &Method::DELETE => Some(&self.delete_routes),
            &Method::HEAD => Some(&self.head_routes),
            &Method::OPTIONS => Some(&self.options_routes),
            &Method::CONNECT => Some(&self.connect_routes),
            &Method::TRACE => Some(&self.trace_routes),
            _ => None,
        }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&DashMap<String, PyFunction>> {
        let method = match Method::from_bytes(route.as_bytes()) {
            Ok(res) => res,
            Err(_) => return None,
        };

        self.get_relevant_map(&method)
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>, is_async: bool) {
        let table = match self.get_relevant_map_str(route_type) {
            Some(table) => table,
            None => return,
        };

        let function = if is_async {
            PyFunction::CoRoutine(handler)
        } else {
            PyFunction::SyncFunction(handler)
        };

        table.insert(route.to_string(), function);
    }

    pub fn get_route(&self, route_method: Method, route: &str) -> Option<PyFunction> {
        let table = self.get_relevant_map(&route_method)?;
        Some(table.get(route)?.clone())
    }

    pub fn protocol_to_tree(incoming: &DashMap<String, PyFunction>) -> Node<PyFunction> {
        let mut tree = Node::new();

        for item in incoming.iter() {
            tree.insert(item.key().clone(), item.value().clone())
                .unwrap();
        }

        tree
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
