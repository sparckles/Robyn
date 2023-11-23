use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyDict, PyList};
use std::collections::HashMap;

// Custom Multimap class
#[pyclass(name = "MultiMap")]
#[derive(Clone, Debug, Default)]
pub struct MultiMap {
    pub inner: HashMap<String, Vec<String>>,
}

#[pymethods]
impl MultiMap {
    #[new]
    pub fn new() -> Self {
        MultiMap {
            inner: HashMap::new(),
        }
    }

    pub fn set(&mut self, key: String, value: String) {
        self.inner.entry(key).or_insert_with(Vec::new).push(value);
    }

    pub fn get(&self, py: Python, key: String) -> PyObject {
        match self.inner.get(&key) {
            Some(values) => {
                let py_list = PyList::empty(py);
                for value in values {
                    py_list.append(value).unwrap();
                }
                py_list.into()
            }
            None => py.None(),
        }
    }

    pub fn empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn contains(&self, key: String) -> bool {
        self.inner.contains_key(&key)
    }

    pub fn get_one(&self, key: String) -> Option<String> {
        match self.inner.get(&key) {
            Some(values) => values.first().cloned(),
            None => None,
        }
    }

    pub fn get_all(&self, key: String) -> Option<Vec<String>> {
        self.inner.get(&key).cloned()
    }

    pub fn extend(&mut self, other: &mut Self) {
        for (key, values) in other.inner.iter_mut() {
            for value in values.iter_mut() {
                self.set(key.clone(), value.clone());
            }
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    // Add other methods as needed
}

impl MultiMap {
    pub fn from_hashmap(map: HashMap<String, Vec<String>>) -> Self {
        let mut multimap = MultiMap::new();
        for (key, values) in map {
            for value in values {
                multimap.set(key.clone(), value);
            }
        }
        multimap
    }

    pub fn contains_key(&self, key: &str) -> bool {
        self.inner.contains_key(key)
    }

    pub fn insert(&mut self, key: String, value: Vec<String>) {
        self.inner.insert(key, value);
    }

    pub fn get_mut(&mut self, key: &str) -> Option<&Vec<String>> {
        self.inner.get(key)
    }
}

pub type Headers = MultiMap;

pub type Queries = MultiMap;
