use actix_http::header::HeaderMap;
use dashmap::DashMap;
use log::debug;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

// Custom Multimap class
#[pyclass(name = "Headers")]
#[derive(Clone, Debug, Default)]
pub struct Headers {
    pub headers: DashMap<String, Vec<String>>,
}

#[pymethods]
impl Headers {
    #[new]
    pub fn new(default_headers: Option<&PyDict>) -> Self {
        match default_headers {
            Some(default_headers) => {
                let headers = DashMap::new();
                for (key, value) in default_headers {
                    let key = key.to_string().to_lowercase();

                    let new_value = value.downcast::<PyList>();

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
        debug!("Setting header {} to {}", key, value);
        self.headers.insert(key.to_lowercase(), vec![value]);
    }

    pub fn append(&mut self, key: String, value: String) {
        debug!("Setting header {} to {}", key, value);
        self.headers
            .entry(key.to_lowercase())
            .or_default()
            .push(value);
    }

    pub fn get_all(&self, py: Python, key: String) -> Py<PyList> {
        match self.headers.get(&key.to_lowercase()) {
            Some(values) => {
                let py_values = PyList::new(py, values.iter().map(|value| value.to_object(py)));
                py_values.into()
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
            let py_values = PyList::new(py, values.iter().map(|value| value.to_object(py)));
            dict.set_item(key, py_values).unwrap();
        }
        dict.into()
    }

    pub fn contains(&self, key: String) -> bool {
        debug!("Checking if header {} exists", key);
        debug!("Headers: {:?}", self.headers);
        self.headers.contains_key(&key.to_lowercase())
    }

    pub fn populate_from_dict(&mut self, headers: &PyDict) {
        for (key, value) in headers {
            let key = key.to_string().to_lowercase();
            let new_value = value.downcast::<PyList>();

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

    pub fn extend(&mut self, headers: &Headers) {
        for iter in headers.headers.iter() {
            let (key, values) = iter.pair();
            let mut entry = self.headers.entry(key.clone()).or_default();
            entry.extend(values.clone());
        }
    }

    pub fn from_actix_headers(req_headers: &HeaderMap) -> Self {
        let headers = Headers::default();

        for (key, value) in req_headers {
            let key = key.to_string().to_lowercase();
            let value = value.to_str().unwrap().to_string();
            headers.headers.entry(key).or_default().push(value);
        }

        headers
    }
}
