use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};

use pyo3::{prelude::*, types::PyDict};

#[pyclass]
#[derive(Debug, PartialEq, Eq, Hash)]
pub enum MiddlewareType {
    #[pyo3(name = "BEFORE_REQUEST")]
    BeforeRequest = 0,
    #[pyo3(name = "AFTER_REQUEST")]
    AfterRequest = 1,
}

#[pymethods]
impl MiddlewareType {
    // This is needed because pyo3 doesn't support hashing enums from Python
    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
    }
}

#[pyclass]
#[derive(Debug, PartialEq, Eq, Hash, Clone)]
pub enum FunctionType {
    #[pyo3(name = "SYNC")]
    Sync = 0,
    #[pyo3(name = "ASYNC")]
    Async = 1,
    #[pyo3(name = "SYNCGENERATOR")]
    SyncGenerator = 2,
    #[pyo3(name = "ASYNCGENERATOR")]
    AsyncGenerator = 3,
}

#[pymethods]
impl FunctionType {
    // This is needed because pyo3 doesn't support hashing enums from Python
    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    #[pyo3(get, set)]
    pub handler: Py<PyAny>,
    #[pyo3(get, set)]
    pub ftype: FunctionType,
    #[pyo3(get, set)]
    pub number_of_params: u8,
    #[pyo3(get, set)]
    pub args: Py<PyDict>,
    #[pyo3(get, set)]
    pub kwargs: Py<PyDict>,
    // /// currently for use with generators that need to persist state beyond the initial call
    // #[pyo3(get,set)]
    // pub state: Option<Py<PyAny>>
}

#[pymethods]
impl FunctionInfo {
    #[new]
    pub fn new(
        handler: Py<PyAny>,
        ftype: FunctionType,
        number_of_params: u8,
        args: Py<PyDict>,
        kwargs: Py<PyDict>,
    ) -> Self {
        Self {
            handler,
            ftype,
            number_of_params,
            args,
            kwargs,
        }
    }
}
