use std::collections::HashMap;
use std::str::FromStr;
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
pub fn apply_headers(response: &mut HttpResponseBuilder, headers: HashMap<String, String>) {
    for (key, val) in (headers).iter() {
        response.insert_header((key.clone(), val.clone()));
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
    headers: HashMap<String, String>,
    payload: &mut web::Payload,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: HashMap<String, String>,
) -> HttpResponse {
    let contents = match execute_http_function(
        function,
        payload,
        headers.clone(),
        req,
        route_params,
        queries,
        number_of_params,
    )
    .await
    {
        Ok(res) => res,
        Err(err) => {
            println!("Error: {:?}", err);
            let mut response = HttpResponse::InternalServerError();
            apply_headers(&mut response, headers.clone());
            return response.finish();
        }
    };

    let body = contents.get("body").unwrap().to_owned();
    let status_code =
        actix_http::StatusCode::from_str(contents.get("status_code").unwrap()).unwrap();

    let mut response = HttpResponse::build(status_code);
    apply_headers(&mut response, headers.clone());
    let final_response = if body != "" {
        response.body(body)
    } else {
        response.finish()
    };

    println!(
        "The status code is {} and the headers are {:?}",
        final_response.status(),
        final_response.headers()
    );
    // response.body(contents.get("body").unwrap().to_owned())
    final_response
}

pub async fn handle_middleware_request(
    function: PyFunction,
    number_of_params: u8,
    headers: &Arc<Headers>,
    payload: &mut web::Payload,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: HashMap<String, String>,
) -> HashMap<String, HashMap<String, String>> {
    let contents = match execute_middleware_function(
        function,
        payload,
        headers,
        req,
        route_params,
        queries,
        number_of_params,
    )
    .await
    {
        Ok(res) => res,
        Err(_err) => HashMap::new(),
    };

    println!("These are the middleware response {:?}", contents);
    contents
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

async fn execute_middleware_function<'a>(
    function: PyFunction,
    payload: &mut web::Payload,
    headers: &Headers,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: HashMap<String, String>,
    number_of_params: u8,
) -> Result<HashMap<String, HashMap<String, String>>> {
    // TODO:
    // try executing the first version of middleware(s) here
    // with just headers as params

    let mut data: Vec<u8> = Vec::new();

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

        data = body.to_vec()
    }

    // request object accessible while creating routes
    let mut request = HashMap::new();
    let mut headers_python = HashMap::new();
    for elem in (*headers).iter() {
        headers_python.insert(elem.key().clone(), elem.value().clone());
    }

    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("queries", queries.into_py(py));
                request.insert("headers", headers_python.into_py(py));
                // request.insert("body", data.into_py(py));

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

            let res =
                Python::with_gil(|py| -> PyResult<HashMap<String, HashMap<String, String>>> {
                    let output: Vec<HashMap<String, HashMap<String, String>>> =
                        output.extract(py).unwrap();
                    let responses = output[0].clone();
                    Ok(responses)
                })?;

            Ok(res)
        }

        PyFunction::SyncFunction(handler) => {
            tokio::task::spawn_blocking(move || {
                Python::with_gil(|py| {
                    let handler = handler.as_ref(py);
                    request.insert("params", route_params.into_py(py));
                    request.insert("queries", queries.into_py(py));
                    request.insert("headers", headers_python.into_py(py));
                    request.insert("body", data.into_py(py));

                    let output: PyResult<&PyAny> = match number_of_params {
                        0 => handler.call0(),
                        1 => handler.call1((request,)),
                        // this is done to accomodate any future params
                        2_u8..=u8::MAX => handler.call1((request,)),
                    };

                    let output: Vec<HashMap<String, HashMap<String, String>>> =
                        output?.extract().unwrap();

                    Ok(output[0].clone())
                })
            })
            .await?
        }
    }
}

// Change this!
#[inline]
async fn execute_http_function(
    function: PyFunction,
    payload: &mut web::Payload,
    headers: HashMap<String, String>,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: HashMap<String, String>,
    number_of_params: u8,
    // need to change this to return a response struct
    // create a custom struct for this
) -> Result<HashMap<String, String>> {
    let mut data: Vec<u8> = Vec::new();

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

        data = body.to_vec()
    }

    // request object accessible while creating routes
    let mut request = HashMap::new();

    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                request.insert("params", route_params.into_py(py));
                request.insert("queries", queries.into_py(py));
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
                println!("This is the result of the code {:?}", output);

                let mut res: HashMap<String, String> =
                    output.into_ref(py).downcast::<PyDict>()?.extract()?;

                let response_type = res.get("type").unwrap();

                if response_type == "static_file" {
                    let file_path = res.get("file_path").unwrap();
                    let contents = read_file(file_path);
                    res.insert("body".to_owned(), contents);
                }
                Ok(res)
            })?;

            Ok(res)
        }

        PyFunction::SyncFunction(handler) => {
            tokio::task::spawn_blocking(move || {
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
            })
            .await?
        }
    }
}

pub async fn execute_event_handler(
    event_handler: Option<Arc<PyFunction>>,
    event_loop: Arc<Py<PyAny>>,
) {
    if let Some(handler) = event_handler {
        match &(*handler) {
            PyFunction::SyncFunction(function) => {
                println!("Startup event handler");
                Python::with_gil(|py| {
                    function.call0(py).unwrap();
                });
            }
            PyFunction::CoRoutine(function) => {
                let future = Python::with_gil(|py| {
                    println!("Startup event handler async");

                    let coroutine = function.as_ref(py).call0().unwrap();
                    pyo3_asyncio::into_future_with_loop((*event_loop).as_ref(py), coroutine)
                        .unwrap()
                });
                future.await.unwrap();
            }
        }
    }
}
