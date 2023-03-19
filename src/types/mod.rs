use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    types::{PyBytes, PyString},
};

pub mod function_info;
pub mod request;
pub mod response;

#[pyclass]
#[derive(Default, Clone)]
pub struct Url {
    #[pyo3(get)]
    pub scheme: String,
    #[pyo3(get)]
    pub host: String,
    #[pyo3(get)]
    pub path: String,
}

impl Url {
    fn new(scheme: &str, host: &str, path: &str) -> Self {
        Self {
            scheme: scheme.to_string(),
            host: host.to_string(),
            path: path.to_string(),
        }
    }
}

pub fn get_body_from_pyobject(body: &PyAny) -> PyResult<Vec<u8>> {
    if let Ok(s) = body.downcast::<PyString>() {
        Ok(s.to_string().into_bytes())
    } else if let Ok(b) = body.downcast::<PyBytes>() {
        Ok(b.as_bytes().to_vec())
    } else {
        Err(PyValueError::new_err(
            "Could not convert specified body to bytes",
        ))
    }
}

pub fn check_body_type(py: Python, body: Py<PyAny>) -> PyResult<()> {
    if body.downcast::<PyString>(py).is_err() && body.downcast::<PyBytes>(py).is_err() {
        return Err(PyValueError::new_err(
            "Could not convert specified body to bytes",
        ));
    };
    Ok(())
}
