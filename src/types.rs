use core::mem;
use std::collections::HashMap;
use std::ops::{Deref, DerefMut};
use std::{
    convert::Infallible,
    pin::Pin,
    task::{Context, Poll},
};

use actix_http::body::MessageBody;
use actix_http::body::{BodySize, BoxBody};
use actix_http::StatusCode;
use actix_web::web::Bytes;
use actix_web::{http::Method, HttpRequest};
use actix_web::{HttpResponse, HttpResponseBuilder, Responder};
use anyhow::Result;
use dashmap::DashMap;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyBytes, PyDict, PyString};
use pyo3::{exceptions, intern, prelude::*};

use crate::io_helpers::{apply_hashmap_headers, read_file};

fn type_of<T>(_: &T) -> String {
    std::any::type_name::<T>().to_string()
}

#[derive(Debug, Clone, Default)]
#[pyclass(name = "Body")]
pub struct ActixBytesWrapper {
    content: Bytes,
}

#[pymethods]
impl ActixBytesWrapper {
    pub fn as_str(&self) -> PyResult<String> {
        Ok(String::from_utf8(self.content.to_vec())?)
    }

    pub fn as_bytes(&self) -> PyResult<Vec<u8>> {
        Ok(self.content.to_vec())
    }

    pub fn set(&mut self, content: &PyAny) -> PyResult<()> {
        let value = if let Ok(v) = content.downcast::<PyString>() {
            v.to_string().into_bytes()
        } else if let Ok(v) = content.downcast::<PyBytes>() {
            v.as_bytes().to_vec()
        } else {
            return Err(PyValueError::new_err(format!(
                "Could not convert {} specified body to bytes",
                type_of(content)
            )));
        };
        self.content = Bytes::from(value);
        Ok(())
    }
}

// provides an interface between pyo3::types::{PyString, PyBytes} and actix_web::web::Bytes
impl ActixBytesWrapper {
    pub fn new(raw_body: &PyAny) -> PyResult<Self> {
        let value = if let Ok(v) = raw_body.downcast::<PyString>() {
            v.to_string().into_bytes()
        } else if let Ok(v) = raw_body.downcast::<PyBytes>() {
            v.as_bytes().to_vec()
        } else {
            return Err(PyValueError::new_err(format!(
                "Could not convert {} specified body to bytes",
                type_of(raw_body)
            )));
        };
        Ok(Self {
            content: Bytes::from(value),
        })
    }

    pub fn from_str(raw_body: &str) -> Self {
        Self {
            content: Bytes::from(raw_body.to_string()),
        }
    }
}

impl Deref for ActixBytesWrapper {
    type Target = Bytes;

    fn deref(&self) -> &Self::Target {
        &self.content
    }
}

impl DerefMut for ActixBytesWrapper {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.content
    }
}

impl MessageBody for ActixBytesWrapper {
    type Error = Infallible;

    #[inline]
    fn size(&self) -> BodySize {
        BodySize::Sized(self.len() as u64)
    }

    #[inline]
    fn poll_next(
        self: Pin<&mut Self>,
        _cx: &mut Context<'_>,
    ) -> Poll<Option<Result<Bytes, Self::Error>>> {
        if self.is_empty() {
            Poll::Ready(None)
        } else {
            Poll::Ready(Some(Ok(mem::take(self.get_mut()))))
        }
    }

    #[inline]
    fn try_into_bytes(self) -> Result<Bytes, Self> {
        Ok(self.content)
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    #[pyo3(get, set)]
    pub handler: Py<PyAny>,
    #[pyo3(get, set)]
    pub is_async: bool,
    #[pyo3(get, set)]
    pub number_of_params: u8,
}

#[pymethods]
impl FunctionInfo {
    #[new]
    pub fn new(handler: Py<PyAny>, is_async: bool, number_of_params: u8) -> Self {
        Self {
            handler,
            is_async,
            number_of_params,
        }
    }
}

#[derive(Default, Clone)]
pub struct Url {
    pub scheme: String,
    pub host: String,
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

    pub fn to_object(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item(intern!(py, "scheme"), self.scheme.as_str())?;
        dict.set_item(intern!(py, "host"), self.host.as_str())?;
        dict.set_item(intern!(py, "path"), self.path.as_str())?;
        Ok(dict.into_py(py))
    }
}

#[pyclass]
#[derive(Default, Clone)]
pub struct Request {
    #[pyo3(get, set)]
    pub queries: HashMap<String, String>,
    #[pyo3(get, set)]
    pub headers: HashMap<String, String>,
    pub method: Method,
    #[pyo3(get, set)]
    pub params: HashMap<String, String>,
    pub body: Bytes,
    pub url: Url,
}

impl Request {
    pub fn from_actix_request(
        req: &HttpRequest,
        body: Bytes,
        global_headers: &DashMap<String, String>,
    ) -> Self {
        let mut queries = HashMap::new();
        if !req.query_string().is_empty() {
            let split = req.query_string().split('&');
            for s in split {
                let params = s.split_once('=').unwrap_or((s, ""));
                queries.insert(params.0.to_string(), params.1.to_string());
            }
        }
        let request_headers = req
            .headers()
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_str().unwrap().to_string()))
            .chain(
                global_headers
                    .iter()
                    .map(|h| (h.key().clone(), h.value().clone())),
            )
            .collect();

        Self {
            queries,
            headers: request_headers,
            method: req.method().clone(),
            params: HashMap::new(),
            body,
            url: Url::new(
                req.connection_info().scheme(),
                req.connection_info().host(),
                req.path(),
            ),
        }
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    #[pyo3(get, set)]
    pub headers: HashMap<String, String>,
    #[pyo3(get)]
    pub body: ActixBytesWrapper,
    pub file_path: Option<String>,
}

impl Responder for Response {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        let mut response_builder =
            HttpResponseBuilder::new(StatusCode::from_u16(self.status_code).unwrap());
        apply_hashmap_headers(&mut response_builder, &self.headers);
        response_builder.body(self.body)
    }
}

impl Response {
    pub fn not_found(headers: &HashMap<String, String>) -> Self {
        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers: headers.clone(),
            body: ActixBytesWrapper::from_str("Not found"),
            file_path: None,
        }
    }

    pub fn internal_server_error(headers: &HashMap<String, String>) -> Self {
        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers: headers.clone(),
            body: ActixBytesWrapper::from_str("Internal server error"),
            file_path: None,
        }
    }
}

#[pymethods]
impl Response {
    // To do: Add check for content-type in header and change response_type accordingly
    #[new]
    pub fn new(status_code: u16, headers: HashMap<String, String>, body: &PyAny) -> PyResult<Self> {
        Ok(Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers,
            body: ActixBytesWrapper::new(body)?,
            file_path: None,
        })
    }

    pub fn set_body(&mut self, body: &PyAny) -> PyResult<()> {
        self.body = ActixBytesWrapper::new(body)?;
        Ok(())
    }

    pub fn set_file_path(&mut self, file_path: &str) -> PyResult<()> {
        // we should be handling based on headers but works for now
        self.response_type = "static_file".to_string();
        self.file_path = Some(file_path.to_string());
        self.body = ActixBytesWrapper {
            content: Bytes::from(
                read_file(file_path)
                    .map_err(|e| PyErr::new::<exceptions::PyIOError, _>(e.to_string()))?,
            ),
        };
        Ok(())
    }
}

pub type Headers = DashMap<String, String>;
