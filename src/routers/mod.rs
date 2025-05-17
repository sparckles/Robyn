use anyhow::Result;
use pyo3::Bound;

use crate::types::function_info::FunctionInfo;

pub mod const_router;
pub mod http_router;
pub mod middleware_router;
pub mod web_socket_router;

pub trait Router<T, U> {
    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    fn add_route(
        &self,
        route_type: &U,
        route: &str,
        function: FunctionInfo,
        event_loop: Option<Bound<'_, pyo3::PyAny>>,
    ) -> Result<()>;

    /// Retrieve the correct function from the previously inserted routes
    fn get_route(&self, route_type: &U, route: &str) -> Option<T>;
}
