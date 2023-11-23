use log::debug;
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
        debug!("Setting key: {} to value: {}", key, value);
        self.inner.entry(key).or_insert_with(Vec::new).push(value);
        debug!("Multimap: {:?}", self.inner);
    }

    pub fn get(&self, key: String) -> Option<String> {
        match self.inner.get(&key) {
            Some(values) => values.last().cloned(),
            None => None,
        }
    }

    pub fn empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn contains(&self, key: String) -> bool {
        self.inner.contains_key(&key)
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

    pub fn __contains__(&self, key: String) -> bool {
        self.inner.contains_key(&key)
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

    pub fn from_dict(dict: &PyDict) -> Self {
        let mut multimap = MultiMap::new();
        for (key, value) in dict.iter() {
            let key = key.extract::<String>().unwrap();
            let value = value.extract::<String>().unwrap();
            multimap.set(key, value);
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
