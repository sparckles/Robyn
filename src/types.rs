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
    pub function_type: String,
    pub number_of_params: u8,
}

#[pymethods]
impl FunctionInfo {
    #[new]
    pub fn new(handler: Py<PyAny>, function_type: &str, number_of_params: u8) -> Self {
        match function_type {
            "sync_function" | "async_function" | "sync_generator" => (),
            _ => panic!("Invalid function type"),
        }

        Self {
            handler,
            function_type: function_type.to_string(),
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
