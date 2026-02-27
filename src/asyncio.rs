use pyo3::{prelude::*, sync::PyOnceLock};
use std::convert::Into;

static CONTEXTVARS: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static CONTEXT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

fn contextvars(py: Python<'_>) -> PyResult<&Bound<'_, PyAny>> {
    Ok(CONTEXTVARS
        .get_or_try_init(py, || py.import("contextvars").map(Into::into))?
        .bind(py))
}

#[allow(dead_code)]
pub(crate) fn empty_context(py: Python<'_>) -> PyResult<&Bound<'_, PyAny>> {
    Ok(CONTEXT
        .get_or_try_init(py, || {
            contextvars(py)?
                .getattr("Context")?
                .call0()
                .map(std::convert::Into::into)
        })?
        .bind(py))
}

#[inline(always)]
pub(crate) fn copy_context(py: Python) -> Py<PyAny> {
    // Use the fast FFI path for CPython
    // Note: PyPy support would require a different implementation, but robyn targets CPython
    let ctx = unsafe {
        let ptr = pyo3::ffi::PyContext_CopyCurrent();
        Bound::from_owned_ptr(py, ptr)
    };
    ctx.unbind()
}

