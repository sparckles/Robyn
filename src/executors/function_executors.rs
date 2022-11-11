use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator};
use std::collections::HashMap;

pub fn execute_sync_generator<'a>(
    py: Python<'a>,
    function: Py<PyAny>,
    request: Option<HashMap<&'a str, Py<PyAny>>>,
) -> PyResult<&'a PyAny> {
    let response_contents: &PyDict = if let Some(request) = request {
        function
            .call1(py, (request,))?
            .into_ref(py)
            .downcast::<PyDict>()?
    } else {
        function.call0(py)?.into_ref(py).downcast::<PyDict>()?
    };

    let generator = response_contents
        .get_item("body")
        .unwrap()
        .downcast::<PyIterator>()?;

    let output = generator.last().unwrap();

    output
}
