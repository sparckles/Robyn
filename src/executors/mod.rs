#[deny(clippy::if_same_then_else)]
/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
pub mod web_socket_executors;

use std::sync::Arc;

use anyhow::Result;
use log::debug;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;

use crate::types::{
    function_info::FunctionInfo, request::Request, response::Response, MiddlewareReturn,
};

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
    // kwargs are handled
    let kwargs = function.kwargs.as_ref(py);

    let function_args = function_args.to_object(py);

    match function.number_of_params {
        0 => handler.call0(),
        1 => {
            if function.args.as_ref(py).get_item("request").is_some()
                || function.args.as_ref(py).get_item("response").is_some()
            {
                // If 'request' is present, call handler with 'function_args'
                handler.call1((function_args,))
            } else {
                // If neither 'request' nor 'response' is present
                handler.call((), Some(kwargs))
            }
        }
        2 => {
            if function.args.as_ref(py).get_item("request").is_some()
                || function.args.as_ref(py).get_item("response").is_some()
            {
                // If either 'request' or 'response' is present, call handler with 'function_args' and 'kwargs'
                handler.call((function_args,), Some(kwargs))
            } else {
                // If neither 'request' nor 'response' is present
                handler.call((), Some(kwargs))
            }
        }
        3..=u8::MAX => handler.call((function_args,), Some(kwargs)),
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

pub async fn execute_event_handler(
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
