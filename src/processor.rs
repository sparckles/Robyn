use std::collections::HashMap;
use std::sync::Arc;

use actix_web::{http::Method, web, HttpRequest, HttpResponse, HttpResponseBuilder};
use anyhow::{bail, Result};
// pyO3 module
use crate::types::{Headers, PyFunction};
use futures_util::stream::StreamExt;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use std::fs::File;
use std::io::Read;

/// @TODO make configurable
const MAX_SIZE: usize = 10_000;

#[inline]
pub fn apply_headers(response: &mut HttpResponseBuilder, headers: &Arc<Headers>) {
    for a in headers.iter() {
        response.insert_header((a.key().clone(), a.value().clone()));
    }
}

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
pub async fn handle_request(
    function: PyFunction,
    number_of_params: u8,
    headers: &Arc<Headers>,
    payload: &mut web::Payload,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
) -> HttpResponse {
    let contents = match execute_http_function(
        function,
        payload,
        headers,
        req,
        route_params,
        number_of_params,
    )
    .await
    {
        Ok(res) => res,
        Err(err) => {
            println!("Error: {:?}", err);
            let mut response = HttpResponse::InternalServerError();
            apply_headers(&mut response, headers);
            return response.finish();
        }
    };

    let mut response = HttpResponse::Ok();
    apply_headers(&mut response, headers);
    response.body(contents)
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

// Change this!
#[inline]
async fn execute_http_function(
    function: PyFunction,
    payload: &mut web::Payload,
    headers: &Headers,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    number_of_params: u8,
) -> Result<String> {
    let mut data: Option<Vec<u8>> = None;

    if req.method() == Method::POST
        || req.method() == Method::PUT
        || req.method() == Method::PATCH
        || req.method() == Method::DELETE
    {
        let mut body = web::BytesMut::new();
        while let Some(chunk) = payload.next().await {
            let chunk = chunk?;
            // limit max size of in-memory payload
            if (body.len() + chunk.len()) > MAX_SIZE {
                bail!("Body content Overflow");
            }
            body.extend_from_slice(&chunk);
        }

        data = Some(body.to_vec())
    }

    // request object accessible while creating routes
    let mut request = HashMap::new();
    let mut headers_python = HashMap::new();
    for elem in headers.into_iter() {
        headers_python.insert(elem.key().clone(), elem.value().clone());
    }
    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("headers", headers_python.into_py(py));

                match data {
                    Some(res) => {
                        let data = res.into_py(py);
                        request.insert("body", data);
                    }
                    None => {}
                };

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
                                    Ok(read_file(file_path))
                                } else {
                                    Err(PyErr::from_instance("Server Error".into_py(py).as_ref(py)))
                                }
                            }
                            false => {
                                Err(PyErr::from_instance("Server Error".into_py(py).as_ref(py)))
                            }
                        }
                    }
                    Err(_) => {
                        // this means that this is basic string output
                        // and a json serialized string will be parsed here
                        let contents: &str = string_contents.extract(py)?;
                        Ok(contents.to_string())
                    }
                }
            })?;

            Ok(res)
        }

        PyFunction::SyncFunction(handler) => {
            tokio::task::spawn_blocking(move || {
                Python::with_gil(|py| {
                    let handler = handler.as_ref(py);
                    request.insert("params", route_params.into_py(py));
                    request.insert("headers", headers_python.into_py(py));
                    match data {
                        Some(res) => {
                            let data = res.into_py(py);
                            request.insert("body", data);
                        }
                        None => {}
                    };

                    let output: PyResult<&PyAny> = match number_of_params {
                        0 => handler.call0(),
                        1 => handler.call1((request,)),
                        // this is done to accomodate any future params
                        2_u8..=u8::MAX => handler.call1((request,)),
                    };
                    let output: &str = output?.extract()?;
                    Ok(output.to_string())
                })
            })
            .await?
        }
    }
}
