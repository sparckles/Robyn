use std::collections::HashMap;
// pyo3 modules
use pyo3::prelude::*;

pub enum RouteType {
    Route(String),
    Buffer(Box<[u8]>),
}

#[derive(PartialEq, Eq, Hash, Debug)]
pub struct Route {
    route: String,
}

impl Route {
    pub fn new(route: RouteType) -> Self {
        match route {
            RouteType::Buffer(buffer) => {
                let stream = String::from_utf8((&buffer).to_vec()).unwrap();
                let stream = stream
                    .split_whitespace()
                    .filter(|x| x.starts_with("/"))
                    .nth(0)
                    .unwrap();

                println!("{}", stream);
                Self {
                    route: stream.to_string(),
                }
            }
            RouteType::Route(route) => Self { route },
        }
    }

    pub fn get_route(&self) -> String {
        self.route.clone()
    }
}

// this should ideally be a hashmap of hashmaps but not really

pub struct Router {
    get_routes: HashMap<Route, Py<PyAny>>,
    post_routes: HashMap<Route, Py<PyAny>>,
    put_routes: HashMap<Route, Py<PyAny>>,
    update_routes: HashMap<Route, Py<PyAny>>,
    delete_routes: HashMap<Route, Py<PyAny>>,
    patch_routes: HashMap<Route, Py<PyAny>>,
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
            update_routes: HashMap::new(),
            delete_routes: HashMap::new(),
            patch_routes: HashMap::new(),
        }
    }

    pub fn add_route(&mut self, route_type: &str, route: Route, handler: Py<PyAny>) {
        if route_type == "GET" {
            self.get_routes.insert(route, handler);
        } else if route_type == "POST" {
            self.post_routes.insert(route, handler);
        } else if route_type == "PUT" {
            self.put_routes.insert(route, handler);
        } else if route_type == "UPDATE" {
            self.update_routes.insert(route, handler);
        } else if route_type == "DELETE" {
            self.delete_routes.insert(route, handler);
        } else if route_type == "PATCH" {
            self.patch_routes.insert(route, handler);
        }
    }
}
