use actix_http::{body::BoxBody, StatusCode};
use actix_web::{web::Bytes, HttpRequest, HttpResponse, HttpResponseBuilder, Responder};
use futures::Stream;
use log::debug;
use pyo3::{
    exceptions::PyIOError,
    prelude::*,
    types::{PyBytes, PyDict},
    Bound, IntoPyObject,
};
use std::pin::Pin;
use tokio;

use crate::io_helpers::{apply_hashmap_headers, read_file};
use crate::types::{check_body_type, check_description_type, get_description_from_pyobject};

use super::cookie::{Cookie, Cookies};
use super::headers::Headers;

#[derive(Debug, Clone)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Headers,
    pub description: Vec<u8>,
    pub file_path: Option<String>,
    pub cookies: Cookies,
}

#[derive(Debug, Clone)]
pub struct StreamingResponse {
    pub status_code: u16,
    pub headers: Headers,
    pub content_generator: Py<PyAny>,
    pub media_type: String,
}

#[derive(Debug)]
pub enum ResponseType {
    Standard(Response),
    Streaming(StreamingResponse),
}

impl ResponseType {
    pub fn headers_mut(&mut self) -> &mut Headers {
        match self {
            ResponseType::Standard(response) => &mut response.headers,
            ResponseType::Streaming(streaming_response) => &mut streaming_response.headers,
        }
    }
}

impl Responder for ResponseType {
    type Body = BoxBody;

    fn respond_to(self, req: &HttpRequest) -> HttpResponse<Self::Body> {
        match self {
            ResponseType::Standard(response) => response.respond_to(req),
            ResponseType::Streaming(streaming_response) => streaming_response.respond_to(req),
        }
    }
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder = HttpResponseBuilder::new(
            StatusCode::from_u16(self.status_code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        );
        apply_hashmap_headers(&mut response_builder, &self.headers);

        // Apply cookies as Set-Cookie headers
        for (name, cookie) in &self.cookies.cookies {
            match cookie.to_header_value(name) {
                Ok(header_value) => {
                    response_builder.append_header(("Set-Cookie", header_value));
                }
                Err(e) => {
                    debug!("Skipping invalid cookie '{}': {}", name, e);
                }
            }
        }

        response_builder.body(self.description)
    }
}

impl StreamingResponse {
    pub fn new(
        status_code: u16,
        headers: Headers,
        content_generator: Py<PyAny>,
        media_type: String,
    ) -> Self {
        Self {
            status_code,
            headers,
            content_generator,
            media_type,
        }
    }
}

impl Responder for StreamingResponse {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder = HttpResponseBuilder::new(
            StatusCode::from_u16(self.status_code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        );

        apply_hashmap_headers(&mut response_builder, &self.headers);

        // Only add SSE-specific headers for event-stream responses if not already present
        if self.media_type == "text/event-stream" {
            if !self.headers.contains("Connection".to_string()) {
                response_builder.append_header(("Connection", "keep-alive"));
            }
            if !self.headers.contains("X-Accel-Buffering".to_string()) {
                response_builder.append_header(("X-Accel-Buffering", "no")); // Disable nginx buffering
            }
            if !self.headers.contains("Cache-Control".to_string()) {
                response_builder
                    .append_header(("Cache-Control", "no-cache, no-store, must-revalidate"));
            }
            if !self.headers.contains("Pragma".to_string()) {
                response_builder.append_header(("Pragma", "no-cache"));
            }
            if !self.headers.contains("Expires".to_string()) {
                response_builder.append_header(("Expires", "0"));
            }
        }

        // Create the optimized stream from the Python generator
        let stream = create_python_stream(self.content_generator);

        // Build streaming response with optimized settings
        response_builder.streaming(stream)
    }
}

fn create_python_stream(
    generator: Py<PyAny>,
) -> Pin<Box<dyn Stream<Item = Result<Bytes, actix_web::Error>> + Send>> {
    Box::pin(futures::stream::unfold(generator, |generator| async move {
        // Use spawn_blocking to execute the Python generator call in a separate thread
        // This prevents blocking the async runtime when the generator contains blocking operations
        match tokio::task::spawn_blocking(move || {
            Python::with_gil(|py| {
                let gen = generator.bind(py);

                // Check if this is an async generator first
                let is_async_gen = gen.hasattr("__anext__").unwrap_or(false);

                if is_async_gen {
                    // For async generators, we expect them to be converted to sync generators in Python
                    debug!("Detected async generator - this should be handled in Python layer");
                    None
                } else {
                    // Try to get the next value from the generator (sync)
                    match gen.call_method0("__next__") {
                        Ok(value) => {
                            // Try bytes first (common for binary file streaming),
                            // then fall back to string extraction
                            if let Ok(py_bytes) = value.downcast::<PyBytes>() {
                                let data = py_bytes.as_bytes().to_vec();
                                debug!("Generator yielded {} bytes", data.len());
                                Some((data, generator))
                            } else if let Ok(string_value) = value.extract::<String>() {
                                debug!("Generator yielded string of len {}", string_value.len());
                                Some((string_value.into_bytes(), generator))
                            } else {
                                let type_name = value
                                    .get_type()
                                    .name()
                                    .map(|n| n.to_string())
                                    .unwrap_or_else(|_| "unknown".to_string());
                                debug!("Generator yielded unsupported type: {}", type_name);
                                None // End of stream
                            }
                        }
                        Err(call_err) => {
                            // Check if this is a StopIteration (normal end) or actual error
                            if call_err.is_instance_of::<pyo3::exceptions::PyStopIteration>(py) {
                                debug!("Generator exhausted (StopIteration)");
                            } else {
                                debug!("Generator call error: {}", call_err);
                            }
                            None // End of stream
                        }
                    }
                }
            })
        })
        .await
        {
            Ok(Some((data, generator))) => Some((Ok(Bytes::from(data)), generator)),
            Ok(None) => None,
            Err(join_err) => {
                debug!(
                    "Failed to execute generator call in spawn_blocking: {}",
                    join_err
                );
                None
            }
        }
    }))
}

