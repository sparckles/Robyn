use std::collections::HashMap;

use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder};
use pyo3::{
    exceptions::{PyIOError, PyValueError},
    prelude::*,
    types::{PyBytes, PyDict, PyString},
};

use crate::io_helpers::{apply_hashmap_headers, read_file};
use crate::types::{check_description_type, get_description_from_pyobject};

#[derive(Debug, Clone, FromPyObject)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: HashMap<String, String>,
    // https://pyo3.rs/v0.19.2/function.html?highlight=from_py_#per-argument-options
    #[pyo3(from_py_with = "get_description_from_pyobject")]
    pub description: Vec<u8>,
    pub file_path: Option<String>,
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder =
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        apply_hashmap_headers(&mut response_builder, &self.headers);
        response_builder.body(self.description)
    }
}

impl Response {
    pub fn not_found(headers: &HashMap<String, String>) -> Self {
        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers: headers.clone(),
            description: "Not found".to_owned().into_bytes(),
            file_path: None,
        }
    }

    pub fn internal_server_error(headers: &HashMap<String, String>) -> Self {
        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers: headers.clone(),
            description: "Internal server error".to_owned().into_bytes(),
            file_path: None,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        let description = String::from_utf8(self.description.to_vec())
            .unwrap()
            .to_object(py);
        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type.clone(),
            headers,
            description,
            file_path: self.file_path.clone(),
        };
        Py::new(py, response).unwrap().as_ref(py).into()
    }
}

#[pyclass(name = "Response")]
#[derive(Debug, Clone)]
pub struct PyResponse {
    #[pyo3(get)]
    pub status_code: u16,
    #[pyo3(get)]
    pub response_type: String,
    #[pyo3(get, set)]
    pub headers: Py<PyDict>,
    #[pyo3(get)]
    pub description: Py<PyAny>,
    #[pyo3(get)]
    pub file_path: Option<String>,
}

#[pymethods]
impl PyResponse {
    // To do: Add check for content-type in header and change response_type accordingly
    #[new]
    pub fn new(
        py: Python,
        status_code: u16,
        headers: Py<PyDict>,
        description: Py<PyAny>,
    ) -> PyResult<Self> {
        if description.downcast::<PyString>(py).is_err()
            && description.downcast::<PyBytes>(py).is_err()
        {
            return Err(PyValueError::new_err(
                "Could not convert specified body to bytes",
            ));
        };
        Ok(Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers,
            description,
            file_path: None,
        })
    }

    #[setter]
    pub fn set_description(&mut self, py: Python, description: Py<PyAny>) -> PyResult<()> {
        check_description_type(py, description.clone())?;
        self.description = description;
        Ok(())
    }

    #[setter]
    pub fn set_file_path(&mut self, py: Python, file_path: &str) -> PyResult<()> {
        // we should be handling based on headers but works for now
        self.response_type = "static_file".to_string();
        self.file_path = Some(file_path.to_string());
        self.description = read_file(file_path)
            .map_err(|e| PyErr::new::<PyIOError, _>(e.to_string()))?
            .into_py(py);
        Ok(())
    }
}
