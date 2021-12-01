mod processor;
mod router;
mod server;
mod shared_socket;
mod types;
mod web_socket_connection;

use server::Server;
use shared_socket::SocketHeld;

// pyO3 module
use pyo3::prelude::*;

#[pymodule]
pub fn robyn(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class to make the rustPyFunctions available
    m.add_class::<Server>()?;
    m.add_class::<SocketHeld>()?;
    pyo3::prepare_freethreaded_python();
    Ok(())
}
