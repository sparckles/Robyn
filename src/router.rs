use crate::request::Request;
use std::collections::HashMap;

enum RequestType {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    UPDATE,
}

#[derive(PartialEq, Eq, Hash)]
struct Route {}

// this should ideally be a hashmap of hashmaps but not really
pub struct Router {
    get_routes: HashMap<Route, Request>,
    post_routes: HashMap<Route, Request>,
    put_routes: HashMap<Route, Request>,
    patch_routes: HashMap<Route, Request>,
    delete_routes: HashMap<Route, Request>,
    update_routes: HashMap<Route, Request>,
}
// these should be of the type struct and not the type router
// request_stream: &TcpStream,
// request_type: Option<RequestType>,
// headers: Vec<String>,
// body: Vec<String>

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: HashMap::new(),
            post_routes: HashMap::new(),
            put_routes: HashMap::new(),
            patch_routes: HashMap::new(),
            delete_routes: HashMap::new(),
            update_routes: HashMap::new(),
        }
    }

    fn add_route(&mut self, route: Route, request_type: RequestType, request: Request) {
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
