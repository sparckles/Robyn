use anyhow::Result;
use pyo3::{Py, PyAny};

pub mod const_router;
pub mod middleware_router;
pub mod router;
pub mod types;
pub mod web_socket_router;

pub struct RouteType<T>(pub T);

pub trait Router<T, U> {
    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    fn add_route(
        &self,
        route_type: &str,
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        event_loop: Option<&PyAny>,
    ) -> Result<()>;

    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    fn get_route(&self, route_method: RouteType<U>, route: &str) -> Option<T>;
}
