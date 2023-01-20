use std::collections::HashMap;

use actix_web::web::Bytes;
use actix_web::{http::Method, HttpRequest};
use anyhow::Result;
use dashmap::DashMap;
use pyo3::{exceptions, prelude::*};

use crate::io_helpers::read_file;

#[pyclass]
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    pub handler: Py<PyAny>,
    pub is_async: bool,
    pub number_of_params: u8,
    pub validator: Py<PyAny>,
}

#[pymethods]
impl FunctionInfo {
    #[new]
    pub fn new(handler: Py<PyAny>, is_async: bool, number_of_params: u8, validator: Py<PyAny>) -> Self {
        Self {
            handler,
            is_async,
            number_of_params,
            validator,
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
    pub body: String,
    pub file_path: Option<String>,
}

#[pymethods]
impl Response {
    #[new]
    pub fn new(status_code: u16, headers: HashMap<String, String>, body: String) -> Self {
        Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers,
            body,
            file_path: None,
        }
    }

    pub fn set_file_path(&mut self, file_path: &str) -> PyResult<()> {
        // we should be handling based on headers but works for now
        self.response_type = "static_file".to_string();
        self.file_path = Some(file_path.to_string());
        self.body = match read_file(file_path) {
            Ok(b) => b,
            Err(e) => return Err(exceptions::PyIOError::new_err::<String>(e.to_string())),
        };
        Ok(())
    }
}

pub type Headers = DashMap<String, String>;
