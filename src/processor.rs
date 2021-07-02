use std::sync::Arc;

use actix_web::{http::Method, web, HttpRequest, HttpResponse, HttpResponseBuilder};
use anyhow::{bail, Result};
// pyO3 module
use crate::types::{Headers, PyFunction};
use futures_util::stream::StreamExt;
use pyo3::prelude::*;

/// @TODO make configurable
const MAX_SIZE: usize = 10_000;

#[inline]
pub fn apply_headers(response: &mut HttpResponseBuilder, headers: &Arc<Headers>) {
    for a in headers.iter() {
        response.insert_header((a.key().clone(), a.value().clone()));
    }
}

/// Handle message fetches the response function
/// function is the response function fetched from the router
/// tokio task is spawned depending on the type of function fetched (Sync/Async)
pub async fn handle_request(
    function: PyFunction,
    headers: &Arc<Headers>,
    payload: &mut web::Payload,
    req: &HttpRequest,
) -> HttpResponse {
    let contents = match execute_function(function, payload, req).await {
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
async fn execute_function(
    function: PyFunction,
    payload: &mut web::Payload,
    req: &HttpRequest,
) -> Result<String> {
    let mut data: Option<Vec<u8>> = None;

    if req.method() == Method::POST {
        let mut body = web::BytesMut::new();
        while let Some(chunk) = payload.next().await {
            let chunk = chunk?;
            // limit max size of in-memory payload
            if (body.len() + chunk.len()) > MAX_SIZE {
                bail!("Overflow");
            }
            body.extend_from_slice(&chunk);
        }

        data = Some(body.to_vec())
    }

    match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let handler = handler.as_ref(py);

                let coro: PyResult<&PyAny> = match data {
                    Some(res) => {
                        let data = res.into_py(py);
                        handler.call1((&data,))
                    }
                    None => handler.call0(),
                };
                pyo3_asyncio::into_future(coro?)
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
                    let output: PyResult<&PyAny> = match data {
                        Some(res) => {
                            let data = res.into_py(py);
                            handler.call1((&data,))
                        }
                        None => handler.call0(),
                    };
                    let output: &str = output?.extract()?;

                    Ok(output.to_string())
                })
            })
            .await?
        }
    }
}
