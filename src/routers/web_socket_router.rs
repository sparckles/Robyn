use std::collections::HashMap;
use std::sync::RwLock;
// pyo3 modules
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyAny;

/// Contains the thread safe hashmaps of different routes

pub struct WebSocketRouter {
    web_socket_routes: RwLock<HashMap<String, HashMap<String, (PyFunction, u8)>>>,
}

impl WebSocketRouter {
    pub fn new() -> Self {
        Self {
            web_socket_routes: RwLock::new(HashMap::new()),
        }
    }

    #[inline]
    pub fn get_web_socket_map(
        &self,
    ) -> &RwLock<HashMap<String, HashMap<String, (PyFunction, u8)>>> {
        &self.web_socket_routes
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
}
