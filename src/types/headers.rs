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

                    let new_value = value.downcast::<PyList>();

                    if new_value.is_err() {
                        let value = value.to_string();
                        headers.entry(key).or_insert_with(Vec::new).push(value);
                    } else {
                        let value: Vec<String> =
                            new_value.unwrap().iter().map(|x| x.to_string()).collect();
                        headers.entry(key).or_insert_with(Vec::new).extend(value);
                    }
                }
                Headers { headers }
            }
            None => Headers {
                headers: HashMap::new(),
            },
        }
    }

    pub fn set(&mut self, key: String, value: String) {
        self.headers
            .entry(key.to_lowercase())
            .or_insert_with(Vec::new)
            .push(value.to_lowercase());
    }

    pub fn get(&self, py: Python, key: String) -> Py<PyList> {
        match self.headers.get(&key.to_lowercase()) {
            Some(values) => {
                let py_values = PyList::new(py, values.iter().map(|value| value.to_object(py)));
                py_values.into()
            }
            None => PyList::empty(py).into(),
        }
    }

    /// Returns all headers as a PyList of tuples.
    pub fn get_headers(&self, py: Python) -> Py<PyList> {
        let headers_list = PyList::new(
            py,
            self.headers.iter().map(|(key, values)| {
                let py_values = PyList::new(py, values);
                (key.clone(), py_values.to_object(py))
            }),
        );
        headers_list.into()
    }

    pub fn populate_from_dict(&mut self, headers: &PyDict) {
        for (key, value) in headers {
            let key = key.to_string().to_lowercase();
            let value: Vec<String> = value
                .downcast::<PyList>()
                .unwrap()
                .iter()
                .map(|x| x.to_string())
                .collect();
            self.headers.insert(key, value);
        }
    }

    pub fn is_empty(&self) -> bool {
        self.headers.is_empty()
    }
}
