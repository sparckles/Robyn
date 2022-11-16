use crate::executors::{execute_http_function, execute_middleware_function};

use log::debug;
use std::rc::Rc;
use std::str::FromStr;
use std::{cell::RefCell, collections::HashMap};

use actix_web::{HttpResponse, HttpResponseBuilder};
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
    payload: &mut [u8],
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
) -> HttpResponse {
    let contents = match execute_http_function(
        function,
        payload,
        headers.clone(),
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

    // removed the response creation

    contents
}

pub async fn handle_http_middleware_request(
    function: PyFunction,
    number_of_params: u8,
    headers: &HashMap<String, String>,
    payload: &mut [u8],
    route_params: HashMap<String, String>,
    queries: Rc<RefCell<HashMap<String, String>>>,
    res: Option<&HttpResponse>,
) -> HashMap<String, HashMap<String, String>> {
    let contents = match execute_middleware_function(
        function,
        payload,
        headers,
        route_params,
        queries,
        number_of_params,
        res,
    )
    .await
    {
        Ok(res) => res,
        Err(_err) => HashMap::new(),
    };

    debug!("These are the middleware response {:?}", contents);
    contents
}
