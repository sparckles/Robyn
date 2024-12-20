mod executors;
mod io_helpers;
mod routers;
mod server;
mod shared_socket;
mod types;
mod websockets;

use server::Server;
use shared_socket::SocketHeld;

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyTuple;
use types::{
    function_info::{FunctionInfo, MiddlewareType},
    headers::Headers,
    identity::Identity,
    multimap::QueryParams,
    request::{PyRequest, Request},
    response::{PyResponse, Response, ResponseBody},
    HttpMethod, Url,
};
use actix_web::{Error, error::ErrorInternalServerError};
use anyhow::Result;

use websockets::{registry::WebSocketRegistry, WebSocketConnector};

fn create_error_response(e: impl std::fmt::Display) -> Response {
    let headers = Headers::new(None);
    headers.headers.entry("Content-Type".to_string()).or_default().push("text/plain".to_string());
    headers.headers.entry("X-Error-Response".to_string()).or_default().push("true".to_string());
    headers.headers.entry("global_after".to_string()).or_default().push("global_after_request".to_string());
    headers.headers.entry("server".to_string()).or_default().push("robyn".to_string());

    Response {
        status_code: 500,
        response_type: "text".to_string(),
        headers,
        body: ResponseBody::Text(format!("error msg: {}", e)),
        file_path: None,
        streaming: false,
    }
}

#[pyfunction]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").into()
}

#[pymodule]
pub fn robyn(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // the pymodule class/function to make the rustPyFunctions available
    m.add_function(wrap_pyfunction!(get_version, m)?)?;

    m.add_class::<Server>()?;
    m.add_class::<Headers>()?;
    m.add_class::<WebSocketRegistry>()?;
    m.add_class::<WebSocketConnector>()?;
    m.add_class::<SocketHeld>()?;
    m.add_class::<FunctionInfo>()?;
    m.add_class::<Identity>()?;
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    m.add_class::<Url>()?;
    m.add_class::<QueryParams>()?;
    m.add_class::<MiddlewareType>()?;
    m.add_class::<HttpMethod>()?;

    pyo3::prepare_freethreaded_python();
    Ok(())
}

fn handle_error<E: std::fmt::Display>(e: E, py: Python) -> Result<PyObject, Error> {
    let headers = Headers::new(None);
    headers.headers.entry("Content-Type".to_string()).or_default().push("text/plain".to_string());
    headers.headers.entry("X-Error-Response".to_string()).or_default().push("true".to_string());
    headers.headers.entry("global_after".to_string()).or_default().push("global_after_request".to_string());
    headers.headers.entry("server".to_string()).or_default().push("robyn".to_string());

    PyResponse::new(
        py,
        500,
        headers.into_py(py).as_ref(py),
        format!("error msg: {}", e).into_py(py),
        None,
    )
    .map(|resp| resp.into_py(py))
    .map_err(|e| ErrorInternalServerError(e.to_string()))
}

pub async fn handle_route(
    request: Request,
    function: FunctionInfo,
    py: Python<'_>,
) -> Result<Response, Error> {
    let handler = function.handler;
    let is_async = function.is_async;
    let number_of_params = function.number_of_params;

    let mut args = Vec::new();
    if number_of_params > 0 {
        args.push(request.to_object(py));
    }

    let result = if is_async {
        let args = PyTuple::new(py, args);
        match handler.call1(py, args) {
            Ok(awaitable) => {
                match pyo3_asyncio::tokio::into_future(awaitable.as_ref(py)) {
                    Ok(future) => {
                        match future.await {
                            Ok(result) => Ok(result),
                            Err(e) => Ok(handle_error(e, py)?)
                        }
                    }
                    Err(e) => Ok(handle_error(e, py)?)
                }
            }
            Err(e) => Ok(handle_error(e, py)?)
        }
    } else {
        let args = PyTuple::new(py, args);
        handler.call1(py, args)
    };

    match result {
        Ok(result) => {
            if let Ok(response) = result.extract::<Response>(py) {
                Ok(response)
            } else if let Ok(text) = result.extract::<String>(py) {
                Ok(Response {
                    status_code: 200,
                    response_type: "text".to_string(),
                    headers: Headers::new(None),
                    body: ResponseBody::Text(text),
                    file_path: None,
                    streaming: false,
                })
            } else {
                // Convert any other type to string
                let text = result.as_ref(py).str().map_err(|e| ErrorInternalServerError(e.to_string()))?.to_string();
                Ok(Response {
                    status_code: 200,
                    response_type: "text".to_string(),
                    headers: Headers::new(None),
                    body: ResponseBody::Text(text),
                    file_path: None,
                    streaming: false,
                })
            }
        }
        Err(e) => {
            let headers = Headers::new(None);
            headers.headers.entry("Content-Type".to_string()).or_default().push("text/plain".to_string());
            headers.headers.entry("X-Error-Response".to_string()).or_default().push("true".to_string());
            headers.headers.entry("global_after".to_string()).or_default().push("global_after_request".to_string());
            headers.headers.entry("server".to_string()).or_default().push("robyn".to_string());

            Ok(Response {
                status_code: 500,
                response_type: "text".to_string(),
                headers,
                body: ResponseBody::Text(format!("error msg: {}", e)),
                file_path: None,
                streaming: false,
            })
        }
    }
}
