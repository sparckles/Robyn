use std::path::PathBuf;
use std::sync::Arc;

use actix_files::NamedFile;
use actix_web::{http::Method, web, HttpRequest, HttpResponse, HttpResponseBuilder};
use anyhow::{bail, Result};
// pyO3 module
use crate::types::{Headers, PyFunction, Response, STATIC_FILE};
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
    headers: &Arc<Headers>,
    payload: &mut web::Payload,
    req: &HttpRequest,
) -> Result<HttpResponse> {
    let contents = execute_function(function, payload, req).await?;

    if contents.response_type == STATIC_FILE {
        let path: PathBuf = contents.meta.into();
        return Ok(NamedFile::open(path)?.into_response(req));
    }

    let mut response = HttpResponse::Ok();
    apply_headers(&mut response, headers);
    Ok(response.body(contents.meta))
}

#[inline]
async fn execute_function(
    function: PyFunction,
    payload: &mut web::Payload,
    req: &HttpRequest,
) -> Result<Response> {
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
            let res = Python::with_gil(|py| -> PyResult<Response> {
                let reffer: Response = output.extract(py)?;
                Ok(reffer)
            })?;

            Ok(res)
        }
        PyFunction::SyncFunction(handler) => {
            tokio::task::spawn_blocking(move || {
                Python::with_gil(|py| {
                    let output: Py<PyAny> = match data {
                        Some(res) => {
                            let data = res.into_py(py);
                            handler.call1(py, (&data,))?
                        }
                        None => handler.call0(py)?,
                    };
                    let reffer: Response = output.extract(py)?;
                    Ok(reffer)
                })
            })
            .await?
        }
    }
}
