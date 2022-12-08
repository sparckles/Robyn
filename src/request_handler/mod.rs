use crate::{
    executors::{execute_http_function, execute_middleware_function},
    types::Request,
};

use crate::io_helpers::apply_headers;
use log::debug;
use std::collections::HashMap;
use std::str::FromStr;

use actix_web::HttpResponse;
// pyO3 module
use crate::types::FunctionInfo;

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
pub async fn handle_http_request(request: &Request, function: FunctionInfo) -> HttpResponse {
    let contents = match execute_http_function(request, function).await {
        Ok(res) => res,
        Err(err) => {
            debug!("Error: {:?}", err);
            let mut response = HttpResponse::InternalServerError();
            apply_headers(&mut response, &request.headers);
            return response.finish();
        }
    };

    let body = contents.get("body").unwrap().to_owned();
    let status_code =
        actix_http::StatusCode::from_str(contents.get("status_code").unwrap()).unwrap();

    let response_headers = match contents.get("headers") {
        Some(headers) => serde_json::from_str(headers).unwrap(),
        None => HashMap::new(),
    };

    debug!(
        "These are the request headers from serde {:?}",
        response_headers
    );

    let mut response = HttpResponse::build(status_code);
    apply_headers(&mut response, &response_headers);
    apply_headers(&mut response, &request.headers);

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
    request: &Request,
    function: FunctionInfo,
) -> HashMap<String, HashMap<String, String>> {
    let contents = execute_middleware_function(request, function)
        .await
        .unwrap_or_default();

    debug!("These are the middleware response {:?}", contents);
    contents
}
