use actix_http::header::HeaderMap;
use dashmap::DashMap;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::IntoPyObject;

// Custom Multimap class
#[pyclass(name = "Headers")]
#[derive(Clone, Debug, Default)]
pub struct Headers {
    pub headers: DashMap<String, Vec<String>>,
}

#[pymethods]
impl Headers {
    #[new]
    pub fn new(default_headers: Option<&Bound<'_, PyDict>>) -> Self {
        match default_headers {
            Some(default_headers) => {
                let headers = DashMap::new();
                for (key, value) in default_headers {
                    let key = key.to_string().to_lowercase();

                    let new_value = value.cast::<PyList>();

                    if let Ok(new_value) = new_value {
                        let value: Vec<String> = new_value.iter().map(|x| x.to_string()).collect();
                        headers.entry(key).or_insert_with(Vec::new).extend(value);
                    } else {
                        let value = value.to_string();
                        headers.entry(key).or_insert_with(Vec::new).push(value);
                    }
                }
                Headers { headers }
            }
            None => Headers {
                headers: DashMap::new(),
            },
        }
    }

    pub fn set(&mut self, key: String, value: String) {
        self.headers.insert(key.to_lowercase(), vec![value]);
    }

    pub fn append(&mut self, key: String, value: String) {
        self.headers
            .entry(key.to_lowercase())
            .or_default()
            .push(value);
    }

    pub fn get_all(&self, py: Python, key: String) -> Py<PyList> {
        match self.headers.get(&key.to_lowercase()) {
            Some(values) => {
                let py_values = PyList::new(
                    py,
                    values
                        .iter()
                        .map(|value| value.into_pyobject(py).unwrap().into_any()),
                );
                py_values.expect("get-all failed").into()
            }
            None => PyList::empty(py).into(),
        }
    }

    pub fn get(&self, key: String) -> Option<String> {
        // return the last value
        match self.headers.get(&key.to_lowercase()) {
            Some(iter) => {
                let (_, values) = iter.pair();
                let last_value = values.last().unwrap();
                Some(last_value.to_string())
            }
            None => None,
        }
    }

    pub fn get_headers(&self, py: Python) -> Py<PyDict> {
        // return as a dict of lists
        let dict = PyDict::new(py);
        for iter in self.headers.iter() {
            let (key, values) = iter.pair();
            let py_values: Bound<'_, PyList> = PyList::new(
                py,
                values
                    .iter()
                    .map(|value| value.into_pyobject(py).unwrap().into_any()),
            )
            .expect("get-all failed");
            dict.set_item(key, py_values).unwrap();
        }
        dict.into()
    }

    pub fn to_dict(&self, py: Python) -> Py<PyDict> {
        // return as a flat dict {key: value}; when a header appears multiple
        // times its values are joined with ", " (per RFC 7230), mirroring the
        // ergonomics of QueryParams.to_dict so callers can use `.get(key, default)`.
        let dict = PyDict::new(py);
        for iter in self.headers.iter() {
            let (key, values) = iter.pair();
            dict.set_item(key, values.join(", ")).unwrap();
        }
        dict.into()
    }

    pub fn keys(&self, py: Python) -> Py<PyList> {
        let keys: Vec<String> = self.headers.iter().map(|e| e.key().clone()).collect();
        PyList::new(py, keys).expect("keys failed").into()
    }

    pub fn values(&self, py: Python) -> Py<PyList> {
        // last value per header, consistent with get()
        let values: Vec<String> = self
            .headers
            .iter()
            .filter_map(|e| e.value().last().cloned())
            .collect();
        PyList::new(py, values).expect("values failed").into()
    }

    pub fn items(&self) -> Vec<(String, String)> {
        // (name, last value) pairs, consistent with get()
        self.headers
            .iter()
            .filter_map(|e| e.value().last().map(|v| (e.key().clone(), v.clone())))
            .collect()
    }

    pub fn multi_items(&self) -> Vec<(String, String)> {
        // (name, value) for every value, preserving duplicate header names
        let mut items = Vec::new();
        for entry in self.headers.iter() {
            for value in entry.value() {
                items.push((entry.key().clone(), value.clone()));
            }
        }
        items
    }

    pub fn contains(&self, key: String) -> bool {
        self.headers.contains_key(&key.to_lowercase())
    }

    pub fn populate_from_dict(&mut self, headers: &Bound<PyDict>) {
        for (key, value) in headers.iter() {
            let key = key.to_string().to_lowercase();
            let new_value = value.cast::<PyList>();

            if let Ok(new_value) = new_value {
                let value: Vec<String> = new_value.iter().map(|x| x.to_string()).collect();
                self.headers.entry(key).or_default().extend(value);
            } else {
                let value = value.to_string();
                self.headers.entry(key).or_default().push(value);
            }
        }
    }

    pub fn is_empty(&self) -> bool {
        self.headers.is_empty()
    }

    fn __eq__(&self, other: &Headers) -> bool {
        if self.headers.is_empty() && other.headers.is_empty() {
            return true;
        }

        if self.headers.len() != other.headers.len() {
            return false;
        }

        for iter in &self.headers {
            let (key, values) = iter.pair();
            match other.headers.get(key) {
                Some(other_values) => {
                    if values.len() != other_values.len()
                        || !values.iter().all(|v| other_values.contains(v))
                    {
                        return false;
                    }
                }
                None => return false,
            }
        }

        true
    }

    pub fn __contains__(&self, key: String) -> bool {
        self.contains(key)
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.headers)
    }

    pub fn __setitem__(&mut self, key: String, value: String) {
        self.set(key, value);
    }

    pub fn __getitem__(&self, key: String) -> Option<String> {
        self.get(key)
    }
}

impl Headers {
    pub fn remove(&mut self, key: &str) {
        self.headers.remove(&key.to_lowercase());
    }

    pub fn clear(&mut self) {
        self.headers.clear();
    }

    pub fn extend(&mut self, headers: &Headers) {
        for iter in headers.headers.iter() {
            let (key, values) = iter.pair();
            let mut entry = self.headers.entry(key.clone()).or_default();
            entry.extend(values.iter().cloned());
        }
    }

    /// Merge headers from `headers` into `self`, but only for keys not already present.
    /// This gives middleware-set headers precedence over global defaults,
    /// preventing duplicate `Access-Control-Allow-Origin` (and similar) violations.
    pub fn set_missing(&mut self, headers: &Headers) {
        for iter in headers.headers.iter() {
            let (key, values) = iter.pair();
            self.headers
                .entry(key.clone())
                .or_insert_with(|| values.clone());
        }
    }

    pub fn from_actix_headers(req_headers: &HeaderMap) -> Self {
        let headers = Headers::default();

        for (key, value) in req_headers {
            let key = key.to_string().to_lowercase();
            let value = match value.to_str() {
                Ok(value) => value.to_string(),
                Err(_) => continue,
            };
            headers.headers.entry(key).or_default().push(value);
        }

        headers
    }
}
