use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder, Error, web::Bytes};
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict, PyList},
};
use futures::stream::Stream;
use std::pin::Pin;

use crate::io_helpers::{apply_hashmap_headers, read_file};
use super::headers::Headers;

#[derive(Debug, Clone)]
pub enum ResponseBody {
    Text(String),
    Binary(Vec<u8>),
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

#[derive(Debug, Clone)]
pub struct StreamingResponse {
    pub status_code: u16,
    pub headers: Headers,
    pub description: Py<PyAny>,
    pub response_type: String,
    pub file_path: Option<String>,
}

impl<'a> FromPyObject<'a> for Response {
    fn extract(ob: &'a PyAny) -> PyResult<Self> {
        // First check if this is a streaming response by checking response_type
        if let Ok(response_type) = ob.getattr("response_type")?.extract::<String>() {
            if response_type == "stream" {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Use StreamingResponse for streaming data"
                ));
            }
        }

        let status_code: u16 = ob.getattr("status_code")?.extract()?;
        let headers: Headers = ob.getattr("headers")?.extract()?;
        let description = ob.getattr("description")?;
        let file_path: Option<String> = ob.getattr("file_path")?.extract()?;

        // For non-streaming responses, convert to appropriate type
        if description.is_none() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description cannot be None"
            ));
        } else if description.is_instance_of::<pyo3::types::PyBytes>() {
            let body = ResponseBody::Binary(description.extract::<Vec<u8>>()?);
            Ok(Response {
                status_code,
                response_type: "binary".to_string(),
                headers,
                body,
                file_path,
            })
        } else if description.is_instance_of::<pyo3::types::PyString>() {
            let body = ResponseBody::Text(description.extract::<String>()?);
            Ok(Response {
                status_code,
                response_type: "text".to_string(),
                headers,
                body,
                file_path,
            })
        } else {
            // If description is not bytes or str, it might be a streaming response
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be bytes or str"
            ))
        }
    }
}

impl<'a> FromPyObject<'a> for StreamingResponse {
    fn extract(ob: &'a PyAny) -> PyResult<Self> {
        // First check if this is a streaming response by checking response_type
        if let Ok(response_type) = ob.getattr("response_type")?.extract::<String>() {
            if response_type != "stream" {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Not a streaming response (response_type = {})", response_type)
                ));
            }
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Missing response_type attribute"
            ));
        }

        let status_code: u16 = ob.getattr("status_code")?.extract()?;
        let headers: Headers = ob.getattr("headers")?.extract()?;
        let description = ob.getattr("description")?;
        let file_path: Option<String> = ob.getattr("file_path")?.extract()?;

        // Check if description is a generator or iterator
        if !description.hasattr("__iter__")? && !description.hasattr("__aiter__")? {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be an iterator or async iterator"
            ));
        }

        Ok(StreamingResponse {
            status_code,
            headers,
            description: description.into_py(ob.py()),
            response_type: "stream".to_string(),
            file_path,
        })
    }
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder =
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        
        // Set content type based on body type if not already set
        if !self.headers.headers.contains_key("content-type") {
            match &self.body {
                ResponseBody::Text(_) => {
                    response_builder.insert_header(("content-type", "text/plain; charset=utf-8"));
                }
                ResponseBody::Binary(_) => {
                    response_builder.insert_header(("content-type", "application/octet-stream"));
                }
                ResponseBody::Streaming(_) => {
                    panic!("Use StreamingResponse for streaming data");
                }
            };
        }
        
        // Apply headers after content-type
        apply_hashmap_headers(&mut response_builder, &self.headers);
        
        match self.body {
            ResponseBody::Text(text) => response_builder.body(text),
            ResponseBody::Binary(data) => response_builder.body(data),
            ResponseBody::Streaming(_) => {
                panic!("Use StreamingResponse for streaming data")
            }
        }
    }
}

impl Responder for StreamingResponse {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder =
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        
        // Apply headers
        apply_hashmap_headers(&mut response_builder, &self.headers);
        
