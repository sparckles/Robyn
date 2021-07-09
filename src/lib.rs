mod processor;
mod router;
mod server;
mod types;

use server::Server;

use tokio::fs;

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyString;
use pyo3::wrap_pyfunction;

#[pyfunction]
pub fn start_server() {
    // this is a wrapper function for python
    // to start a server
    Server::new();
}

#[pyfunction]
pub fn async_static_files(py: Python, file_name: String) -> PyResult<PyObject> {
    pyo3_asyncio::tokio::into_coroutine(py, async move {
        let contents = fs::read(file_name.clone()).await.unwrap();
        let foo = String::from_utf8_lossy(&contents);
        Ok(Python::with_gil(|py| {
            let x = PyString::new(py, &foo);
            let any: &PyAny = x.as_ref();
            let any = any.to_object(py);
            any.clone()
        }))
    })
}

#[pymodule]
pub fn robyn(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class to make the rustPyFunctions available
    // in python
    m.add_wrapped(wrap_pyfunction!(start_server))?;
    m.add_wrapped(wrap_pyfunction!(async_static_files))?;
    m.add_class::<Server>()?;
    pyo3_asyncio::try_init(py)?;
    pyo3::prepare_freethreaded_python();
    Ok(())
}
