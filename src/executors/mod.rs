#[deny(clippy::if_same_then_else)]
pub mod web_socket_executors;

use std::sync::Arc;

use anyhow::Result;
use pyo3::prelude::*;
use pyo3::{BoundObject, IntoPyObject};
use pyo3_async_runtimes::TaskLocals;

use crate::asyncio::run_in_context_helper;
use crate::types::{
    function_info::FunctionInfo,
    request::Request,
    response::{Response, ResponseType, StreamingResponse},
    MiddlewareReturn,
};

#[inline]
fn get_function_output<'a, T>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    function_args: &T,
) -> Result<pyo3::Bound<'a, pyo3::PyAny>, PyErr>
where
    T: Clone + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    let handler = function.handler.bind(py).downcast()?;

    // 0-param handlers: skip Request→Python conversion entirely
    if function.number_of_params == 0 {
        return handler.call0();
    }

    let kwargs = function.kwargs.bind(py);
    let function_args: Py<PyAny> = function_args
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert args: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();

    match function.number_of_params {
        1 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                handler.call((), Some(kwargs))
            } else {
                handler.call1((function_args,))
            }
        }
        _ => handler.call((function_args,), Some(kwargs)),
    }
}

/// Invoke a sync handler with its arguments inside `ctx`.
///
/// This mirrors [`get_function_output`] but routes the call through
/// `ctx.run(...)` so that any `contextvars.ContextVar` writes the handler
/// performs land in the shared per-request context.
#[inline]
fn get_function_output_in_context<'a, T>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    ctx: &Bound<'a, PyAny>,
    function_args: &T,
) -> Result<pyo3::Bound<'a, pyo3::PyAny>, PyErr>
where
    T: Clone + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    let handler = function.handler.bind(py);

    if function.number_of_params == 0 {
        return ctx.call_method1("run", (handler,));
    }

    let kwargs = function.kwargs.bind(py);
    let function_args: Py<PyAny> = function_args
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert args: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();

    match function.number_of_params {
        1 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                ctx.call_method("run", (handler,), Some(kwargs))
            } else {
                ctx.call_method1("run", (handler, function_args))
            }
        }
        _ => ctx.call_method("run", (handler, function_args), Some(kwargs)),
    }
}

/// Wrap a user coroutine so that it runs as an `asyncio.Task` bound to `ctx`.
///
/// The returned awaitable, when scheduled via `into_future`, dispatches the
/// user coroutine via `loop.create_task(coro, context=ctx)`. Because `ctx`
/// is passed directly (not copied), `ContextVar` mutations inside the user
/// coroutine persist in `ctx` and are observable in subsequent phases that
/// reuse the same context.
#[inline]
fn wrap_coro_in_context<'a>(
    py: Python<'a>,
    ctx: &Bound<'a, PyAny>,
    coroutine: Bound<'a, PyAny>,
) -> PyResult<Bound<'a, PyAny>> {
    run_in_context_helper(py)?.call1((coroutine, ctx))
}

// Execute the middleware function
// type T can be either Request (before middleware) or Response (after middleware)
// Return type can either be a Request or a Response, we wrap it inside an enum for easier handling
#[inline]
pub async fn execute_middleware_function<T>(
    input: &T,
    function: &FunctionInfo,
    context: Option<&Py<PyAny>>,
) -> Result<MiddlewareReturn>
where
    T: Clone + for<'a, 'py> FromPyObject<'a, 'py> + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    if function.is_async {
        let output: Py<PyAny> = Python::with_gil(|py| -> PyResult<_> {
            let coroutine = get_function_output(function, py, input)?;
            let awaitable = match context {
                Some(ctx) => wrap_coro_in_context(py, ctx.bind(py), coroutine)?,
                None => coroutine,
            };
            pyo3_async_runtimes::tokio::into_future(awaitable)
        })?
        .await?;

        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            // Try response extraction first, then request
            match output.extract::<Response>(py) {
                Ok(response) => Ok(MiddlewareReturn::Response(response)),
                Err(_) => match output.extract::<Request>(py) {
                    Ok(request) => Ok(MiddlewareReturn::Request(request)),
                    Err(e) => Err(e.into()),
                },
            }
        })
    } else {
        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            let output = match context {
                Some(ctx) => get_function_output_in_context(function, py, ctx.bind(py), input)?,
                None => get_function_output(function, py, input)?,
            };

            match output.extract::<Response>() {
                Ok(response) => Ok(MiddlewareReturn::Response(response)),
                Err(_) => match output.extract::<Request>() {
                    Ok(request) => Ok(MiddlewareReturn::Request(request)),
                    Err(e) => Err(e.into()),
                },
            }
        })
    }
}

// Execute the after_request middleware function with both request and response
// This allows after_request callbacks to access the request object
#[inline]
fn get_function_output_with_two_args<'a, T, U>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    first_arg: &T,
    second_arg: &U,
) -> Result<pyo3::Bound<'a, pyo3::PyAny>, PyErr>
where
    T: Clone + for<'py> IntoPyObject<'py>,
    U: Clone + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
    for<'py> <U as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    let handler = function.handler.bind(py).downcast()?;

    if function.number_of_params == 0 {
        return handler.call0();
    }

    let kwargs = function.kwargs.bind(py);
    let first_arg: Py<PyAny> = first_arg
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert first arg: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();
    let second_arg: Py<PyAny> = second_arg
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert second arg: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();

    match function.number_of_params {
        1 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                handler.call((), Some(kwargs))
            } else {
                handler.call1((second_arg,))
            }
        }
        2 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                handler.call((first_arg, second_arg), Some(kwargs))
            } else {
                handler.call1((first_arg, second_arg))
            }
        }
        _ => handler.call((first_arg, second_arg), Some(kwargs)),
    }
}

