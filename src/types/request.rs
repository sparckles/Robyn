use actix_multipart::Multipart;
use actix_web::{
    web::{self, BytesMut},
    Error, HttpRequest,
};
use futures_util::StreamExt as _;
use log::debug;
use pyo3::types::{PyBytes, PyDict, PyList, PyString};
use pyo3::{exceptions::PyValueError, prelude::*, IntoPyObject};
use serde_json::Value;
use std::collections::HashMap;

use crate::types::{check_body_type, get_body_from_pyobject, Url};

use super::{headers::Headers, identity::Identity, multimap::QueryParams};

#[derive(Default, Debug, Clone, FromPyObject)]
pub struct Request {
    pub query_params: QueryParams,
    pub headers: Headers,
    pub method: String,
    pub path_params: HashMap<String, String>,
    // https://pyo3.rs/v0.19.2/function.html?highlight=from_py_#per-argument-options
    #[pyo3(from_py_with = get_body_from_pyobject)]
    pub body: Vec<u8>,
    pub url: Url,
    pub ip_addr: Option<String>,
    pub identity: Option<Identity>,
    pub form_data: Option<HashMap<String, String>>,
    pub files: Option<HashMap<String, Vec<u8>>>,
}

impl<'py> IntoPyObject<'py> for Request {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;
    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let headers: Py<Headers> = self.headers.into_pyobject(py)?.extract()?;
        let path_params = self.path_params.into_pyobject(py)?.extract()?;

        let body = if self.body.is_empty() {
            PyString::new(py, "").into_any()
        } else {
            match std::str::from_utf8(&self.body) {
                Ok(s) => PyString::new(py, s).into_any(),
                Err(_) => PyBytes::new(py, &self.body).into_any(),
            }
        };

        let form_data: Py<PyDict> = match self.form_data {
            Some(data) if !data.is_empty() => {
                let dict = PyDict::new(py);
                // Use with_capacity equivalent by setting items directly
                for (key, value) in data {
                    dict.set_item(key, value)?;
                }
                dict.into()
            }
            _ => PyDict::new(py).into(),
        };

        let files: Py<PyDict> = match self.files {
            Some(data) if !data.is_empty() => {
                let dict = PyDict::new(py);
                for (key, value) in data {
                    let bytes = PyBytes::new(py, &value);
                    dict.set_item(key, bytes)?;
                }
                dict.into()
            }
            _ => PyDict::new(py).into(),
        };

        let request = PyRequest {
            query_params: self.query_params,
            path_params,
            headers,
            body: body.into(),
            method: self.method,
            url: self.url,
            ip_addr: self.ip_addr,
            identity: self.identity,
            form_data,
            files,
        };
        Ok(Py::new(py, request)?.into_bound(py).into_any())
    }
}

async fn handle_multipart(
    mut payload: Multipart,
    files: &mut HashMap<String, Vec<u8>>,
    form_data: &mut HashMap<String, String>,
    body: &mut Vec<u8>,
) -> Result<(), Error> {
    // Iterate over multipart stream

    while let Some(item) = payload.next().await {
        let mut field = item?;

        let mut data = Vec::new();
        // Read the field data
        while let Some(chunk) = field.next().await {
            debug!("Chunk: {:?}", chunk);
            let data_chunk = chunk?;
            data.extend_from_slice(&data_chunk);
        }

        let content_disposition = field.content_disposition();
        let field_name = content_disposition.get_name().unwrap_or_default();
        let file_name = content_disposition.get_filename().map(|s| s.to_string());

        body.extend_from_slice(&data);

        if let Some(name) = file_name {
            files.insert(name, data);
        } else if let Ok(text) = String::from_utf8(data) {
            form_data.insert(field_name.to_string(), text);
        }
    }

    Ok(())
}

