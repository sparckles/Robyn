use dashmap::DashMap;
use pyo3::prelude::*;

// Replace PyFunction with a decorator
#[derive(Debug, Clone)]
pub enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
}

pub type Headers = DashMap<String, String>;
