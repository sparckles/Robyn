use std::collections::HashMap;
use std::net::TcpStream;

use pyo3::types::PyAny;

use crate::types::AsyncFunction;
enum RequestType {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    UPDATE,
}

struct Response {}
struct Request {}

struct Route {}

// this should ideally be a hashmap of hashmaps but not really
struct Router {
    get_routes: HashMap<Route, Vec<Request>>,
    post_routes: HashMap<Route, Vec<Request>>,
    put_routes: HashMap<Route, Vec<Request>>,
    patch_routes: HashMap<Route, Vec<Request>>,
    delete_routes: HashMap<Route, Vec<Request>>,
    update_routes: HashMap<Route, Vec<Request>>,
}
// these should be of the type struct and not the type router
// request_stream: &TcpStream,
// request_type: Option<RequestType>,
// headers: Vec<String>,
// body: Vec<String>

impl Router {
    fn new(request_stream: &TcpStream) -> Self {
        Self {
            routes: HashMap::new(),
        }
    }

    fn add_route(&mut self, route: String, request_type: RequestType, request: Request) {
        match request_type {
            RequestType::GET => self.get_routes.insert(route, request),
            RequestType::POST => self.post_routes.insert(route, request),
            RequestType::PUT => self.put_routes.insert(route, request),
            RequestType::PATCH => self.patch_routes.insert(route, request),
            RequestType::DELETE => self.delete_routes.insert(route, request),
            RequestType::UPDATE => self.update_routes.insert(route, request),
        };
    }
}
