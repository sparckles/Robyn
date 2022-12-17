/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
use crate::io_helpers::read_file;
use crate::types::{FunctionInfo, Request, Response};

use std::collections::HashMap;
use std::sync::Arc;

use anyhow::{Context, Result};
use log::debug;
use pyo3::types::PyDict;
use pyo3_asyncio::TaskLocals;
// pyO3 module
use pyo3::prelude::*;

fn get_function_output<'a>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    request: &Request,
) -> Result<&'a PyAny, PyErr> {
    let handler = function.handler.as_ref(py);
    let request_hashmap = request.to_hashmap(py).unwrap();

    // this makes the request object accessible across every route
    match function.number_of_params {
        0 => handler.call0(),
        1 => handler.call1((request_hashmap,)),
        // this is done to accommodate any future params
        2_u8..=u8::MAX => handler.call1((request_hashmap,)),
    }
}

pub async fn execute_middleware_function<'a>(
    request: &Request,
    function: FunctionInfo,
) -> Result<HashMap<String, HashMap<String, String>>> {
    // TODO:
    // add body in middlewares too

    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(&function, py, request);
            pyo3_asyncio::tokio::into_future(function_output?)
        })?
        .await?;

        Python::with_gil(|py| -> PyResult<HashMap<String, HashMap<String, String>>> {
            let output: Vec<HashMap<String, HashMap<String, String>>> = output.extract(py)?;
            let responses = output[0].clone();
            Ok(responses)
        })
        .context("Failed to execute handler function")
    } else {
        Python::with_gil(|py| get_function_output(&function, py, request)?.extract())
            .context("Failed to execute handler function")
    }
}

#[inline]
pub async fn execute_http_function(request: &Request, function: FunctionInfo) -> Result<Response> {
    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(&function, py, request);
            pyo3_asyncio::tokio::into_future(function_output?)
        })?
        .await?;

        // convert the output to a PyDict
        let res = Python::with_gil(|py| -> Result<Response> {
            let output: Py<PyDict> = output.extract(py)?;

            let output_type = output.as_ref(py).get_item("type");

            if let Some(output_type) = output_type {
                let output_type: String = output_type.extract()?;

                if output_type == "static_file" {
                    let file_path: String =
                        output.as_ref(py).get_item("file_path").unwrap().extract()?;
                    let contents = read_file(&file_path).unwrap();
                    output.as_ref(py).set_item("body", contents)?;
                }
            };

            let status_code = output.as_ref(py).get_item("status_code").unwrap();
            let status_code: u16 = status_code.extract().unwrap();

            let body = output.as_ref(py).get_item("body").unwrap();
            let body: String = body.extract().unwrap();

            let headers = output.as_ref(py).get_item("headers");

            let not_none_headers = if headers.is_some() {
                let some_headers: HashMap<String, String> = headers
                    .unwrap()
                    .extract::<HashMap<String, String>>()
                    .unwrap();
                some_headers
            } else {
                HashMap::new()
            };

            Ok(Response::new(status_code, not_none_headers, body))
        })?;

        debug!("This is the result of the code {:?}", output);
        Ok(res)
    } else {
        let res = Python::with_gil(|py| {
            let py_obj = get_function_output(&function, py, request).unwrap();
            Response::from_obj(py, py_obj)
        })
        .unwrap();

        Ok(res)
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
