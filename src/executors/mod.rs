#[deny(clippy::if_same_then_else)]
/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
pub mod web_socket_executors;

use crate::types::{
    function_info::FunctionInfo, request::Request, response::Response, MiddlewareReturn,
};

use anyhow::Result;
use log::debug;
use pyo3::prelude::*;
use pyo3::types::PyTuple;
use pyo3_asyncio::TaskLocals;
use std::sync::Arc;

#[inline]
fn get_function_output<'a, T>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    function_args: &T,
) -> Result<&'a PyAny, PyErr>
where
    T: ToPyObject,
{
    let handler = function.handler.as_ref(py);
    let kwargs = function.kwargs.as_ref(py);
    let function_args = function_args.to_object(py);
    debug!("Function args: {:?}", function_args);

    match function.number_of_params {
        0 => handler.call0(),
        1 => {
            if kwargs.get_item("global_dependencies")?.is_some()
                || kwargs.get_item("router_dependencies")?.is_some()
            // these are reserved keywords
            {
                handler.call((), Some(kwargs))
            } else {
                handler.call1((function_args,))
            }
        }
        _ => {
            if let Ok(tuple) = function_args.downcast::<PyTuple>(py) {
                handler.call(tuple, Some(kwargs))
            } else {
                handler.call((function_args,), Some(kwargs))
            }
        }
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
    T: for<'a> FromPyObject<'a> + ToPyObject,
{
    if function.is_async {
        let output: Py<PyAny> = Python::with_gil(|py| {
            pyo3_asyncio::tokio::into_future(get_function_output(function, py, input)?)
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
// Execute middleware function after receiving a response
//
// This function handles post-request middleware logic that can receive both
// the response and the original request as parameters.
// T represents the response type, R represents the request type.
//
// The function determines whether to pass just the response or both response and request
// to the middleware function based on the number of parameters it accepts.
pub async fn execute_middleware_after_request<T, T2>(
    response: &T,
    request: &T2,
    function: &FunctionInfo,
) -> Result<MiddlewareReturn>
where
    T: for<'a> FromPyObject<'a> + ToPyObject,
    T2: for<'a> FromPyObject<'a> + ToPyObject,
{
    if function.is_async {
        let output: Py<PyAny> = Python::with_gil(|py| {
            let result = if function.number_of_params == 2 {
                pyo3_asyncio::tokio::into_future(get_function_output(
                    function,
                    py,
                    &(response, request),
                )?)
            } else {
                pyo3_asyncio::tokio::into_future(get_function_output(function, py, response)?)
            };
            result
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
            let output = if function.number_of_params == 2 {
                get_function_output(function, py, &(response, request))?
            } else {
                get_function_output(function, py, response)?
            };
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
            pyo3_asyncio::tokio::into_future(function_output)
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
                pyo3_asyncio::into_future_with_locals(
                    task_locals,
                    function.handler.as_ref(py).call0()?,
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
