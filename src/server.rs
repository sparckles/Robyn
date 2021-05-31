use crate::request::Request;
use crate::router::{Route, RouteType, Router};
use crate::threadpool::ThreadPool;
use std::io::prelude::*;
use std::net::{TcpListener, TcpStream};

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyLong};

#[pyclass]
pub struct Server {
    port: usize,
    number_of_threads: usize,
    router: Router, //
    threadpool: ThreadPool,
    listener: TcpListener,
}

#[pymethods]
impl Server {
    // pub fn new(port: usize, number_of_threads: usize) -> Self {
    #[new]
    pub fn new() -> Self {
        let url = format!("127.0.0.1:{}", 5000);
        Self {
            port: 5000,
            number_of_threads: 1,
            router: Router::new(),
            threadpool: ThreadPool::new(1),
            listener: TcpListener::bind(url).unwrap(),
        }
    }

    pub fn start(&mut self) {
        let listener = &self.listener;
        let pool = &self.threadpool;

        // test()

        for stream in listener.incoming() {
            let mut stream = stream.unwrap();
            let mut buffer = [0; 1024];
            stream.read(&mut buffer).unwrap();
            let route = Route::new(RouteType::Buffer(Box::new(buffer)));
            let request = Request::new(stream);
            // yaha pe add a check and dispatch the code and instead of pool.execute
            //  use pool.async

            // need to change on how we are passing the functions in the thread
            pool.execute(|| {
                let rt = tokio::runtime::Runtime::new().unwrap();
                // let mut contents = String::new();
                // handle_connection(stream, rt, &mut contents, &test_helper);
            });
        }
    }

    pub fn add_route(&mut self, route: String, handler: &PyAny) {
        // not considering abhi and adding everything to the get type
        self.router
            .add_route(Route::new(RouteType::Route(route)), handler);
    }
}
