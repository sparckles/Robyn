use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder};
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict},
    IntoPyObject,
};

use crate::io_helpers::{apply_hashmap_headers, read_file};
use crate::types::{check_body_type, check_description_type, get_description_from_pyobject};

use super::headers::Headers;

#[derive(Debug, Clone, FromPyObject)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Headers,
    // https://pyo3.rs/v0.25.0/function.html#per-argument-options
    #[pyo3(from_py_with = get_description_from_pyobject)]
    pub description: Vec<u8>,
    pub file_path: Option<String>,
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder = HttpResponseBuilder::new(
            StatusCode::from_u16(self.status_code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        );
        apply_hashmap_headers(&mut response_builder, &self.headers);
        response_builder.body(self.description)
    }
}

impl Response {
    pub fn not_found(headers: Option<&Headers>) -> Self {
        const NOT_FOUND_BYTES: &[u8] = b"Not found";

        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers: headers.cloned().unwrap_or_else(|| Headers::new(None)),
            description: NOT_FOUND_BYTES.to_vec(),
            file_path: None,
        }
    }

    pub fn internal_server_error(headers: Option<&Headers>) -> Self {
        const SERVER_ERROR_BYTES: &[u8] = b"Internal server error";

        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers: headers.cloned().unwrap_or_else(|| Headers::new(None)),
            description: SERVER_ERROR_BYTES.to_vec(),
            file_path: None,
        }
    }
}

impl<'py> IntoPyObject<'py> for Response {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;
    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let headers = self.headers.into_pyobject(py)?.extract()?;

        let description = if self.description.is_empty() {
            "".into_pyobject(py)?.into_any()
        } else {
            match String::from_utf8(self.description.clone()) {
                Ok(description) => description.into_pyobject(py)?.into_any(),
                Err(_) => PyBytes::new(py, &self.description).into_any(),
            }
        };

        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type,
            headers,
            description: description.into(),
            file_path: self.file_path,
        };
        Ok(Py::new(py, response)?.into_bound(py).into_any())
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
    pub headers: Py<Headers>,
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
        headers: Bound<'_, PyAny>,
        description: Py<PyAny>,
    ) -> PyResult<Self> {
        check_body_type(py, &description)?;

        let headers_output: Py<Headers> = if let Ok(headers_dict) = headers.downcast::<PyDict>() {
            // Here you'd have logic to create a Headers instance from a PyDict
            // For simplicity, let's assume you have a method `from_dict` on Headers for this
            let headers = Headers::new(Some(headers_dict)); // Hypothetical method
            Py::new(py, headers)?
        } else if let Ok(headers) = headers.extract::<Py<Headers>>() {
            // If it's already a Py<Headers>, use it directly
            headers
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "headers must be a Headers instance or a dict",
            ));
        };

        Ok(Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers: headers_output,
            description,
            file_path: None,
        })
    }

    #[setter]
    pub fn set_description(&mut self, py: Python, description: Py<PyAny>) -> PyResult<()> {
        check_description_type(py, &description)?;
        self.description = description;
        Ok(())
    }

    #[setter]
    pub fn set_file_path(&mut self, py: Python, file_path: &str) -> PyResult<()> {
        self.response_type = "static_file".to_string();
        self.file_path = Some(file_path.to_string());

        match read_file(file_path) {
            Ok(content) => {
                self.description = PyBytes::new(py, &content).into();
                Ok(())
            }
            Err(e) => Err(PyIOError::new_err(format!("Failed to read file: {}", e))),
        }
    }

    pub fn set_cookie(&mut self, py: Python, key: &str, value: &str) -> PyResult<()> {
        self.headers
            .try_borrow_mut(py)
            .expect("value already borrowed")
            .append(key.to_string(), value.to_string());
        Ok(())
    }
}
