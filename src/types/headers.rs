use log::debug;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

// Custom Multimap class
#[pyclass(name = "Headers")]
#[derive(Clone, Debug, Default)]
pub struct Headers {
    pub headers: HashMap<String, Vec<String>>,
}

#[pymethods]
impl Headers {
    #[new]
    pub fn new(default_headers: Option<&PyDict>) -> Self {
        match default_headers {
            Some(default_headers) => {
                let mut headers = HashMap::new();
                for (key, value) in default_headers {
                    let key = key.to_string();
                    let value: Vec<String> = value
                        .downcast::<PyList>()
                        .unwrap()
                        .iter()
                        .map(|x| x.to_string())
                        .collect();
                    headers.insert(key, value);
                }
                Headers { headers }
            }
            None => Headers {
                headers: HashMap::new(),
            },
        }
    }

    pub fn set_header(&mut self, key: String, value: String) {
        self.headers
            .entry(key)
            .or_insert_with(Vec::new)
            .push(value.to_lowercase());
    }
}
