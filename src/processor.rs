use std::sync::Arc;

use actix_web::{HttpResponse, HttpResponseBuilder};
use anyhow::Result;
// pyO3 module
use crate::types::{Headers, PyFunction};
use pyo3::prelude::*;

#[inline]
pub fn apply_headers(response: &mut HttpResponseBuilder, headers: &Arc<Headers>) {
    for a in headers.iter() {
        response.insert_header((a.key().clone(), a.value().clone()));
    }
}

/// Handle message fetches the response function
/// function is the response function fetched from the router
/// tokio task is spawned depending on the type of function fetched (Sync/Async)
pub async fn handle_request(function: PyFunction, headers: &Arc<Headers>) -> HttpResponse {
    let contents = match execute_function(function).await {
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
