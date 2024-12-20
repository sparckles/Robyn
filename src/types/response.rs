use actix_http::{body::BoxBody, StatusCode};
use actix_web::{HttpRequest, HttpResponse, HttpResponseBuilder, Responder, Error, web::Bytes};
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict},
};
use futures::stream::Stream;
use std::pin::Pin;
use serde_json;

use crate::io_helpers::{apply_hashmap_headers, read_file};
use super::headers::Headers;

#[derive(Debug, Clone)]
pub enum ResponseBody {
    Text(String),
    Binary(Vec<u8>),
    Streaming(Py<PyAny>),
}

#[derive(Debug, Clone)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Headers,
    pub body: ResponseBody,
    pub file_path: Option<String>,
    pub streaming: bool,
}

impl FromPyObject<'_> for Response {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let status_code: u16 = ob.getattr("status_code")?.extract()?;
        let mut headers: Headers = ob.getattr("headers")?.extract()?;
        let description = ob.getattr("description")?;
        let file_path: Option<String> = ob.getattr("file_path")?.extract()?;
        let streaming: bool = ob.getattr("streaming")?.extract().unwrap_or(false);

        // For error responses or middleware responses, handle them specially
        if status_code >= 400 || status_code == 401 {
            let body = if description.is_instance_of::<pyo3::types::PyBytes>() {
                ResponseBody::Binary(description.extract::<Vec<u8>>()?)
            } else if description.is_instance_of::<pyo3::types::PyString>() {
                ResponseBody::Text(description.extract::<String>()?)
            } else {
                ResponseBody::Text(description.str()?.extract::<String>()?)
            };

            return Ok(Response {
                status_code,
                response_type: "text".to_string(),
                headers,
                body,
                file_path,
                streaming: false,
            });
        }

        // For streaming responses, handle iterator/generator
        if streaming || description.hasattr("__iter__")? || description.hasattr("__aiter__")? {
            // For SSE responses, ensure proper headers
            if headers.headers.get("content-type").map_or(false, |v| v.contains(&"text/event-stream".to_string())) {
                headers.headers.entry("cache-control".to_string()).or_default().push("no-cache".to_string());
                headers.headers.entry("connection".to_string()).or_default().push("keep-alive".to_string());
            }
            
            Ok(Response {
                status_code,
                response_type: "stream".to_string(),
                headers,
                body: ResponseBody::Streaming(description.into_py(ob.py())),
                file_path,
                streaming: true,  // Always set streaming to true for iterators
            })
        } else if description.is_none() {
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
                streaming: false,
            })
        } else if description.is_instance_of::<pyo3::types::PyString>() {
            let body = ResponseBody::Text(description.extract::<String>()?);
            Ok(Response {
                status_code,
                response_type: "text".to_string(),
                headers,
                body,
                file_path,
                streaming: false,
            })
        } else {
            // Try to convert to string if possible
            if let Ok(text) = description.str() {
                let body = ResponseBody::Text(text.extract::<String>()?);
                Ok(Response {
                    status_code,
                    response_type: "text".to_string(),
                    headers,
                    body,
                    file_path,
                    streaming: false,
                })
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Description must be bytes, str, or an iterator"
                ));
            }
        }
    }
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder = HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        
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
                    response_builder.insert_header(("content-type", "text/plain; charset=utf-8"));
                }
            };
        }
        
        // Apply headers after content-type
        apply_hashmap_headers(&mut response_builder, &self.headers);
        
        // For error responses or middleware responses, return immediately
        if self.status_code >= 400 || self.status_code == 401 {
            match &self.body {
                ResponseBody::Text(text) => return response_builder.body(text.clone()),
                ResponseBody::Binary(data) => return response_builder.body(data.clone()),
                ResponseBody::Streaming(_) => return response_builder.body("Internal Server Error"),
            }
        }
        
        if self.streaming {
            match self.body {
                ResponseBody::Streaming(description) => {
                    // Add SSE headers if content type is text/event-stream
                    if self.headers.headers.get("content-type").map_or(false, |v| v.contains(&"text/event-stream".to_string())) {
                        response_builder.insert_header(("cache-control", "no-cache"));
                        response_builder.insert_header(("connection", "keep-alive"));
                    }
                    
                    // Create streaming body
                    let stream = Box::pin(futures::stream::unfold((description, true), move |(description, first_iter)| {
                        Box::pin(async move {
                            let result = Python::with_gil(|py| {
                                let desc = description.as_ref(py);
                                
                                // Handle sync iterator
                                if desc.hasattr("__iter__").unwrap_or(false) {
                                    if let Ok(mut iter) = desc.iter() {
                                        if let Some(Ok(item)) = iter.next() {
                                            let chunk = if item.is_instance_of::<pyo3::types::PyBytes>() {
                                                Some(item.extract::<Vec<u8>>().unwrap())
                                            } else if item.is_instance_of::<pyo3::types::PyString>() {
                                                Some(item.extract::<String>().unwrap().into_bytes())
                                            } else if item.is_instance_of::<pyo3::types::PyInt>() {
                                                Some(item.extract::<i64>().unwrap().to_string().into_bytes())
                                            } else if item.is_instance_of::<pyo3::types::PyDict>() {
                                                Some(serde_json::to_string(
                                                    &item.extract::<serde_json::Value>().unwrap()
                                                ).unwrap().into_bytes())
                                            } else {
                                                Some(item.str().unwrap().extract::<String>().unwrap().into_bytes())
                                            };
                                            
                                            if let Some(chunk) = chunk {
                                                return Some((Ok(Bytes::from(chunk)), (description, false)));
                                            }
                                        }
                                    }
                                }
                                // Handle async generator
                                else if desc.hasattr("__aiter__").unwrap_or(false) {
                                    if let Ok(agen) = if first_iter {
                                        desc.call_method0("__aiter__")
                                    } else {
                                        Ok(desc)
                                    } {
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
                                                                Some(item.extract::<Vec<u8>>().unwrap())
                                                            } else if item.is_instance_of::<pyo3::types::PyString>() {
                                                                Some(item.extract::<String>().unwrap().into_bytes())
                                                            } else if item.is_instance_of::<pyo3::types::PyInt>() {
                                                                Some(item.extract::<i64>().unwrap().to_string().into_bytes())
                                                            } else if item.is_instance_of::<pyo3::types::PyDict>() {
                                                                Some(serde_json::to_string(
                                                                    &item.extract::<serde_json::Value>().unwrap()
                                                                ).unwrap().into_bytes())
                                                            } else {
                                                                Some(item.str().unwrap().extract::<String>().unwrap().into_bytes())
                                                            }
                                                        });

                                                        if let Some(chunk) = chunk {
                                                            return Some((Ok(Bytes::from(chunk)), (agen.into_py(desc.py()), false)));
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
                    })) as Pin<Box<dyn Stream<Item = Result<Bytes, Error>> + Send + 'static>>;
                    
                    response_builder.streaming(stream)
                }
                _ => response_builder.body("") // Return empty response for non-streaming body
            }
        } else {
            match self.body {
                ResponseBody::Text(text) => response_builder.body(text),
                ResponseBody::Binary(data) => response_builder.body(data),
                ResponseBody::Streaming(_) => response_builder.body("") // Return empty response for streaming body without streaming=True
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
            body: ResponseBody::Text("Not found".to_string()),
            file_path: None,
            streaming: false,
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
            streaming: false,
        }
    }

    pub fn from_error(error: PyErr) -> Self {
        let headers = Headers::new(None);
        headers.headers.entry("Content-Type".to_string()).or_default().push("text/plain".to_string());
        headers.headers.entry("X-Error-Response".to_string()).or_default().push("true".to_string());
        headers.headers.entry("global_after".to_string()).or_default().push("global_after_request".to_string());
        headers.headers.entry("server".to_string()).or_default().push("robyn".to_string());

        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers,
            body: ResponseBody::Text(format!("error msg: {}", error)),
            file_path: None,
            streaming: false,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        
        let description = match &self.body {
            ResponseBody::Text(text) => text.clone().into_py(py),
            ResponseBody::Binary(data) => PyBytes::new(py, data).into(),
            ResponseBody::Streaming(desc) => desc.clone_ref(py),
        };

        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type.clone(),
            headers,
            description,
            file_path: self.file_path.clone(),
            streaming: self.streaming,
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
    #[pyo3(get, set)]
    pub streaming: bool,
}

#[pymethods]
impl PyResponse {
    #[new]
    pub fn new(
        py: Python,
        status_code: u16,
        headers: &PyAny,
        description: Py<PyAny>,
        streaming: Option<bool>,
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
            && !desc.hasattr("__iter__")?
            && !desc.hasattr("__aiter__")?
        {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be bytes, str, or an iterator"
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

        // Default to text response type and determine if streaming
        let (response_type, is_streaming) = if desc.is_instance_of::<pyo3::types::PyBytes>() {
            ("binary".to_string(), false)
        } else if desc.hasattr("__iter__")? || desc.hasattr("__aiter__")? {
            ("stream".to_string(), streaming.unwrap_or(true))
        } else {
            ("text".to_string(), false)
        };

        Ok(Self {
            status_code,
            response_type,
            headers: headers_output,
            description,
            file_path: None,
            streaming: is_streaming,
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
        
        // Allow string, bytes, or iterators
        if !desc.is_instance_of::<pyo3::types::PyBytes>()
            && !desc.is_instance_of::<pyo3::types::PyString>()
            && !desc.hasattr("__iter__")?
            && !desc.hasattr("__aiter__")?
        {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Description must be bytes, str, or an iterator"
            ));
        }

        // Update response type and streaming based on new description
        let (response_type, streaming) = if desc.is_instance_of::<pyo3::types::PyBytes>() {
            ("binary".to_string(), false)
        } else if desc.hasattr("__iter__")? || desc.hasattr("__aiter__")? {
            ("stream".to_string(), true)
        } else {
            ("text".to_string(), false)
        };

        self.response_type = response_type;
        self.streaming = streaming;
        self.description = description;
        Ok(())
    }

    #[setter]
    pub fn set_file_path(&mut self, py: Python, file_path: &str) -> PyResult<()> {
        self.file_path = Some(file_path.to_string());
        self.response_type = "binary".to_string();
        self.streaming = false;

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

impl IntoPy<PyObject> for Response {
    fn into_py(self, py: Python) -> PyObject {
        let headers = self.headers.into_py(py);
        
        let description = match &self.body {
            ResponseBody::Text(text) => text.clone().into_py(py),
            ResponseBody::Binary(data) => PyBytes::new(py, data).into(),
            ResponseBody::Streaming(desc) => desc.clone_ref(py),
        };

        PyResponse::new(
            py,
            self.status_code,
            headers.as_ref(py),
            description,
            Some(self.streaming),
        ).unwrap().into_py(py)
    }
}
