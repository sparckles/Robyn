use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder, Error, web::Bytes};
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict, PyList},
};
use futures::stream::Stream;
use futures_util::StreamExt;
use std::pin::Pin;

use crate::io_helpers::{apply_hashmap_headers, read_file};
use crate::types::{check_body_type, check_description_type, get_description_from_pyobject};

use super::headers::Headers;

#[derive(Debug, Clone)]
pub enum ResponseBody {
    Static(Vec<u8>),
    Streaming(Vec<Vec<u8>>),
}

#[derive(Debug, Clone)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Headers,
    pub body: ResponseBody,
    pub file_path: Option<String>,
}

impl<'a> FromPyObject<'a> for Response {
    fn extract(ob: &'a PyAny) -> PyResult<Self> {
        let status_code = ob.getattr("status_code")?.extract()?;
        let response_type = ob.getattr("response_type")?.extract()?;
        let headers = ob.getattr("headers")?.extract()?;
        let description = ob.getattr("description")?;
        let file_path = ob.getattr("file_path")?.extract()?;

        let body = if let Ok(iter) = description.iter() {
            let mut chunks = Vec::new();
            for item in iter {
                let item = item?;
                let chunk = if item.is_instance_of::<pyo3::types::PyBytes>() {
                    item.extract::<Vec<u8>>()?
                } else if item.is_instance_of::<pyo3::types::PyString>() {
                    item.extract::<String>()?.into_bytes()
                } else if item.is_instance_of::<pyo3::types::PyInt>() {
                    item.extract::<i64>()?.to_string().into_bytes()
                } else {
                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                        "Stream items must be bytes, str, or int"
                    ));
                };
                chunks.push(chunk);
            }
            ResponseBody::Streaming(chunks)
        } else {
            ResponseBody::Static(get_description_from_pyobject(description)?)
        };

        Ok(Response {
            status_code,
            response_type,
            headers,
            body,
            file_path,
        })
    }
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder =
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        apply_hashmap_headers(&mut response_builder, &self.headers);
        
        match self.body {
            ResponseBody::Static(data) => response_builder.body(data),
            ResponseBody::Streaming(chunks) => {
                let stream = Box::pin(
                    futures::stream::iter(chunks.into_iter())
                        .map(|chunk| Ok::<Bytes, Error>(Bytes::from(chunk)))
                ) as Pin<Box<dyn Stream<Item = Result<Bytes, Error>>>>;
                response_builder.streaming(stream)
            }
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
            body: ResponseBody::Static("Not found".to_owned().into_bytes()),
            file_path: None,
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
            body: ResponseBody::Static("Internal server error".to_owned().into_bytes()),
            file_path: None,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        
        let description = match &self.body {
            ResponseBody::Static(data) => {
                match String::from_utf8(data.to_vec()) {
                    Ok(description) => description.to_object(py),
                    Err(_) => PyBytes::new(py, data).into(),
                }
            },
            ResponseBody::Streaming(chunks) => {
                let list = PyList::empty(py);
                for chunk in chunks {
                    list.append(PyBytes::new(py, chunk)).unwrap();
                }
                list.to_object(py)
            }
        };

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
        headers: &PyAny,
        description: Py<PyAny>,
    ) -> PyResult<Self> {
        // Check if description is an iterator/generator
        let is_stream = Python::with_gil(|py| {
            description.as_ref(py).iter().is_ok()
        });

        if is_stream {
            // For streaming responses, we don't need to check body type
            // as we'll validate each chunk when it's yielded
        } else {
            check_body_type(py, &description)?;
        }

        let headers_output: Py<Headers> = if let Ok(headers_dict) = headers.downcast::<PyDict>() {
            let headers = Headers::new(Some(headers_dict));
            Py::new(py, headers)?
        } else if let Ok(headers) = headers.extract::<Py<Headers>>() {
            headers
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "headers must be a Headers instance or a dict",
            ));
        };

        Ok(Self {
            status_code,
            response_type: if is_stream { "stream".to_string() } else { "text".to_string() },
            headers: headers_output,
            description,
            file_path: None,
        })
    }

    #[setter]
    pub fn set_description(&mut self, py: Python, description: Py<PyAny>) -> PyResult<()> {
        // Check if description is an iterator/generator
        let is_stream = description.as_ref(py).iter().is_ok();

        if is_stream {
            self.response_type = "stream".to_string();
        } else {
            check_description_type(py, &description)?;
            self.response_type = "text".to_string();
        }
        
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
