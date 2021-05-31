use futures::future::BoxFuture;
use pyo3::prelude::*;
use std::future::Future;

pub type Job = Box<dyn FnOnce() + Send + 'static>;
pub type AsyncFunction = Box<&PyAny>
// Box<dyn Result<<dyn Future<Output = PyResult<PyObject>> + Send + 'static>>, PyErr>;
// pub type PyFuture = Box<dyn Future<Output = PyResult<PyObject>> + Send + 'static>;
pub type PyFuture<'a> = BoxFuture<'a, PyResult<PyObject>>;

