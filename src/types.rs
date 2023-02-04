use core::{mem};
use std::ops::{Deref, DerefMut};
use std::{
    convert::Infallible,
    task::{Context, Poll},
    pin::Pin,
};
use std::collections::HashMap;

use actix_web::web::Bytes;
use actix_web::{http::Method, HttpRequest};
use actix_http::body::MessageBody;
use actix_http::body::BodySize;

use anyhow::Result;
use dashmap::DashMap;
use pyo3::{exceptions, prelude::*};
use pyo3::types::{PyBytes, PyString};
use pyo3::exceptions::PyValueError;

use crate::io_helpers::read_file;

fn type_of<T>(_: &T) -> String {
    std::any::type_name::<T>().to_string()
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct ActixBytesWrapper(Bytes);

// provides an interface between pyo3::types::{PyString, PyBytes} and actix_web::web::Bytes
impl ActixBytesWrapper {
    pub fn new(raw_body: &PyAny) -> PyResult<Self> {
        let value = if let Ok(v) = raw_body.downcast::<PyString>() {
            v.to_string().into_bytes()
        } else if let Ok(v) = raw_body.downcast::<PyBytes>() {
            v.as_bytes().to_vec()
        } else {
            return Err(PyValueError::new_err(
                format!("Could not convert {} specified body to bytes", type_of(raw_body))
            ));
        };
        Ok(Self(Bytes::from(value)))
    }
}

impl Deref for ActixBytesWrapper {
    type Target = Bytes;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl DerefMut for ActixBytesWrapper {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
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
        Ok(self.0)
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

#[derive(Default)]
pub struct Request {
    pub queries: HashMap<String, String>,
    pub headers: HashMap<String, String>,
    pub method: Method,
    pub params: HashMap<String, String>,
    pub body: Bytes,
}

impl Request {
    pub fn from_actix_request(req: &HttpRequest, body: Bytes) -> Self {
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
            .collect();

        Self {
            queries,
            headers: request_headers,
            method: req.method().clone(),
            params: HashMap::new(),
            body,
        }
    }

    pub fn to_hashmap(&self, py: Python<'_>) -> Result<HashMap<&str, Py<PyAny>>> {
        let mut result = HashMap::new();
        result.insert("params", self.params.to_object(py));
        result.insert("queries", self.queries.to_object(py));
        result.insert("headers", self.headers.to_object(py));
        result.insert("body", self.body.to_object(py));
        Ok(result)
    }
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: HashMap<String, String>,
    pub body: ActixBytesWrapper,
    pub file_path: Option<String>,
}

#[pymethods]
impl Response {
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

    pub fn set_file_path(&mut self, file_path: &str) -> PyResult<()> {
        // we should be handling based on headers but works for now
        self.response_type = "static_file".to_string();
        self.file_path = Some(file_path.to_string());
        let response = match read_file(file_path) {
            Ok(b) => b,
            Err(e) => return Err(exceptions::PyIOError::new_err::<String>(e.to_string())),
        };
        self.body = ActixBytesWrapper(Bytes::from(response));
        Ok(())
    }
}

pub type Headers = DashMap<String, String>;
