use actix_web::{web, HttpRequest, HttpResponse};
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::types::{Headers, Response, StreamingResponse};

pub async fn handle_request(
    req: HttpRequest,
    path: web::Path<String>,
    query: web::Query<std::collections::HashMap<String, String>>,
    payload: web::Payload,
    app_state: web::Data<PyObject>,
) -> HttpResponse {
    let path = path.into_inner();
    let query = query.into_inner();

    Python::with_gil(|py| {
        let app = app_state.as_ref();
        let args = PyDict::new(py);

        // Convert query params to Python dict
        let query_dict = PyDict::new(py);
        for (key, value) in query {
            query_dict.set_item(key, value).unwrap();
        }

        // Create headers dict
        let headers = Headers::new(None);

        // Call the route handler
        let result = app.call_method1(
            py,
            "handle_request",
            (path, req.method().as_str(), query_dict, headers),
        );

        match result {
            Ok(response) => {
                // Try to extract as StreamingResponse first
                match response.extract::<StreamingResponse>(py) {
                    Ok(streaming_response) => streaming_response.respond_to(&req),
                    Err(_) => {
                        // If not a StreamingResponse, try as regular Response
                        match response.extract::<Response>(py) {
                            Ok(response) => response.respond_to(&req),
                            Err(e) => {
                                // If extraction fails, return 500 error
                                let headers = Headers::new(None);
                                Response::internal_server_error(Some(&headers)).respond_to(&req)
                            }
                        }
                    }
                }
            }
            Err(e) => {
                // Handle Python error by returning 500
                let headers = Headers::new(None);
                Response::internal_server_error(Some(&headers)).respond_to(&req)
            }
        }
    })
}

pub async fn handle_request_with_body(
    req: HttpRequest,
    path: web::Path<String>,
    query: web::Query<std::collections::HashMap<String, String>>,
    payload: web::Payload,
    app_state: web::Data<PyObject>,
) -> HttpResponse {
    let path = path.into_inner();
    let query = query.into_inner();

    Python::with_gil(|py| {
        let app = app_state.as_ref();
        let args = PyDict::new(py);

        // Convert query params to Python dict
        let query_dict = PyDict::new(py);
        for (key, value) in query {
            query_dict.set_item(key, value).unwrap();
        }

        // Create headers dict
        let headers = Headers::new(None);

        // Call the route handler
        let result = app.call_method1(
            py,
            "handle_request_with_body",
            (path, req.method().as_str(), query_dict, headers, payload),
        );

        match result {
            Ok(response) => {
                // Try to extract as StreamingResponse first
                match response.extract::<StreamingResponse>(py) {
                    Ok(streaming_response) => streaming_response.respond_to(&req),
                    Err(_) => {
                        // If not a StreamingResponse, try as regular Response
                        match response.extract::<Response>(py) {
                            Ok(response) => response.respond_to(&req),
                            Err(e) => {
                                // If extraction fails, return 500 error
                                let headers = Headers::new(None);
                                Response::internal_server_error(Some(&headers)).respond_to(&req)
                            }
                        }
                    }
                }
            }
            Err(e) => {
                // Handle Python error by return 500
                let headers = Headers::new(None);
                Response::internal_server_error(Some(&headers)).respond_to(&req)
            }
        }
    })
} 