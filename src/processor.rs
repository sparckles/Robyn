use anyhow::Result;
// pyO3 module
use crate::types::PyFunction;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use std::fs::File;
use std::io::Read;

use hyper::{Body, Response, StatusCode};

// Handle message fetches the response function
// function is the response function fetched from the router
// tokio task is spawned depending on the type of function fetched (Sync/Async)

/// This functions handles the incoming request matches it to the function and serves the response
///
/// # Arguments
///
/// * `function` - a PyFunction matched from the router
///
/// # Errors
///
/// When the route is not found. It should check if the 404 route exist and then serve it back
/// There can also be PyError due to any mis processing of the files
///
pub async fn handle_request(function: PyFunction) -> Result<Response<Body>, hyper::Error> {
    let contents = match execute_function(function).await {
        Ok(res) => res,
        Err(err) => {
            println!("Error: {:?}", err);
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::INTERNAL_SERVER_ERROR;
            return Ok(not_found);
        }
    };

    Ok(Response::new(Body::from(contents)))
}

// ideally this should be async
/// A function to read lossy files and serve it as a html response
///
/// # Arguments
///
/// * `file_path` - The file path that we want the function to read
///
fn read_file(file_path: &str) -> String {
    let mut file = File::open(file_path).unwrap();
    let mut buf = vec![];
    file.read_to_end(&mut buf).unwrap();
    String::from_utf8_lossy(&buf).to_string()
}

#[inline]
async fn execute_function(function: PyFunction) -> Result<String> {
    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let coro = handler.as_ref(py).call0()?;
                pyo3_asyncio::into_future(coro)
            })?;
            let output = output.await?;
            let res = Python::with_gil(|py| -> PyResult<String> {
                let string_contents = output.clone();
                let contents = output.into_ref(py).downcast::<PyDict>();
                match contents {
                    Ok(res) => {
                        // static file or json here
                        let contains_response_type = res.contains("response_type")?;
                        match contains_response_type {
                            true => {
                                let response_type: &str =
                                    res.get_item("response_type").unwrap().extract()?;
                                if response_type == "static_file" {
                                    // static file here and serve string
                                    let file_path = res.get_item("file_path").unwrap().extract()?;
                                    return Ok(read_file(file_path));
                                } else {
                                    return Err(PyErr::from_instance(
                                        "Server Error".into_py(py).as_ref(py),
                                    ));
                                }
                            }
                            false => {
                                return Err(PyErr::from_instance(
                                    "Server Error".into_py(py).as_ref(py),
                                ));
                            }
                        }
                    }
                    Err(_) => {
                        // this means that this is basic string output
                        // and a json serialized string will be parsed here
                        let contents: &str = string_contents.extract(py)?;
                        return Ok(contents.to_string());
                    }
                }
            })?;

            Ok(res)
        }
        PyFunction::SyncFunction(handler) => {
            tokio::task::spawn_blocking(move || {
                Python::with_gil(|py| {
                    let handler = handler.as_ref(py);
                    let output: &str = handler.call0()?.extract()?;
                    Ok(output.to_string())
                })
            })
            .await?
        }
    }
}
