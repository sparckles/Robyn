use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use actix_web::http::Method;
use matchit::Node;

use anyhow::{bail, Error, Result};

/// Contains the thread safe hashmaps of different routes

pub struct ConstRouter {
    get_routes: RwLock<Node<String>>,
    post_routes: RwLock<Node<String>>,
    put_routes: RwLock<Node<String>>,
    delete_routes: RwLock<Node<String>>,
    patch_routes: RwLock<Node<String>>,
    head_routes: RwLock<Node<String>>,
    options_routes: RwLock<Node<String>>,
    connect_routes: RwLock<Node<String>>,
    trace_routes: RwLock<Node<String>>,
}

impl ConstRouter {
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
    fn get_relevant_map(&self, route: Method) -> Option<&RwLock<Node<String>>> {
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
    fn get_relevant_map_str(&self, route: &str) -> Option<&RwLock<Node<String>>> {
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

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_route(
        &self,
        route_type: &str, // we can just have route type as WS
        route: &str,
        response: &str,
    ) -> Result<(), Error> {
        // TODO:
        // allow handlers
        // allow routes
        // and all others
        // spawn a blockking thread for insertion
        let table = match self.get_relevant_map_str(route_type) {
            Some(table) => table,
            None => bail!("No relevant map"),
        };

        // try removing unwrap here
        table
            .write()
            .unwrap()
            .insert(route.to_string(), response.to_string())?;

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

        match table.read().unwrap().at(route) {
            Ok(res) => Some(res.value.clone()),
            Err(_) => None,
        }
    }
}
