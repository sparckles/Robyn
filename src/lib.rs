mod executors;
mod io_helpers;
mod routers;
mod server;
mod shared_socket;
mod types;
mod web_socket_connection;

use server::Server;
use shared_socket::SocketHeld;

// pyO3 module
use pyo3::prelude::*;
use types::{
    function_info::{FunctionInfo, MiddlewareType},
    request::PyRequest,
    response::PyResponse,
    HttpMethod,
};

#[pyfunction]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").into()
}

#[pymodule]
pub fn robyn(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class/function to make the rustPyFunctions available
    m.add_function(wrap_pyfunction!(get_version, m)?)?;
    m.add_class::<Server>()?;
    m.add_class::<SocketHeld>()?;
    m.add_class::<FunctionInfo>()?;
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    m.add_class::<MiddlewareType>()?;
    m.add_class::<HttpMethod>()?;
    pyo3::prepare_freethreaded_python();
    Ok(())
}
