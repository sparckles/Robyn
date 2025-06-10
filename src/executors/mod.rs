#[deny(clippy::if_same_then_else)]
/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
pub mod web_socket_executors;

use std::sync::Arc;

use anyhow::Result;
use log::debug;
use pyo3::prelude::*;
use pyo3::{BoundObject, IntoPyObject};
use pyo3_async_runtimes::TaskLocals;

use crate::types::{
    function_info::FunctionInfo, request::Request, response::Response, MiddlewareReturn,
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
    let kwargs = function.kwargs.bind(py);
    let function_args: PyObject = function_args
        .clone()
        .into_pyobject(py)
        .unwrap()
        .into_any()
        .unbind();
    debug!("Function args: {:?}", function_args);

    match function.number_of_params {
        0 => handler.call0(),
        1 => {
            if pyo3::types::PyDictMethods::get_item(kwargs, "global_dependencies")
                .is_ok_and(|it| !it.is_none())
                || pyo3::types::PyDictMethods::get_item(kwargs, "router_dependencies")
                    .is_ok_and(|it| !it.is_none())
            // these are reserved keywords
            {
                handler.call((), Some(kwargs))
            } else {
                handler.call1((function_args,))
            }
        }
        _ => handler.call((function_args,), Some(kwargs)),
    }
}

// Execute the middleware function
// type T can be either Request (before middleware) or Response (after middleware)
// Return type can either be a Request or a Response, we wrap it inside an enum for easier handling
#[inline]
pub async fn execute_middleware_function<T>(
    input: &T,
    function: &FunctionInfo,
) -> Result<MiddlewareReturn>
where
    T: Clone + for<'a> FromPyObject<'a> + for<'py> IntoPyObject<'py>,
    for<'py> <T as IntoPyObject<'py>>::Error: std::fmt::Debug,
{
    if function.is_async {
        let output: Py<PyAny> = Python::with_gil(|py| {
            pyo3_async_runtimes::tokio::into_future(get_function_output(function, py, input)?)
        })?
        .await?;

        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            let output_response = output.extract::<Response>(py);
            match output_response {
                Ok(o) => Ok(MiddlewareReturn::Response(o)),
                Err(_) => Ok(MiddlewareReturn::Request(output.extract::<Request>(py)?)),
            }
        })
    } else {
        Python::with_gil(|py| -> Result<MiddlewareReturn> {
            let output = get_function_output(function, py, input)?;
            debug!("Middleware output: {:?}", output);
            match output.extract::<Response>() {
                Ok(o) => Ok(MiddlewareReturn::Response(o)),
                Err(_) => Ok(MiddlewareReturn::Request(output.extract::<Request>()?)),
            }
        })
    }
}

#[inline]
pub async fn execute_http_function(
    request: &Request,
    function: &FunctionInfo,
) -> PyResult<Response> {
    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(function, py, request)?;
            pyo3_async_runtimes::tokio::into_future(function_output)
        })?
        .await?;

        return Python::with_gil(|py| -> PyResult<Response> { output.extract(py) });
    };

    Python::with_gil(|py| -> PyResult<Response> {
        get_function_output(function, py, request)?.extract()
    })
}

pub async fn execute_startup_handler(
    event_handler: Option<Arc<FunctionInfo>>,
    task_locals: &TaskLocals,
) -> Result<()> {
    if let Some(function) = event_handler {
        if function.is_async {
            debug!("Startup event handler async");
            Python::with_gil(|py| {
                pyo3_async_runtimes::into_future_with_locals(
                    task_locals,
                    function.handler.bind(py).call0()?,
                )
            })?
            .await?;
        } else {
            debug!("Startup event handler");
            Python::with_gil(|py| function.handler.call0(py))?;
        }
    }
    Ok(())
}
