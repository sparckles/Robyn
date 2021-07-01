use anyhow::Result;
// pyO3 module
use crate::types::PyFunction;
use pyo3::prelude::*;

use hyper::{Body, Response, StatusCode};

// Handle message fetches the response function
// function is the response function fetched from the router
// tokio task is spawned depending on the type of function fetched (Sync/Async)

pub async fn handle_request(
    function: PyFunction,
) -> Result<Response<Body>, hyper::Error> {
    let contents = match execute_function(function).await {
        Ok(res) => res,
        Err(_err) => {
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::INTERNAL_SERVER_ERROR;
            return Ok(not_found);
        }
    };

    Ok(Response::new(Body::from(contents)))
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
                let contents: &str = output.extract(py)?;
                Ok(contents.to_string())
            })?;

            Ok(res)
        }
        PyFunction::SyncFunction(handler) => tokio::task::spawn_blocking(move || {
            Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                let output: &str = handler.call0()?.extract()?;
                Ok(output.to_string())
            })
        })
        .await?,
    }
}