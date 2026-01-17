mod asyncio;
mod blocking;
mod callbacks;
mod conversion;
mod executors;
mod io_helpers;
mod runtime;
mod routers;
mod server;
mod shared_socket;
mod types;
mod websockets;

use server::Server;
use shared_socket::SocketHeld;

// pyO3 module
use pyo3::prelude::*;
use types::{
    function_info::{FunctionInfo, MiddlewareType},
    headers::Headers,
    identity::Identity,
    multimap::QueryParams,
    request::PyRequest,
    response::{PyResponse, PyStreamingResponse},
    HttpMethod, Url,
};

use websockets::{registry::WebSocketRegistry, WebSocketConnector};

#[pyfunction]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").into()
}

#[pymodule]
pub fn robyn(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // the pymodule class/function to make the rustPyFunctions available
    m.add_function(wrap_pyfunction!(get_version, m)?)?;

    m.add_class::<Server>()?;
    m.add_class::<Headers>()?;
    m.add_class::<WebSocketRegistry>()?;
    m.add_class::<WebSocketConnector>()?;
    m.add_class::<SocketHeld>()?;
    m.add_class::<FunctionInfo>()?;
    m.add_class::<Identity>()?;
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    m.add_class::<PyStreamingResponse>()?;
    m.add_class::<Url>()?;
    m.add_class::<QueryParams>()?;
    m.add_class::<MiddlewareType>()?;
    m.add_class::<HttpMethod>()?;

    // Register awaitable types
    m.add_class::<callbacks::PyEmptyAwaitable>()?;
    m.add_class::<callbacks::PyDoneAwaitable>()?;
    m.add_class::<callbacks::PyErrAwaitable>()?;
    m.add_class::<callbacks::PyIterAwaitable>()?;
    m.add_class::<callbacks::PyFutureAwaitable>()?;

    // Note: prepare_freethreaded_python is deprecated, but Python::initialize() 
    // is not available in pymodule context. This is safe to ignore for now.
    #[allow(deprecated)]
    pyo3::prepare_freethreaded_python();
    Ok(())
}
