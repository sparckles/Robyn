/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
use crate::types::{FunctionInfo, Request, Response};

use std::collections::HashMap;
use std::sync::Arc;

use anyhow::{Context, Result};
use log::debug;
use pyo3_asyncio::TaskLocals;
// pyO3 module
use pyo3::prelude::*;

fn get_function_output<'a>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    request: &mut Request,
    response: &mut Response,
) -> Result<&'a PyAny, PyErr> {
    let handler = function.handler.as_ref(py);
    let request_hashmap = request.to_hashmap(py).unwrap();
    let response_hashmap = response.to_hashmap(py).unwrap();

    // this returns a response of function execute in case of http functions
    // and the request,response tuple in case of middleware functions
    match function.number_of_params {
        0 => handler.call0(),
        1 => handler.call1((request_hashmap,)),
        // this is done to accommodate any future params
        2_u8..=u8::MAX => handler.call1((request_hashmap, response_hashmap)),
    }
}

pub async fn execute_middleware_function<'a>(
    request: &mut Request,
    response: &mut Response,
    function: FunctionInfo,
) -> Result<(HashMap<String, Py<PyAny>>, HashMap<String, Py<PyAny>>)> {
    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(&function, py, request, response);
            pyo3_asyncio::tokio::into_future(function_output?)
        })?
        .await?;

        let output = Python::with_gil(
            |py| -> PyResult<(HashMap<String, Py<PyAny>>, HashMap<String, Py<PyAny>>)> {
                let (request, response): (HashMap<String, Py<PyAny>>, HashMap<String, Py<PyAny>>) =
                    output.extract(py)?;
                Ok((request, response))
            },
        )
        .context("Failed to execute handler function");

        output
    } else {
        Python::with_gil(|py| get_function_output(&function, py, request, response)?.extract())
            .context("Failed to execute handler function")
    }
}

#[inline]
pub async fn execute_http_function(
    request: &mut Request,
    response: &mut Response,
    function: FunctionInfo,
) -> Result<Response> {
    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(&function, py, request, response);
            pyo3_asyncio::tokio::into_future(function_output?)
        })?
        .await?;

        Python::with_gil(|py| -> Result<Response> {
            output.extract(py).context("Failed to get route response")
        })
    } else {
        Python::with_gil(|py| -> Result<Response> {
            let output = get_function_output(&function, py, request, response)?;
            output.extract().context("Failed to get route response")
        })
    }
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
