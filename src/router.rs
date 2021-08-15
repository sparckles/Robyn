use dashmap::DashMap;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;

/// Contains the thread safe hashmaps of different routes
pub struct Router {
    get_routes: DashMap<String, PyFunction>,
    post_routes: DashMap<String, PyFunction>,
    put_routes: DashMap<String, PyFunction>,
    delete_routes: DashMap<String, PyFunction>,
    patch_routes: DashMap<String, PyFunction>,
}

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: DashMap::new(),
            post_routes: DashMap::new(),
            put_routes: DashMap::new(),
            delete_routes: DashMap::new(),
            patch_routes: DashMap::new(),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: Method) -> Option<&DashMap<String, PyFunction>> {
        match route {
            Method::GET => Some(&self.get_routes),
            Method::POST => Some(&self.post_routes),
            Method::PUT => Some(&self.put_routes),
            Method::DELETE => Some(&self.delete_routes),
            Method::PATCH => Some(&self.patch_routes),
            _ => None,
        }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&DashMap<String, PyFunction>> {
        let method = match Method::from_bytes(route.as_bytes()) {
            Ok(res) => res,
            Err(_) => return None,
        };

        self.get_relevant_map(method)
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
        let table = self.get_relevant_map(route_method)?;
        Some(table.get(route)?.clone())
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