        // Create streaming body
        let description = self.description;
        let stream = Box::pin(futures::stream::unfold(description, move |description| {
            Box::pin(async move {
                let result = Python::with_gil(|py| {
                    let desc = description.as_ref(py);
                    
                    // Handle sync iterator
                    if desc.hasattr("__iter__").unwrap_or(false) {
                        if let Ok(mut iter) = desc.iter() {
                            if let Some(Ok(item)) = iter.next() {
                                let chunk = if item.is_instance_of::<pyo3::types::PyBytes>() {
                                    item.extract::<Vec<u8>>().ok()
                                } else if item.is_instance_of::<pyo3::types::PyString>() {
                                    item.extract::<String>().ok().map(|s| s.into_bytes())
                                } else if item.is_instance_of::<pyo3::types::PyInt>() {
                                    item.extract::<i64>().ok().map(|i| i.to_string().into_bytes())
                                } else {
                                    None
                                };
                                
                                if let Some(chunk) = chunk {
                                    return Some((Ok(Bytes::from(chunk)), description));
                                }
                            }
                        }
                    }
                    // Handle async generator
                    else if desc.hasattr("__aiter__").unwrap_or(false) {
                        if let Ok(agen) = desc.call_method0("__aiter__") {
                            if let Ok(anext) = agen.call_method0("__anext__") {
                                // Convert Python awaitable to Rust Future
                                if let Ok(future) = pyo3_asyncio::tokio::into_future(anext) {
                                    // Create a new task to handle the async operation
                                    let handle = tokio::runtime::Handle::current();
                                    match handle.block_on(future) {
                                        Ok(item) => {
                                            let chunk = Python::with_gil(|py| {
                                                let item = item.as_ref(py);
                                                if item.is_none() {
                                                    return None;
                                                }
                                                
                                                if item.is_instance_of::<pyo3::types::PyBytes>() {
                                                    item.extract::<Vec<u8>>().ok()
                                                } else if item.is_instance_of::<pyo3::types::PyString>() {
                                                    item.extract::<String>().ok().map(|s| s.into_bytes())
                                                } else if item.is_instance_of::<pyo3::types::PyInt>() {
                                                    item.extract::<i64>().ok().map(|i| i.to_string().into_bytes())
                                                } else {
                                                    None
                                                }
                                            });

                                            if let Some(chunk) = chunk {
                                                return Some((Ok(Bytes::from(chunk)), description));
                                            }
                                        }
                                        Err(_) => return None
                                    }
                                }
                            }
                        }
                    }
                    None
                });
                result
            })
        })) as Pin<Box<dyn Stream<Item = Result<Bytes, Error>>>>;
        
        response_builder.streaming(stream)
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
            body: ResponseBody::Text("Not found".to_string()),
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
            body: ResponseBody::Text("Internal server error".to_string()),
            file_path: None,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        
        let description = match &self.body {
            ResponseBody::Text(text) => text.clone().into_py(py),
            ResponseBody::Binary(data) => PyBytes::new(py, data).into(),
            ResponseBody::Streaming(_) => {
                panic!("Use StreamingResponse for streaming data")
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

impl ToPyObject for StreamingResponse {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        
        let response = PyStreamingResponse {
            status_code: self.status_code,
            headers,
            description: self.description.clone_ref(py),
            response_type: self.response_type.clone(),
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

#[pyclass(name = "StreamingResponse")]
#[derive(Debug, Clone)]
pub struct PyStreamingResponse {
    #[pyo3(get)]
    pub status_code: u16,
    #[pyo3(get)]
    pub headers: Py<Headers>,
    #[pyo3(get)]
    pub description: Py<PyAny>,
    #[pyo3(get)]
    pub response_type: String,
    #[pyo3(get)]
    pub file_path: Option<String>,
}

#[pymethods]
impl PyStreamingResponse {
    #[new]
    #[pyo3(signature = (status_code=200, description=None, headers=None))]
    pub fn new(py: Python, status_code: u16, description: Option<Py<PyAny>>, headers: Option<&PyAny>) -> PyResult<Self> {
        let headers_output: Py<Headers> = if let Some(headers) = headers {
            if let Ok(headers_dict) = headers.downcast::<PyDict>() {
                let headers = Headers::new(Some(headers_dict));
                Py::new(py, headers)?
            } else if let Ok(headers) = headers.extract::<Py<Headers>>() {
                headers
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                    "headers must be a Headers instance or a dict",
                ));
            }
        } else {
            let headers = Headers::new(None);
            Py::new(py, headers)?
        };

        let description = match description {
            Some(d) => d,
            None => PyList::empty(py).into(),
        };

        Ok(Self {
            status_code,
            headers: headers_output,
            description,
            response_type: "stream".to_string(),
            file_path: None,
        })
    }
}

#[pymethods]
impl PyResponse {
    #[new]
    pub fn new(
        py: Python,
        status_code: u16,
        headers: &PyAny,
        description: Py<PyAny>,
    ) -> PyResult<Self> {
        // Validate description type first
        let desc = description.as_ref(py);
        if desc.is_none() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description cannot be None"
            ));
        }
        
        // Only allow string or bytes
        if !desc.is_instance_of::<pyo3::types::PyBytes>()
            && !desc.is_instance_of::<pyo3::types::PyString>()
        {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be bytes or str"
            ));
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

        // Default to text response type
        let response_type = if desc.is_instance_of::<pyo3::types::PyBytes>() {
            "binary".to_string()
        } else {
            "text".to_string()
        };

        Ok(Self {
            status_code,
            response_type,
            headers: headers_output,
            description,
            file_path: None,
        })
    }

    #[setter]
    pub fn set_description(&mut self, py: Python, description: Py<PyAny>) -> PyResult<()> {
        // Validate description type
        let desc = description.as_ref(py);
        if desc.is_none() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description cannot be None"
            ));
        }
        
        // Only allow string or bytes
        if !desc.is_instance_of::<pyo3::types::PyBytes>()
            && !desc.is_instance_of::<pyo3::types::PyString>()
        {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be bytes or str"
            ));
        }

        // Update response type based on new description
        self.response_type = if desc.is_instance_of::<pyo3::types::PyBytes>() {
            "binary".to_string()
        } else {
            "text".to_string()
        };

        self.description = description;
        Ok(())
    }

    #[setter]
    pub fn set_file_path(&mut self, py: Python, file_path: &str) -> PyResult<()> {
        self.file_path = Some(file_path.to_string());
        self.response_type = "binary".to_string();

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