impl Response {
    fn default_text_headers() -> Headers {
        let mut headers = Headers::new(None);
        headers.set("Content-Type".to_string(), "text/plain".to_string());
        headers
    }

    pub fn not_found(headers: Option<&Headers>) -> Self {
        const NOT_FOUND_BYTES: &[u8] = b"Not found";

        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers: headers.cloned().unwrap_or_else(Self::default_text_headers),
            description: NOT_FOUND_BYTES.to_vec(),
            file_path: None,
            cookies: Cookies::new(),
        }
    }

    pub fn internal_server_error(headers: Option<&Headers>) -> Self {
        const SERVER_ERROR_BYTES: &[u8] = b"Internal server error";

        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers: headers.cloned().unwrap_or_else(Self::default_text_headers),
            description: SERVER_ERROR_BYTES.to_vec(),
            file_path: None,
            cookies: Cookies::new(),
        }
    }

    pub fn method_not_allowed(headers: Option<&Headers>) -> Self {
        const METHOD_NOT_ALLOWED_BYTES: &[u8] = b"Method not allowed";

        Self {
            status_code: 405,
            response_type: "text".to_string(),
            headers: headers.cloned().unwrap_or_else(Self::default_text_headers),
            description: METHOD_NOT_ALLOWED_BYTES.to_vec(),
            file_path: None,
            cookies: Cookies::new(),
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

        let cookies: Py<Cookies> = Py::new(py, self.cookies)?;

        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type,
            headers,
            description: description.into(),
            file_path: self.file_path,
            cookies,
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
    #[pyo3(get)]
    pub cookies: Py<Cookies>,
}

#[pyclass(name = "StreamingResponse")]
#[derive(Debug, Clone)]
pub struct PyStreamingResponse {
    #[pyo3(get)]
    pub status_code: u16,
    #[pyo3(get, set)]
    pub headers: Py<Headers>,
    #[pyo3(get)]
    pub content: Py<PyAny>,
    #[pyo3(get)]
    pub media_type: String,
}

#[pymethods]
impl PyStreamingResponse {
    #[new]
    pub fn new(
        py: Python,
        content: Py<PyAny>,
        status_code: Option<u16>,
        headers: Option<Bound<'_, PyAny>>,
        media_type: Option<String>,
    ) -> PyResult<Self> {
        let status_code = status_code.unwrap_or(200);
        let media_type = media_type.unwrap_or_else(|| "text/event-stream".to_string());

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
            let mut headers = Headers::new(None);
            if media_type == "text/event-stream" {
                headers.set("Content-Type".to_string(), "text/event-stream".to_string());
                headers.set("Connection".to_string(), "keep-alive".to_string());
            } else {
                // For non-SSE streaming responses, still set appropriate headers
                headers.set("Content-Type".to_string(), media_type.clone());
            }
            Py::new(py, headers)?
        };

        Ok(Self {
            status_code,
            headers: headers_output,
            content,
            media_type,
        })
    }
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

        let cookies: Py<Cookies> = Py::new(py, Cookies::new())?;

        Ok(Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers: headers_output,
            description,
            file_path: None,
            cookies,
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

    #[pyo3(signature = (key, value, path=None, domain=None, max_age=None, expires=None, secure=false, http_only=false, same_site=None))]
    pub fn set_cookie(
        &mut self,
        py: Python,
        key: &str,
        value: &str,
        path: Option<String>,
        domain: Option<String>,
        max_age: Option<i64>,
        expires: Option<String>,
        secure: bool,
        http_only: bool,
        same_site: Option<String>,
    ) -> PyResult<()> {
        let cookie = Cookie::new(
            value.to_string(),
            path,
            domain,
            max_age,
            expires,
            secure,
            http_only,
            same_site,
        );

        self.cookies
            .try_borrow_mut(py)
            .expect("value already borrowed")
            .set(key.to_string(), cookie);
        Ok(())
    }
}

impl FromPyObject<'_, '_> for Response {
    type Error = PyErr;

    fn extract(obj: pyo3::Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
        // Only extract from actual Response objects, not StreamingResponse
        let type_name = obj.get_type().name()?;
        debug!("Attempting to extract Response from type: {}", type_name);
        if type_name != "Response" {
            debug!("Type mismatch: expected Response, got {}", type_name);
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                "Expected Response, got {}",
                type_name
            )));
        }

        let status_code: u16 = obj.getattr("status_code")?.extract()?;
        let response_type: String = obj.getattr("response_type")?.extract()?;
        let headers: Headers = obj.getattr("headers")?.extract()?;
        let description: Vec<u8> = get_description_from_pyobject(&obj.getattr("description")?)?;
        let file_path: Option<String> = obj.getattr("file_path")?.extract()?;
        let cookies: Cookies = obj.getattr("cookies")?.extract()?;

        debug!(
            "Successfully extracted Response with status {}",
            status_code
        );
        Ok(Response {
            status_code,
            response_type,
            headers,
            description,
            file_path,
            cookies,
        })
    }
}

