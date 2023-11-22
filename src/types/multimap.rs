use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyDict};
use std::collections::HashMap;

#[derive(Debug, Clone, Default, PartialEq, Eq)]
#[pyclass]
pub struct MultiMap {
    map: HashMap<String, Vec<String>>,
}

#[pymethods]
impl MultiMap {}

impl MultiMap {
    fn new() -> Self {
        MultiMap {
            map: HashMap::new(),
        }
    }

    pub fn from_hashmap(map: HashMap<String, Vec<String>>) -> Self {
        MultiMap { map }
    }

    pub fn insert(&mut self, key: &str, value: &str) {
        self.map
            .entry(key.to_string())
            .or_default()
            .push(value.to_string());
    }

    fn get(&self, key: &str) -> Option<&Vec<String>> {
        self.map.get(key)
    }

    fn get_mut(&mut self, key: &str) -> Option<&mut Vec<String>> {
        self.map.get_mut(key)
    }

    fn remove(&mut self, key: &str) -> Option<Vec<String>> {
        self.map.remove(key)
    }

    fn contains_key(&self, key: &str) -> bool {
        self.map.contains_key(key)
    }

    fn len(&self) -> usize {
        self.map.len()
    }

    fn is_empty(&self) -> bool {
        self.map.is_empty()
    }

    pub fn get_map(&self) -> &HashMap<String, Vec<String>> {
        &self.map
    }

    pub fn to_pydict(self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);

        for (key, value) in self.map.iter() {
            let py_key = key.to_string().into_py(py);
            // convert py_value as a list
            let py_value = value
                .clone()
                .into_iter()
                .map(|v| v.into_py(py))
                .collect::<Vec<_>>()
                .into_py(py);

            dict.set_item(py_key, py_value)?;
        }

        Ok(dict.into_py(py))
    }
}
