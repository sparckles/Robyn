use crate::request::{Request, RequestType};
use std::collections::{HashMap, HashSet};
// pyo3 modules
use crate::types::{AsyncFunction, PyFuture};
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
}

// this should ideally be a hashmap of hashmaps but not really
use crate::threadpool::{Message, ThreadPool};

pub struct Router {
    get_routes: HashMap<Route, Message>,
}
// these should be of the type struct and not the type router
// request_stream: &TcpStream,
// request_type: Option<RequestType>,
// headers: Vec<String>,
// body: Vec<String>

impl Router {
    pub fn new() -> Self {
        let hmap = HashMap::new();
        Self { get_routes: hmap }
    }

    // pub fn add_route(&mut self, route: Route, handler: &'static Message) {
    //     self.get_routes.insert(route, handler);
    // }
}
