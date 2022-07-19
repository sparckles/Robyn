use crate::executors::{execute_http_function, execute_middleware_function};

use log::debug;
use std::rc::Rc;
use std::str::FromStr;
use std::{cell::RefCell, collections::HashMap};

use actix_web::{web, HttpRequest, HttpResponse, HttpResponseBuilder};
// pyO3 module
use crate::types::PyFunction;

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
pub async fn handle_http_request(
    function: PyFunction,
    number_of_params: u8,
    headers: HashMap<String, String>,
    payload: &mut web::Payload,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
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
            debug!("Error: {:?}", err);
            let mut response = HttpResponse::InternalServerError();
            apply_headers(&mut response, headers.clone());
            return response.finish();
        }
    };

    let body = contents.get("body").unwrap().to_owned();
    let status_code =
        actix_http::StatusCode::from_str(contents.get("status_code").unwrap()).unwrap();

    let response_headers: HashMap<String, String> = match contents.get("headers") {
        Some(headers) => {
            let h: HashMap<String, String> = serde_json::from_str(headers).unwrap();
            h
        }
        None => HashMap::new(),
    };

    debug!(
        "These are the request headers from serde {:?}",
        response_headers
    );

    let mut response = HttpResponse::build(status_code);
    apply_headers(&mut response, response_headers);
    let final_response = if !body.is_empty() {
        response.body(body)
    } else {
        response.finish()
    };

    debug!(
        "The response status code is {} and the headers are {:?}",
        final_response.status(),
        final_response.headers()
    );
    final_response
}

pub async fn handle_http_middleware_request(
    function: PyFunction,
    number_of_params: u8,
    headers: &HashMap<String, String>,
    payload: &mut web::Payload,
    req: &HttpRequest,
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
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

    debug!("These are the middleware response {:?}", contents);
    contents
}
