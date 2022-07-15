use std::sync::Arc;
use std::sync::RwLock;
// pyo3 modules
use crate::executors::execute_function;
use log::debug;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Node;

use anyhow::{bail, Error, Result};

/// Contains the thread safe hashmaps of different routes

pub struct ConstRouter {
    get_routes: Arc<RwLock<Node<String>>>,
    post_routes: Arc<RwLock<Node<String>>>,
    put_routes: Arc<RwLock<Node<String>>>,
    delete_routes: Arc<RwLock<Node<String>>>,
    patch_routes: Arc<RwLock<Node<String>>>,
    head_routes: Arc<RwLock<Node<String>>>,
    options_routes: Arc<RwLock<Node<String>>>,
    connect_routes: Arc<RwLock<Node<String>>>,
    trace_routes: Arc<RwLock<Node<String>>>,
}

impl ConstRouter {
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
    fn get_relevant_map(&self, route: Method) -> Option<Arc<RwLock<Node<String>>>> {
        match route {
            Method::GET => Some(self.get_routes.clone()),
            Method::POST => Some(self.post_routes.clone()),
            Method::PUT => Some(self.put_routes.clone()),
            Method::PATCH => Some(self.patch_routes.clone()),
            Method::DELETE => Some(self.delete_routes.clone()),
            Method::HEAD => Some(self.head_routes.clone()),
            Method::OPTIONS => Some(self.options_routes.clone()),
            Method::CONNECT => Some(self.connect_routes.clone()),
            Method::TRACE => Some(self.trace_routes.clone()),
            _ => None,
        }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<Arc<RwLock<Node<String>>>> {
        if route != "WS" {
            let method = match Method::from_bytes(route.as_bytes()) {
                Ok(res) => res,
                Err(_) => return None,
            };

            self.get_relevant_map(method)
        } else {
            None
        }
    }

    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    /// Doesn't allow query params/body/etc as variables cannot be "memoized"/"const"ified
    pub fn add_route(
        &self,
        route_type: &str, // we can just have route type as WS
        route: &str,
        function: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        event_loop: &PyAny,
    ) -> Result<(), Error> {
        let table = match self.get_relevant_map_str(route_type) {
            Some(table) => table,
            None => bail!("No relevant map"),
        };
        let route = route.to_string();
        pyo3_asyncio::tokio::run_until_complete(event_loop, async move {
            let output = execute_function(function, number_of_params, is_async)
                .await
                .unwrap();
            debug!("This is the result of the output {:?}", output);
            table
                .clone()
                .write()
                .unwrap()
                .insert(route, output.get("body").unwrap().to_string())
                .unwrap();

            Ok(())
        })
        .unwrap();

        Ok(())
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn get_route(
        &self,
        route_method: Method,
        route: &str, // check for the route method here
    ) -> Option<String> {
        // need to split this function in multiple smaller functions
        let table = self.get_relevant_map(route_method)?;
        let route_map = table.read().ok()?;

        match route_map.at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        }
    }
}
