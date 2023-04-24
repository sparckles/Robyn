use actix_web::{web::Bytes, HttpRequest};
use dashmap::DashMap;
use pyo3::{prelude::*, types::PyDict};
use std::collections::HashMap;

use crate::types::{check_body_type, get_body_from_pyobject, Url};

#[derive(Default, Clone, FromPyObject)]
pub struct Request {
    pub queries: HashMap<String, String>,
    pub headers: HashMap<String, String>,
    pub method: String,
    pub path_params: HashMap<String, String>,
    #[pyo3(from_py_with = "get_body_from_pyobject")]
    pub body: Vec<u8>,
    pub url: Url,
}

impl ToPyObject for Request {
    fn to_object(&self, py: Python) -> PyObject {
        let queries = self.queries.clone().into_py(py).extract(py).unwrap();
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        let path_params = self.path_params.clone().into_py(py).extract(py).unwrap();
        let body = match String::from_utf8(self.body.clone()) {
            Ok(s) => s.into_py(py),
            Err(_) => self.body.clone().into_py(py),
        };

        let request = PyRequest {
            queries,
            path_params,
            headers,
            body,
            method: self.method.clone(),
            url: self.url.clone(),
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
        let mut queries = HashMap::new();
        if !req.query_string().is_empty() {
            let split = req.query_string().split('&');
            for s in split {
                let path_params = s.split_once('=').unwrap_or((s, ""));
                queries.insert(path_params.0.to_string(), path_params.1.to_string());
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

        Self {
            queries,
            headers,
            method: req.method().as_str().to_owned(),
            path_params: HashMap::new(),
            body: body.to_vec(),
            url,
        }
    }
}

#[pyclass(name = "Request")]
#[derive(Clone)]
pub struct PyRequest {
    #[pyo3(get, set)]
    pub queries: Py<PyDict>,
    #[pyo3(get, set)]
    pub headers: Py<PyDict>,
    #[pyo3(get, set)]
    pub path_params: Py<PyDict>,
    #[pyo3(get)]
    pub body: Py<PyAny>,
    #[pyo3(get)]
    pub method: String,
    #[pyo3(get)]
    pub url: Url,
}

#[pymethods]
impl PyRequest {
    #[setter]
    pub fn set_body(&mut self, py: Python, body: Py<PyAny>) -> PyResult<()> {
        check_body_type(py, body.clone())?;
        self.body = body;
        Ok(())
    }
}
