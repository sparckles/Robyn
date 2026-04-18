// Derived from Granian (https://github.com/emmett-framework/granian)
// Copyright 2021 Giovanni Barillari
// Licensed under the BSD 3-Clause License
// See: https://github.com/emmett-framework/granian/blob/master/LICENSE

use pyo3::{prelude::*, sync::PyOnceLock};
use std::convert::Into;
use std::ffi::CString;

static CONTEXTVARS: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static CONTEXT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static RUN_IN_CONTEXT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

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
pub(crate) fn copy_context(py: Python) -> PyResult<Py<PyAny>> {
    unsafe {
        let ptr = pyo3::ffi::PyContext_CopyCurrent();
        Ok(Bound::from_owned_ptr_or_err(py, ptr)?.unbind())
    }
}

/// Create a fresh `contextvars.Context()` object.
///
/// Used by the HTTP server to allocate one shared context per request so that
/// `contextvars.ContextVar` writes inside `before_request`, the route handler,
/// and `after_request` all land in the same context object and are visible
/// across middleware phases.
#[inline(always)]
pub(crate) fn new_context(py: Python) -> PyResult<Py<PyAny>> {
    Ok(contextvars(py)?.getattr("Context")?.call0()?.unbind())
}

/// Python coroutine function `_run_in_context(coro, ctx)` that schedules
/// `coro` as an `asyncio.Task` with `context=ctx` and awaits it.
///
/// Passing the context directly to `create_task` tells asyncio to use the
/// given `Context` object without copying it, so any `ContextVar` writes
/// performed inside `coro` persist in `ctx` and are visible to later phases
/// that reuse the same `ctx`.
///
/// The `context=` keyword on `loop.create_task` is Python 3.11+. On 3.10 the
/// helper falls back to plain `await coro` (current thread-local context),
/// preserving pre-fix behavior — writes made in `before_request` are not
/// visible to later phases on 3.10.
pub(crate) fn run_in_context_helper<'py>(py: Python<'py>) -> PyResult<&'py Bound<'py, PyAny>> {
    const SOURCE: &str = "import asyncio\n\
                          import sys\n\
                          if sys.version_info >= (3, 11):\n    \
                              async def _run_in_context(coro, ctx):\n        \
                                  task = asyncio.get_running_loop().create_task(coro, context=ctx)\n        \
                                  return await task\n\
                          else:\n    \
                              async def _run_in_context(coro, ctx):\n        \
                                  return await coro\n";

    Ok(RUN_IN_CONTEXT
        .get_or_try_init(py, || -> PyResult<Py<PyAny>> {
            let module = PyModule::from_code(
                py,
                &CString::new(SOURCE).unwrap(),
                &CString::new("robyn_ctx_runner.py").unwrap(),
                &CString::new("_robyn_ctx_runner").unwrap(),
            )?;
            Ok(module.getattr("_run_in_context")?.unbind())
        })?
        .bind(py))
}
