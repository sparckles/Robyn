use crate::router::{Route, RouteType, Router};
use crate::threadpool::ThreadPool;
use std::io::prelude::*;
use std::net::TcpListener;
use std::process;
use std::sync::{Arc, Mutex};
use std::thread;
// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyAny;

#[pyclass]
pub struct Server {
    port: usize,
    number_of_threads: usize,
    router: Arc<Router>, //
    threadpool: Arc<ThreadPool>,
}

// unsafe impl Send for Server {}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            port: 5000,
            number_of_threads: 1,
            router: Arc::new(Router::new()),
            threadpool: Arc::new(ThreadPool::new(1)),
        }
    }

    pub fn start(&mut self, py: Python) {
        let url = format!("127.0.0.1:{}", &self.port);
        let router = self.router.clone();
        let pool = self.threadpool.clone();

        // thread::spawn -> block on
        thread::spawn(move || {
            let listener = TcpListener::bind(url).unwrap();

            for stream in listener.incoming() {
                let mut stream = stream.unwrap();
                let mut buffer = [0; 1024];
                stream.read(&mut buffer).unwrap();
                let route = Route::new(RouteType::Buffer(Box::new(buffer)));

                match router.get_route(route) {
                    Some(a) => {
                        pool.push_async(a, stream);
                    }
                    None => {
                        print!("No match found");
                    }
                }
            }
        });

        let py_loop = pyo3_asyncio::async_std::run_until_complete(py, async move { loop {} });
        match py_loop {
            Ok(_) => {}
            Err(_) => {
                process::exit(1);
            }
        };
    }

    pub fn add_route(&mut self, route_type: &str, route: String, handler: Py<PyAny>) {
        println!("{} {} ", route_type, route);
        let route = Route::new(RouteType::Route((route, route_type.to_string())));
        self.router.add_route(route_type, route, handler);
    }
}
