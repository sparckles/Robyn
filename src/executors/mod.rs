/// This is the module that has all the executor functions
/// i.e. the functions that have the responsibility of parsing and executing functions.
use crate::io_helpers::read_file;

use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::Rc;
use std::sync::Arc;

use actix_web::HttpResponse;
use anyhow::Result;
use log::debug;

use pyo3_asyncio::TaskLocals;
// pyO3 module
use crate::types::PyFunction;

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// @TODO make configurable

pub async fn execute_middleware_function<'a>(
    function: PyFunction,
    payload: &mut [u8],
    headers: &HashMap<String, String>,
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
    number_of_params: u8,
    res: Option<&HttpResponse>,
) -> Result<HashMap<String, HashMap<String, String>>> {
    // TODO:
    // add body in middlewares too

    let data = payload.to_owned();
    let temp_response = &HttpResponse::Ok().finish();

    // make response object accessible while creating routes
    let response = match res {
        Some(res) => res,
        // do nothing if none
        None => temp_response,
    };
    debug!("response: {:?}", response);
    debug!("temp_response: {:?}", temp_response);
    let mut response_headers = HashMap::new();
    for (key, val) in response.headers() {
        response_headers.insert(key.to_string(), val.to_str().unwrap().to_string());
    }
    let mut response_dict: HashMap<&str, Py<PyAny>> = HashMap::new();
    let response_status_code = response.status().as_u16();
    let response_body = data.clone();

    // request object accessible while creating routes
    let mut request = HashMap::new();

    let mut queries_clone: HashMap<String, String> = HashMap::new();

    for (key, value) in (*queries).borrow().clone() {
        queries_clone.insert(key, value);
    }

    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("queries", queries_clone.into_py(py));
                // is this a bottleneck again?
                request.insert("headers", headers.clone().into_py(py));
                request.insert("body", data.into_py(py));
                response_dict.insert("headers", response_headers.into_py(py));
                response_dict.insert("status", response_status_code.into_py(py));
                response_dict.insert("body", response_body.into_py(py));
                debug!("response_dict: {:?}", response_dict);
                debug!("res: {:?}", res);
                // this makes the request object to be accessible across every route
                let coro: PyResult<&PyAny> = match number_of_params {
                    0 => handler.call0(),
                    1 => handler.call1((response_dict,)),
                    2 => handler.call1((request, response_dict)),
                    // this is done to accomodate any future params
                    3_u8..=u8::MAX => handler.call1((request, response_dict)),
                };
                pyo3_asyncio::tokio::into_future(coro?)
            })?;

            let output = output.await?;

            let res =
                Python::with_gil(|py| -> PyResult<HashMap<String, HashMap<String, String>>> {
                    let output: Vec<HashMap<String, HashMap<String, String>>> =
                        output.extract(py)?;
                    let responses = output[0].clone();
                    Ok(responses)
                })?;
            debug!("res at 97 : {:?}", res);
            Ok(res)
        }

        PyFunction::SyncFunction(handler) => {
            // do we even need this?
            // How else can we return a future from this?
            // let's wrap the output in a future?
            let output: Result<HashMap<String, HashMap<String, String>>> = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("queries", queries_clone.into_py(py));
                // is this a bottleneck again?
                request.insert("headers", headers.clone().into_py(py));
                request.insert("body", data.into_py(py));
                response_dict.insert("headers", response_headers.into_py(py));
                response_dict.insert("status", response_status_code.into_py(py));
                response_dict.insert("body", response_body.into_py(py));

                let output: PyResult<&PyAny> = match number_of_params {
                    0 => handler.call0(),
                    1 => handler.call1((request,)),
                    2 => handler.call1((request, response_dict)),
                    // this is done to accomodate any future params
                    3_u8..=u8::MAX => handler.call1((request, response_dict)),
                };

                let output: Vec<HashMap<String, HashMap<String, String>>> = output?.extract()?;

                Ok(output[0].clone())
            });

            Ok(output?)
        }
        
    }
    
}