impl FromPyObject<'_, '_> for StreamingResponse {
    type Error = PyErr;

    fn extract(obj: pyo3::Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
        // Check if it's a StreamingResponse by checking attributes rather than strict type name
        let type_name = obj
            .get_type()
            .name()
            .map(|n| n.to_string())
            .unwrap_or_else(|_| "unknown".to_string());
        debug!("=== STREAMING RESPONSE EXTRACTION START ===");
        debug!(
            "Attempting to extract StreamingResponse from type: {}",
            type_name
        );

        // Check if it has the required attributes for a StreamingResponse
        let has_content = obj.hasattr("content").unwrap_or(false);
        let has_status_code = obj.hasattr("status_code").unwrap_or(false);
        let has_headers = obj.hasattr("headers").unwrap_or(false);
        let has_media_type = obj.hasattr("media_type").unwrap_or(false);

        debug!(
            "Attribute check: content={}, status_code={}, headers={}, media_type={}",
            has_content, has_status_code, has_headers, has_media_type
        );

        // For StreamingResponse, we need content and media_type specifically
        if !has_content || !has_status_code || !has_headers || !has_media_type {
            debug!("Missing required StreamingResponse attributes");
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                "Object is missing required StreamingResponse attributes"
            )));
        }

        debug!("All attributes present, proceeding with extraction");

        let status_code: u16 = match obj.getattr("status_code") {
            Ok(attr) => match attr.extract() {
                Ok(code) => {
                    debug!("Successfully extracted status_code: {}", code);
                    code
                }
                Err(e) => {
                    debug!("Failed to extract status_code as u16: {}", e);
                    return Err(e);
                }
            },
            Err(e) => {
                debug!("Failed to get status_code attribute: {}", e);
                return Err(e);
            }
        };

        let mut headers: Headers = match obj.getattr("headers") {
            Ok(attr) => match attr.extract() {
                Ok(headers) => {
                    debug!("Successfully extracted headers");
                    headers
                }
                Err(e) => {
                    debug!("Failed to extract headers: {}", e);
                    return Err(e.into());
                }
            },
            Err(e) => {
                debug!("Failed to get headers attribute: {}", e);
                return Err(e);
            }
        };

        // Ensure proper SSE headers are set if media_type is text/event-stream
        let media_type: String = match obj.getattr("media_type") {
            Ok(attr) => match attr.extract() {
                Ok(media_type) => {
                    debug!("Successfully extracted media_type: {}", media_type);
                    media_type
                }
                Err(e) => {
                    debug!("Failed to extract media_type: {}", e);
                    "text/event-stream".to_string()
                }
            },
            Err(e) => {
                debug!("Failed to get media_type attribute: {}", e);
                "text/event-stream".to_string()
            }
        };

        // Set proper SSE headers if needed
        if media_type == "text/event-stream" {
            headers.set("Content-Type".to_string(), "text/event-stream".to_string());
            if headers.get("Connection".to_string()).is_none() {
                headers.set("Connection".to_string(), "keep-alive".to_string());
            }
        }

        let content: pyo3::Py<PyAny> = match obj.getattr("content") {
            Ok(attr) => {
                debug!("Successfully got content attribute");
                attr.unbind()
            }
            Err(e) => {
                debug!("Failed to get content attribute: {}", e);
                return Err(e);
            }
        };

        debug!("=== STREAMING RESPONSE EXTRACTION SUCCESS ===");
        debug!(
            "Successfully extracted StreamingResponse with status {} from type {}",
            status_code, type_name
        );
        Ok(StreamingResponse::new(
            status_code,
            headers,
            content,
            media_type,
        ))
    }
}
