use log::debug;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

// Custom Multimap class
#[pyclass(name = "QueryParams")]
#[derive(Clone, Debug, Default)]
pub struct QueryParams {
    pub queries: HashMap<String, Vec<String>>,
}

#[pymethods]
impl QueryParams {
    #[new]
    pub fn new() -> Self {
        QueryParams {
            queries: HashMap::new(),
        }
    }

    pub fn set(&mut self, key: String, value: String) {
        debug!("Setting key: {} to value: {}", key, value);
        self.queries.entry(key).or_default().push(value);
        debug!("Multimap: {:?}", self.queries);
    }

    pub fn get(&self, key: String, default: Option<String>) -> Option<String> {
        match self.queries.get(&key) {
            Some(values) => values.last().cloned(),
            None => default,
        }
    }

    pub fn get_first(&self, key: String) -> Option<String> {
        match self.queries.get(&key) {
            Some(values) => values.first().cloned(),
            None => None,
        }
    }

    pub fn empty(&self) -> bool {
        self.queries.is_empty()
    }

    pub fn contains(&self, key: String) -> bool {
        self.queries.contains_key(&key)
    }

    pub fn get_all(&self, key: String) -> Option<Vec<String>> {
        self.queries.get(&key).cloned()
    }

    pub fn extend(&mut self, other: &mut Self) {
        for (key, values) in other.queries.iter_mut() {
            for value in values.iter_mut() {
                self.set(key.clone(), value.clone());
            }
        }
    }

    pub fn to_dict(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (key, values) in self.queries.iter() {
            let values = PyList::new(py, values.iter());
            dict.set_item(key, values)?;
        }
        Ok(dict.into())
    }

    pub fn __contains__(&self, key: String) -> bool {
        self.queries.contains_key(&key)
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.queries)
    }
}

impl QueryParams {
    pub fn from_hashmap(map: HashMap<String, Vec<String>>) -> Self {
        let mut multimap = QueryParams::new();
        for (key, values) in map {
            for value in values {
                multimap.set(key.clone(), value);
            }
        }
        multimap
    }

    pub fn from_py_dict(dict: &PyDict) -> Self {
        let mut multimap = QueryParams::new();
        for (key, value) in dict.iter() {
            let key = key.extract::<String>().unwrap();
            let value = value.extract::<String>().unwrap();
            multimap.set(key, value);
        }
        multimap
    }

    pub fn contains_key(&self, key: &str) -> bool {
        self.queries.contains_key(key)
    }

    pub fn insert(&mut self, key: String, value: Vec<String>) {
        self.queries.insert(key, value);
    }

    pub fn get_mut(&mut self, key: &str) -> Option<&Vec<String>> {
        self.queries.get(key)
    }
}
