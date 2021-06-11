use crate::request::Request;
use crate::router::{Route, RouteType, Router};
use crate::threadpool::ThreadPool;
use std::collections::HashMap;
use std::io::prelude::*;
use std::net::TcpListener;

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyAny;

#[pyclass]
pub struct Server {
    port: usize,
    number_of_threads: usize,
    router: Router, //
    threadpool: ThreadPool,
    listener: TcpListener,
    get_routes: HashMap<Route, Py<PyAny>>,
}

// unsafe impl Send for Server {}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        let url = format!("127.0.0.1:{}", 5000);
        let get_routes: HashMap<Route, Py<PyAny>> = HashMap::new();
        Self {
            port: 5000,
            number_of_threads: 1,
            router: Router::new(),
            threadpool: ThreadPool::new(1),
            listener: TcpListener::bind(url).unwrap(),
            get_routes, // not implemented in router as unable to match lifetimes
        }
    }

    pub fn start(&mut self) {
        let listener = &self.listener;
        let pool = &self.threadpool;
        for (k, v) in &self.get_routes {
            println!("Hello world but {} {}", k.get_route(), v);
        }

        for stream in listener.incoming() {
            let mut stream = stream.unwrap();
            let mut buffer = [0; 1024];
            stream.read(&mut buffer).unwrap();
            let route = Route::new(RouteType::Buffer(Box::new(buffer)));
            let status_line = "HTTP/1.1 200 OK";
            let contents = "Hello";
            let len = contents.len();
            let response = format!(
                "{}\r\nContent-Length: {}\r\n\r\n{}",
                status_line, len, contents
            );

            stream.write(response.as_bytes()).unwrap();
            stream.flush().unwrap();
            let f = self.get_routes.get(&route);
            // pool.push_async(f);
            match f {
                Some(a) => {
                    pool.push_async(&a.clone());
                }
                None => {}
            }
        }
    }

    pub fn add_route(&mut self, route_type: &str, route: String, handler: Py<PyAny>) {
        let route = Route::new(RouteType::Route(route));
        self.router.add_route(route_type, route, handler);
    }
}