pub async fn execute_function(
    function: Py<PyAny>,
    number_of_params: u8,
    is_async: bool,
) -> Result<HashMap<String, String>> {
    let request: HashMap<String, String> = HashMap::new();

    if is_async {
        let output = Python::with_gil(|py| {
            let handler = function.as_ref(py);
            let coro: PyResult<&PyAny> = match number_of_params {
                0 => handler.call0(),
                1 => handler.call1((request,)),
                // this is done to accomodate any future params
                2_u8..=u8::MAX => handler.call1((request,)),
            };
            pyo3_asyncio::tokio::into_future(coro?)
        })?;

        let output = output.await?;
        let res = Python::with_gil(|py| -> PyResult<HashMap<String, String>> {
            debug!("This is the result of the code {:?}", output);

            let mut res: HashMap<String, String> =
                output.into_ref(py).downcast::<PyDict>()?.extract()?;

            let response_type = res.get("type").unwrap();

            if response_type == "static_file" {
                let file_path = res.get("file_path").unwrap();
                let contents = read_file(file_path).unwrap();
                res.insert("body".to_owned(), contents);
            }
            Ok(res)
        })?;

        Ok(res)
    } else {
        tokio::task::spawn_blocking(move || {
            Python::with_gil(|py| {
                let handler = function.as_ref(py);
                let output: PyResult<&PyAny> = match number_of_params {
                    0 => handler.call0(),
                    1 => handler.call1((request,)),
                    // this is done to accomodate any future params
                    2_u8..=u8::MAX => handler.call1((request,)),
                };
                let output: HashMap<String, String> = output?.extract()?;
                // also convert to object here
                // also check why don't sync functions have file handling enabled
                Ok(output)
            })
        })
        .await?
    }
}

// Change this!
#[inline]
pub async fn execute_http_function(
    function: PyFunction,
    payload: &mut [u8],
    headers: HashMap<String, String>,
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
    number_of_params: u8,
    // need to change this to return a response struct
    // create a custom struct for this
) -> Result<HashMap<String, String>> {
    let data: Vec<u8> = payload.to_owned();

    // request object accessible while creating routes
    let mut request = HashMap::new();

    let mut queries_clone: HashMap<String, String> = HashMap::new();

    for (key, value) in (*queries).borrow().clone() {
        queries_clone.insert(key, value);
    }

    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("queries", queries_clone.into_py(py));
                request.insert("headers", headers.into_py(py));
                let data = data.into_py(py);
                request.insert("body", data);

                // this makes the request object to be accessible across every route
                let coro: PyResult<&PyAny> = match number_of_params {
                    0 => handler.call0(),
                    1 => handler.call1((request,)),
                    // this is done to accomodate any future params
                    2_u8..=u8::MAX => handler.call1((request,)),
                };
                pyo3_asyncio::tokio::into_future(coro?)
            })?;

            let output = output.await?;
            let res = Python::with_gil(|py| -> PyResult<HashMap<String, String>> {
                debug!("This is the result of the code {:?}", output);

                let mut res: HashMap<String, String> =
                    output.into_ref(py).downcast::<PyDict>()?.extract()?;

                let response_type = res.get("type").unwrap();

                if response_type == "static_file" {
                    let file_path = res.get("file_path").unwrap();
                    let contents = read_file(file_path).unwrap();
                    res.insert("body".to_owned(), contents);
                }
                Ok(res)
            })?;

            Ok(res)
        }

        PyFunction::SyncFunction(handler) => {
            Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("headers", headers.into_py(py));
                let data = data.into_py(py);
                request.insert("body", data);

                let output: PyResult<&PyAny> = match number_of_params {
                    0 => handler.call0(),
                    1 => handler.call1((request,)),
                    // this is done to accomodate any future params
                    2_u8..=u8::MAX => handler.call1((request,)),
                };
                let output: HashMap<String, String> = output?.extract()?;
                // also convert to object here
                // also check why don't sync functions have file handling enabled
                Ok(output)
            })
        }
    }
}

pub async fn execute_event_handler(
    event_handler: Option<Arc<PyFunction>>,
    task_locals: &TaskLocals,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(handler) = event_handler {
        match &(*handler) {
            PyFunction::SyncFunction(function) => {
                debug!("Startup event handler");
                Python::with_gil(|py| -> Result<(), Box<dyn std::error::Error>> {
                    function.call0(py)?;
                    Ok(())
                })?;
            }
            PyFunction::CoRoutine(function) => {
                let future = Python::with_gil(|py| {
                    debug!("Startup event handler async");

                    let coroutine = function.as_ref(py).call0().unwrap();

                    pyo3_asyncio::into_future_with_locals(task_locals, coroutine).unwrap()
                });
                future.await?;
            }
        }
    }
    Ok(())
}
