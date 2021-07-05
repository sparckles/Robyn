mod processor;
mod router;
mod server;
mod types;

use server::Server;

// pyO3 module
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyfunction]
pub fn start_server(file_directory: &str) {
    // this is a wrapper function for python
    // to start a server
    Server::new(file_directory);
}

#[pymodule]
pub fn robyn(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class to make the rustPyFunctions available
    // in python
    m.add_wrapped(wrap_pyfunction!(start_server))?;
    m.add_class::<Server>()?;
    pyo3_asyncio::try_init(py)?;
    pyo3::prepare_freethreaded_python();
    Ok(())
}
