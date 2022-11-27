use std::collections::HashMap;

use actix_web::http::Method;
use actix_web::web::Bytes;
use anyhow::Result;
use dashmap::DashMap;
use pyo3::prelude::*;

#[pyclass]
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    pub handler: Py<PyAny>,
    pub is_async: bool,
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
    pub fn to_hashmap(&self, py: Python<'_>) -> Result<HashMap<&str, Py<PyAny>>> {
        let mut result = HashMap::new();
        result.insert("params", self.params.to_object(py));
        result.insert("queries", self.queries.to_object(py));
        result.insert("headers", self.headers.to_object(py));
        result.insert("body", self.body.to_object(py));
        Ok(result)
    }
}

pub type Headers = DashMap<String, String>;
