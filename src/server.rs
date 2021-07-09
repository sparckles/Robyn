use crate::processor::handle_request;
use crate::router::Router;
use std::process;
use std::sync::Arc;
// pyO3 module
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyString};

// hyper modules
use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Error, Request, Response, Server as HyperServer, StatusCode};

use tokio::fs;

#[pyclass]
pub struct Server {
    router: Arc<Router>,
}

impl Default for Server {
    fn default() -> Self {
        Self::new()
    }
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            router: Arc::new(Router::new()),
        }
    }

    pub fn start(&mut self, py: Python, port: u16) {
        // starts the server and binds to the mentioned port
        // initialises the tokio async runtime
        // initialises the python async loop
        let router = self.router.clone();
        pyo3_asyncio::tokio::init_multi_thread_once();

        let py_loop = pyo3_asyncio::tokio::run_until_complete(py, async move {
            let router = router.clone();
            let addr = ([127, 0, 0, 1], port).into();

            let service = make_service_fn(move |_| {
                let router = router.clone();
                async move {
                    Ok::<_, Error>(service_fn(move |req| {
                        let router = router.clone();
                        async move { Ok::<_, Error>(handle_stream(req, router).await.unwrap()) }
                    }))
                }
            });

            let server = HyperServer::bind(&addr).serve(service);
            println!("Listening on http://{}", addr);
            server.await.unwrap();
            Ok(())
        });
        match py_loop {
            Ok(_) => {}
            Err(_) => {
                process::exit(1);
            }
        };
    }

    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>, is_async: bool) {
        println!("Route added for {} {} ", route_type, route);
        self.router.add_route(route_type, route, handler, is_async);
    }
}

// #[pyfunction]
// pub fn async_static_file(py: Python, file_name: String) -> PyResult<&PyAny> {
//     pyo3_asyncio::tokio::local_future_into_py(py, async move {
//         let contents = fs::read(file_name.clone()).await.unwrap();
//         let foo = String::from_utf8_lossy(&contents);
//         Ok(Python::with_gil(|py| {
//             let x = PyString::new(py, &foo);
//             let any: &PyAny = x.as_ref();
//             let any = any.to_object(py);
//             any.clone()
//         }))
//     })
// }

/// This is our service handler. It receives a Request, routes on its
/// path, and returns a Future of a Response.
async fn handle_stream(
    req: Request<Body>,
    router: Arc<Router>,
) -> Result<Response<Body>, hyper::Error> {
    // this function will handle the stream
    // this will get spawned on every request according to tokios runtime
    // analyse the http request and serve back the response
    //
    // ?? need to check about bad requests || maybe when you start handling headers and post
    // requests

    match router.get_route(req.method().clone(), req.uri().path()) {
        Some(handler_function) => handle_request(handler_function).await,
        None => {
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::NOT_FOUND;
            Ok(not_found)
        }
    }
}
