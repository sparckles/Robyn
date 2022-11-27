use anyhow::Result;
use pyo3::PyAny;

use crate::types::FunctionInfo;

pub mod const_router;
pub mod http_router;
pub mod middleware_router;
pub mod types;
pub mod web_socket_router;

pub trait Router<T, U> {
    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    fn add_route(
        &self,
        route_type: &str,
        route: &str,
        function: FunctionInfo,
        event_loop: Option<&PyAny>,
    ) -> Result<()>;

    /// Retrieve the correct function from the previously inserted routes
    fn get_route(&self, route_method: &U, route: &str) -> Option<T>;
}
