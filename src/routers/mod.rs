use std::collections::HashMap;

use anyhow::Result;
use percent_encoding::percent_decode_str;
use pyo3::{Bound, Python};

use crate::types::function_info::FunctionInfo;

pub mod const_router;
pub mod http_router;
pub mod middleware_router;
pub mod web_socket_router;

pub trait Router<T, U> {
    /// Checks if the functions is an async function
    /// Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    fn add_route<'py>(
        &self,
        py: Python,
        route_type: &U,
        route: &str,
        function: FunctionInfo,
        event_loop: Option<Bound<'py, pyo3::PyAny>>,
    ) -> Result<()>;

    /// Retrieve the correct function from the previously inserted routes
    fn get_route(&self, route_type: &U, route: &str) -> Option<T>;
}

/// Decode the captures of a matched route.
///
/// Matching runs on the raw path, so an encoded slash never changes which
/// segment a capture covers. Handlers and route middleware then receive the
/// decoded value; invalid UTF-8 becomes U+FFFD.
pub(crate) fn decode_route_params(params: &matchit::Params<'_, '_>) -> HashMap<String, String> {
    params
        .iter()
        .map(|(key, value)| {
            (
                key.to_string(),
                percent_decode_str(value).decode_utf8_lossy().into_owned(),
            )
        })
        .collect()
}
