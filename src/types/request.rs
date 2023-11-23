use actix_web::{web::Bytes, HttpRequest};
use dashmap::DashMap;
use pyo3::{exceptions::PyValueError, prelude::*, types::PyDict, types::PyString};
use serde_json::Value;
use std::collections::HashMap;

use crate::types::{check_body_type, get_body_from_pyobject, Url};

use super::{identity::Identity, multimap::QueryParams};

#[derive(Default, Debug, Clone, FromPyObject)]
pub struct Request {
    pub query_params: QueryParams,
    pub headers: HashMap<String, String>,
    pub method: String,
    pub path_params: HashMap<String, String>,
    // https://pyo3.rs/v0.19.2/function.html?highlight=from_py_#per-argument-options
    #[pyo3(from_py_with = "get_body_from_pyobject")]
    pub body: Vec<u8>,
    pub url: Url,
    pub ip_addr: Option<String>,
    pub identity: Option<Identity>,
}

impl ToPyObject for Request {
    fn to_object(&self, py: Python) -> PyObject {
        let query_params = self.query_params.clone();
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        let path_params = self.path_params.clone().into_py(py).extract(py).unwrap();
        let body = match String::from_utf8(self.body.clone()) {
            Ok(s) => s.into_py(py),
            Err(_) => self.body.clone().into_py(py),
        };

        let request = PyRequest {
            query_params,
            path_params,
            headers,
            body,
            method: self.method.clone(),
            url: self.url.clone(),
            ip_addr: self.ip_addr.clone(),
            identity: self.identity.clone(),
        };
        Py::new(py, request).unwrap().as_ref(py).into()
    }
}

impl Request {
    pub fn from_actix_request(
        req: &HttpRequest,
        body: Bytes,
        global_headers: &DashMap<String, String>,
    ) -> Self {
        let mut query_params: QueryParams = QueryParams::new();
        if !req.query_string().is_empty() {
            let split = req.query_string().split('&');
            for s in split {
                let path_params = s.split_once('=').unwrap_or((s, ""));
                let key = path_params.0.to_string();
                let value = path_params.1.to_string();

                query_params.set(key, value);
            }
        }
        let headers = req
            .headers()
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_str().unwrap().to_string()))
            .chain(
                global_headers
                    .iter()
                    .map(|h| (h.key().clone(), h.value().clone())),
            )
            .collect();

        let url = Url::new(
            req.connection_info().scheme(),
            req.connection_info().host(),
            req.path(),
        );
        let ip_addr = req.peer_addr().map(|val| val.ip().to_string());

        Self {
            query_params,
            headers,
            method: req.method().as_str().to_owned(),
            path_params: HashMap::new(),
            body: body.to_vec(),
            url,
            ip_addr,
            identity: None,
        }
    }
}

#[pyclass(name = "Request")]
#[derive(Clone)]
pub struct PyRequest {
    #[pyo3(get, set)]
    pub query_params: QueryParams,
    #[pyo3(get, set)]
    pub headers: Py<PyDict>,
    #[pyo3(get, set)]
    pub path_params: Py<PyDict>,
    #[pyo3(get, set)]
    pub identity: Option<Identity>,
    #[pyo3(get)]
    pub body: Py<PyAny>,
    #[pyo3(get)]
    pub method: String,
    #[pyo3(get)]
    pub url: Url,
    #[pyo3(get)]
    pub ip_addr: Option<String>,
}

#[pymethods]
impl PyRequest {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        query_params: &PyDict,
        headers: Py<PyDict>,
        path_params: Py<PyDict>,
        body: Py<PyAny>,
        method: String,
        url: Url,
        identity: Option<Identity>,
        ip_addr: Option<String>,
    ) -> Self {
        let query_params = QueryParams::from_dict(query_params);

        Self {
            query_params,
            headers,
            path_params,
            identity,
            body,
            method,
            url,
            ip_addr,
        }
    }

    #[setter]
    pub fn set_body(&mut self, py: Python, body: Py<PyAny>) -> PyResult<()> {
        check_body_type(py, body.clone())?;
        self.body = body;
        Ok(())
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        match self.body.as_ref(py).downcast::<PyString>() {
            Ok(python_string) => match serde_json::from_str(python_string.extract()?) {
                Ok(Value::Object(map)) => {
                    let dict = PyDict::new(py);

                    for (key, value) in map.iter() {
                        let py_key = key.to_string().into_py(py);
                        let py_value = value.to_string().into_py(py);
                        dict.set_item(py_key, py_value)?;
                    }

                    Ok(dict.into_py(py))
                }
                _ => Err(PyValueError::new_err("Invalid JSON object")),
            },
            Err(e) => Err(e.into()),
        }
    }
}
