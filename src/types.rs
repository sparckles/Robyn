use dashmap::DashMap;
use pyo3::prelude::*;

#[derive(Debug, Clone)]
pub enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
}

pub type RustAsync = Box<dyn FnOnce() + Send + 'static>;

pub type Headers = DashMap<String, String>;
