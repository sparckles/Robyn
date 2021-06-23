use pyo3::prelude::*;

#[derive(Debug, Clone)]
pub enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
}
