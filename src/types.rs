use std::{collections::HashMap, str::FromStr};

use actix_http::StatusCode;
use actix_web::web::Bytes;
use actix_web::{http::Method, HttpRequest};
use anyhow::{Context, Result};
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
pub struct Response {
    pub status_code: StatusCode,
    pub headers: HashMap<String, String>,
    pub body: String,
}

impl Response {
    pub fn from_hashmap(input: HashMap<String, String>) -> Result<Self> {
        let status_code = actix_http::StatusCode::from_str(
            input
                .get("status_code")
                .context("No status code in content")?,
        )?;
        let headers = match input.get("headers") {
            Some(h) => serde_json::from_str(h)?,
            None => HashMap::new(),
        };
        let body = input.get("body").context("No body in content")?.to_owned();
        Ok(Self {
            status_code,
            headers,
            body,
        })
    }
}

pub type Headers = DashMap<String, String>;