impl Request {
    pub async fn from_actix_request(
        req: &HttpRequest,
        mut payload: web::Payload,
        global_headers: &Headers,
    ) -> Self {
        let mut query_params: QueryParams = QueryParams::new();
        let mut form_data: HashMap<String, String> = HashMap::new();
        let mut files = HashMap::new();

        if !req.query_string().is_empty() {
            let split = req.query_string().split('&');
            for s in split {
                let path_params = s.split_once('=').unwrap_or((s, ""));
                let key = path_params.0.to_string();
                let value = path_params.1.to_string();

                query_params.set(key, value);
            }
        }

        let mut headers = Headers::from_actix_headers(req.headers());
        debug!("Global headers: {:?}", global_headers);
        headers.extend(global_headers);

        let body: Vec<u8> = if headers.contains(String::from("content-type"))
            && headers
                .get(String::from("content-type"))
                .is_some_and(|val| val.contains("multipart/form-data"))
        {
            let h = headers.get(String::from("content-type")).unwrap();
            debug!("Content-Type: {:?}", h);
            let multipart = Multipart::new(req.headers(), payload);
            let mut body_local: Vec<u8> = Vec::new();

            let a = handle_multipart(multipart, &mut files, &mut form_data, &mut body_local).await;

            if let Err(e) = a {
                debug!("Error handling multipart data: {:?}", e);
            }

            body_local
        } else {
            let mut body_local = BytesMut::new();
            while let Some(chunk) = payload.next().await {
                let chunk = chunk.expect("Failed to read chunk from payload");
                body_local.extend_from_slice(&chunk);
            }
            body_local.freeze().to_vec()
        };

        debug!("Request body: {:?}", body);
        debug!("Request headers: {:?}", headers);
        debug!("Request query params: {:?}", query_params);
        debug!("Request form data: {:?}", form_data);
        debug!("Request files: {:?}", files);

        // Normalizing Path.
        // Rules:
        // 1. Other than Root("/"), "/endpoint/" will be routed to "/endpoint" internally, without any client redirection.
        let route_path = {
            let mut path = req.path();
            if path.ends_with("/") && path.len() > 1 {
                path = &path[..path.len() - 1]
            }
            path
        };

        let url = Url::new(
            req.connection_info().scheme(),
            req.connection_info().host(),
            route_path,
        );
        let ip_addr = req.peer_addr().map(|val| val.ip().to_string());

        Self {
            query_params,
            headers,
            method: req.method().as_str().to_owned(),
            path_params: HashMap::new(),
            body,
            url,
            ip_addr,
            identity: None,
            form_data: Some(form_data),
            files: Some(files),
        }
    }
}

#[pyclass(name = "Request")]
#[derive(Clone)]
pub struct PyRequest {
    #[pyo3(get, set)]
    pub query_params: QueryParams,
    #[pyo3(get, set)]
    pub headers: Py<Headers>,
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
    #[pyo3(get, set)]
    pub form_data: Py<PyDict>,
    #[pyo3(get, set)]
    pub files: Py<PyDict>,
}

#[pymethods]
impl PyRequest {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        query_params: QueryParams,
        headers: Py<Headers>,
        path_params: Py<PyDict>,
        body: Py<PyAny>,
        method: String,
        url: Url,
        form_data: Py<PyDict>,
        files: Py<PyDict>,
        identity: Option<Identity>,
        ip_addr: Option<String>,
    ) -> Self {
        Self {
            query_params,
            headers,
            path_params,
            identity,
            body,
            method,
            url,
            form_data,
            files,
            ip_addr,
        }
    }

    #[setter]
    pub fn set_body(&mut self, py: Python, body: Py<PyAny>) -> PyResult<()> {
        check_body_type(py, &body)?;
        self.body = body;
        Ok(())
    }

    pub fn json(&self, py: Python) -> PyResult<Py<PyAny>> {
        match self.body.downcast_bound::<PyString>(py) {
            Ok(python_string) => match serde_json::from_str(python_string.extract()?) {
                Ok(Value::Object(map)) => {
                    let dict = PyDict::new(py);

                    for (key, value) in map.iter() {
                        let py_key = key.to_string().into_pyobject(py)?.into_any();
                        let py_value = json_value_to_py(py, value)?;
                        dict.set_item(py_key, py_value)?;
                    }

                    Ok(dict.into_pyobject(py)?.into_any().into())
                }
                _ => Err(PyValueError::new_err("Invalid JSON object")),
            },
            Err(e) => Err(e.into()),
        }
    }
}

/// Maximum allowed recursion depth for JSON parsing to prevent stack overflow attacks.
const MAX_JSON_DEPTH: usize = 128;

/// Converts a serde_json::Value to a Python object with proper type preservation.
/// This is a convenience wrapper that starts recursion with MAX_JSON_DEPTH.
fn json_value_to_py(py: Python, value: &Value) -> PyResult<Py<PyAny>> {
    json_value_to_py_with_depth(py, value, MAX_JSON_DEPTH)
}

/// Converts a serde_json::Value to a Python object with recursion depth limiting.
fn json_value_to_py_with_depth(py: Python, value: &Value, depth: usize) -> PyResult<Py<PyAny>> {
    if depth == 0 {
        return Err(PyValueError::new_err(
            "JSON nesting depth exceeds maximum allowed limit",
        ));
    }

    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(b) => Ok(b.into_pyobject(py)?.to_owned().into_any().unbind()),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_pyobject(py)?.into_any().unbind())
            } else if let Some(u) = n.as_u64() {
                Ok(u.into_pyobject(py)?.into_any().unbind())
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_pyobject(py)?.into_any().unbind())
            } else {
                Err(PyValueError::new_err("Invalid number in JSON"))
            }
        }
        Value::String(s) => Ok(s.as_str().into_pyobject(py)?.into_any().unbind()),
        Value::Array(arr) => {
            let list = PyList::empty(py);
            for item in arr {
                list.append(json_value_to_py_with_depth(py, item, depth - 1)?)?;
            }
            Ok(list.into_pyobject(py)?.into_any().unbind())
        }
        Value::Object(map) => {
            let dict = PyDict::new(py);
            for (k, v) in map {
                dict.set_item(k, json_value_to_py_with_depth(py, v, depth - 1)?)?;
            }
            Ok(dict.into_pyobject(py)?.into_any().unbind())
        }
    }
}
