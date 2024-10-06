use std::collections::HashMap;

use pyo3::{pyclass, pymethods};

#[pyclass]
#[derive(Debug, Clone)]
pub struct Identity {
    #[pyo3(get, set)]
    claims: HashMap<String, String>,
}

#[pymethods]
impl Identity {
    #[new]
    pub fn new(claims: HashMap<String, String>) -> Self {
        Self { claims }
    }
}
