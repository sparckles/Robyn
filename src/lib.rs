mod processor;
mod router;
mod server;
mod types;

use server::Server;

// pyO3 module
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pymodule]
pub fn robyn(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class to make the rustPyFunctions available
    m.add_class::<Server>()?;
    pyo3::prepare_freethreaded_python();
    Ok(())
}
