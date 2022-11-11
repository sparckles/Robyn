use dashmap::DashMap;
use pyo3::prelude::{Py, PyAny};

#[derive(Debug, Clone)]
pub enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
    SyncGenerator(Py<PyAny>),
}

impl PyFunction {
    pub fn from_str(input: &str, handler: Py<PyAny>) -> PyFunction {
        match input.to_lowercase().as_str() {
            "async_function" => PyFunction::CoRoutine(handler),
            "sync_function" => PyFunction::SyncFunction(handler),
            "sync_generator" => PyFunction::SyncGenerator(handler),
            _ => panic!("Unknown function type {:?}", input),
        }
    }
}

pub type Headers = DashMap<String, String>;