/// Two-argument counterpart to [`get_function_output_in_context`] used by
/// `after_request` hooks, which receive both the request and the response.
#[inline]
fn get_function_output_with_two_args_in_context<'a, T, U>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    ctx: &Bound<'a, PyAny>,
    first_arg: &T,
    second_arg: &U,
) -> Result<pyo3::Bound<'a, pyo3::PyAny>, PyErr>
where
    T: Clone + for<'py> IntoPyObject<'py>,
    U: Clone + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
    for<'py> <U as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    let handler = function.handler.bind(py);

    if function.number_of_params == 0 {
        return ctx.call_method1("run", (handler,));
    }

    let kwargs = function.kwargs.bind(py);
    let first_arg: Py<PyAny> = first_arg
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert first arg: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();
    let second_arg: Py<PyAny> = second_arg
        .clone()
        .into_pyobject(py)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to convert second arg: {:?}",
                e
            ))
        })?
        .into_any()
        .unbind();

    match function.number_of_params {
        1 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                ctx.call_method("run", (handler,), Some(kwargs))
            } else {
                ctx.call_method1("run", (handler, second_arg))
            }
        }
        2 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            {
                ctx.call_method("run", (handler, first_arg, second_arg), Some(kwargs))
            } else {
                ctx.call_method1("run", (handler, first_arg, second_arg))
            }
        }
        _ => ctx.call_method("run", (handler, first_arg, second_arg), Some(kwargs)),
    }
}

// Execute the after_request middleware function with both request and response
#[inline]
pub async fn execute_after_middleware_function(
    request: &Request,
    response: &Response,
    function: &FunctionInfo,
    context: Option<&Py<PyAny>>,
) -> Result<MiddlewareReturn> {
    if function.is_async {
        let output: Py<PyAny> = Python::with_gil(|py| -> PyResult<_> {
            let coroutine = get_function_output_with_two_args(function, py, request, response)?;
            let awaitable = match context {
                Some(ctx) => wrap_coro_in_context(py, ctx.bind(py), coroutine)?,
                None => coroutine,
            };
            pyo3_async_runtimes::tokio::into_future(awaitable)
        })?
        .await?;

        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            // Try response extraction first, then request
            match output.extract::<Response>(py) {
                Ok(response) => Ok(MiddlewareReturn::Response(response)),
                Err(_) => match output.extract::<Request>(py) {
                    Ok(request) => Ok(MiddlewareReturn::Request(request)),
                    Err(e) => Err(e.into()),
                },
            }
        })
    } else {
        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            let output = match context {
                Some(ctx) => get_function_output_with_two_args_in_context(
                    function,
                    py,
                    ctx.bind(py),
                    request,
                    response,
                )?,
                None => get_function_output_with_two_args(function, py, request, response)?,
            };

            match output.extract::<Response>() {
                Ok(response) => Ok(MiddlewareReturn::Response(response)),
                Err(_) => match output.extract::<Request>() {
                    Ok(request) => Ok(MiddlewareReturn::Request(request)),
                    Err(e) => Err(e.into()),
                },
            }
        })
    }
}

#[inline]
pub async fn execute_http_function(
    request: &Request,
    function: &FunctionInfo,
    context: Option<&Py<PyAny>>,
) -> PyResult<ResponseType> {
    if function.is_async {
        let output = Python::with_gil(|py| -> PyResult<_> {
            let coroutine = get_function_output(function, py, request)?;
            let awaitable = match context {
                Some(ctx) => wrap_coro_in_context(py, ctx.bind(py), coroutine)?,
                None => coroutine,
            };
            pyo3_async_runtimes::tokio::into_future(awaitable)
        })?
        .await?;

        Python::with_gil(|py| extract_response_type(output, py))
    } else {
        Python::with_gil(|py| {
            let output = match context {
                Some(ctx) => get_function_output_in_context(function, py, ctx.bind(py), request)?,
                None => get_function_output(function, py, request)?,
            };
            extract_response_type_bound(output)
        })
    }
}

#[inline]
fn extract_response_type(output: Py<PyAny>, py: Python) -> PyResult<ResponseType> {
    // Try Response first (most common case), then StreamingResponse
    match output.extract::<Response>(py) {
        Ok(response) => Ok(ResponseType::Standard(response)),
        Err(_) => match output.extract::<StreamingResponse>(py) {
            Ok(streaming_response) => Ok(ResponseType::Streaming(streaming_response)),
            Err(_) => Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "Function must return a Response or StreamingResponse",
            )),
        },
    }
}

#[inline]
fn extract_response_type_bound(output: pyo3::Bound<'_, pyo3::PyAny>) -> PyResult<ResponseType> {
    match output.extract::<Response>() {
        Ok(response) => Ok(ResponseType::Standard(response)),
        Err(_) => match output.extract::<StreamingResponse>() {
            Ok(streaming_response) => Ok(ResponseType::Streaming(streaming_response)),
            Err(_) => Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "Function must return a Response or StreamingResponse",
            )),
        },
    }
}

pub async fn execute_startup_handler(
    event_handler: Option<Arc<FunctionInfo>>,
    task_locals: &TaskLocals,
) -> Result<()> {
    if let Some(function) = event_handler {
        if function.is_async {
            Python::with_gil(|py| {
                pyo3_async_runtimes::into_future_with_locals(
                    task_locals,
                    function.handler.bind(py).call0()?,
                )
            })?
            .await?;
        } else {
            Python::with_gil(|py| function.handler.call0(py))?;
        }
    }
    Ok(())
}
