use dashmap::DashMap;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

// Contains the thread safe hashmaps of different routes
//
use hyper::Method;

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
            Err(_) => return None
        };

        self.get_relevant_map(method)
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>) {
        let table = match self.get_relevant_map_str(route_type) {
            Some(table) => table,
            None => return,
        };
        Python::with_gil(|py| {
            let process_object_wrapper: &PyAny = handler.as_ref(py);
            let py_dict = process_object_wrapper.downcast::<PyDict>().unwrap();
            let is_async: bool = py_dict.get_item("is_async").unwrap().extract().unwrap();
            let handler: &PyAny = py_dict.get_item("handler").unwrap();
            let route_function = if is_async {
                PyFunction::CoRoutine(handler.into())
            } else {
                PyFunction::SyncFunction(handler.into())
            };
            table.insert(route.to_string(), route_function);
        });
    }

    pub fn get_route(&self, route_method: Method, route: &str) -> Option<PyFunction> {
        println!("{}{}", route_method.as_str(), route);
        let table = self.get_relevant_map(route_method)?;
        Some(table.get(route)?.clone())
    }
}
