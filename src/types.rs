use anyhow::Result;
use dashmap::DashMap;
use pyo3::{exceptions::PyValueError, prelude::*};
use pythonize::depythonize;
use serde_json::Value;

#[derive(Debug, Clone)]
pub enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
}

pub const TEXT: u16 = 1;
pub const STATIC_FILE: u16 = 1;

fn conv_py_to_json_string(v: Py<PyAny>) -> Result<String> {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let new_sample: Value = depythonize(v.as_ref(py)).unwrap();
    Ok(serde_json::to_string(&new_sample)?)
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Response {
    pub response_type: u16,
    pub meta: String,
}

#[pymethods]
impl Response {
    #[new]
    pub fn new(response_type: u16, meta: String) -> Self {
        Response {
            response_type,
            meta,
        }
    }

    #[staticmethod]
    pub fn newjson(response_type: u16, _padding: u8, meta: Py<PyAny>) -> PyResult<Self> {
        let meta = match conv_py_to_json_string(meta) {
            Ok(res) => res,
            Err(e) => return Err(PyValueError::new_err("Cannot parse json")),
        };

        Ok(Response {
            response_type,
            meta,
        })
    }
}

pub type Headers = DashMap<String, String>;
