use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder};
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict},
};
use futures::Stream;
use std::pin::Pin;
use actix_web::web::Bytes;

use crate::io_helpers::{apply_hashmap_headers, read_file};
use crate::types::{check_body_type, check_description_type, get_description_from_pyobject};

use super::headers::Headers;

#[derive(Debug, Clone, FromPyObject)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Headers,
    #[pyo3(from_py_with = "get_description_from_pyobject")]
    pub description: Vec<u8>,
    pub file_path: Option<String>,
    pub is_streaming: bool,
    pub stream: Option<Pin<Box<dyn Stream<Item = Result<Bytes, actix_web::Error>>>>>,
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder = 
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        apply_hashmap_headers(&mut response_builder, &self.headers);
        
        if self.is_streaming {
            if let Some(stream) = self.stream {
                response_builder.streaming(stream)
            } else {
                response_builder.body(vec![])
            }
        } else {
            response_builder.body(self.description)
        }
    }
}

impl Response {
    pub fn not_found(headers: Option<&Headers>) -> Self {
        let headers = match headers {
            Some(headers) => headers.clone(),
            None => Headers::new(None),
        };

        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers,
            description: "Not found".to_owned().into_bytes(),
            file_path: None,
            is_streaming: false,
            stream: None,
        }
    }

    pub fn internal_server_error(headers: Option<&Headers>) -> Self {
        let headers = match headers {
            Some(headers) => headers.clone(),
            None => Headers::new(None),
        };

        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers,
            description: "Internal server error".to_owned().into_bytes(),
            file_path: None,
            is_streaming: false,
            stream: None,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        // The description should only be either string or binary.
        // it should raise an exception otherwise
        let description = match String::from_utf8(self.description.to_vec()) {
            Ok(description) => description.to_object(py),
            Err(_) => PyBytes::new(py, &self.description.to_vec()).into(),
        };

        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type.clone(),
            headers,
            description,
            file_path: self.file_path.clone(),
            is_streaming: self.is_streaming,
            stream: self.stream.clone(),
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
    pub headers: Py<Headers>,
    #[pyo3(get)]
    pub description: Py<PyAny>,
    #[pyo3(get)]
    pub file_path: Option<String>,
    #[pyo3(get)]
    pub is_streaming: bool,
    #[pyo3(get)]
    pub stream: Option<Pin<Box<dyn Stream<Item = Result<Bytes, actix_web::Error>>>>>,
}

#[pymethods]
impl PyResponse {
    // To do: Add check for content-type in header and change response_type accordingly
    #[new]
    pub fn new(
        py: Python,
        status_code: u16,
        headers: &PyAny,
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
            is_streaming: false,
            stream: None,
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
