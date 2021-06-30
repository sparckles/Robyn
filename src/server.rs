use crate::processor::handle_request;
use crate::router::{Route, RouteType, Router};
use std::process;
use std::sync::Arc;
// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3::types::PyDict;
use tokio::io::AsyncReadExt;
use tokio::net::{TcpListener, TcpStream};

// use futures_util::TryStreamExt;
use futures::TryStreamExt as _;
use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Error, Method, Request, Response, Server as HyperServer, StatusCode};

#[pyclass]
pub struct Server {
    router: Arc<Router>,
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            router: Arc::new(Router::new()),
        }
    }

    pub fn start(&mut self, py: Python, port: usize) {
        // starts the server and binds to the mentioned port
        // initialises the tokio async runtime
        // initialises the python async loop
        let url = format!("127.0.0.1:{}", port);
        let router = self.router.clone();
        pyo3_asyncio::tokio::init_multi_thread_once();

        let py_loop = pyo3_asyncio::tokio::run_until_complete(py, async move {
            // let listener = TcpListener::bind(url).await.unwrap();
            // We'll bind to 127.0.0.1:3000
            // while let Ok((stream, _addr)) = listener.accept().await {
            let router = router.clone();
            //     tokio::spawn(handle_stream(router, stream));
            // }
            let addr = ([127, 0, 0, 1], 3000).into();
            // let router = Box::new(router);
            // let service = make_service_fn(move |_| async {
            //     let router = router.clone();
            //     Ok::<_, hyper::Error>(service_fn(|req| async {
            //         handle_stream(req, router.clone()).await
            //     }))
            // });

            let service = make_service_fn(move |_| {
                // let router = router.clone();
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

    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>) {
        println!("Route added for {} {} ", route_type, route);
        // let route = Route::new(RouteType::Route((route, route_type.to_string())));
        self.router.add_route(route_type, &route, handler);
    }
}

/// This is our service handler. It receives a Request, routes on its
/// path, and returns a Future of a Response.
async fn echo(req: Request<Body>) -> Result<Response<Body>, hyper::Error> {
    match (req.method(), req.uri().path()) {
        // Serve some instructions at /
        (&Method::GET, "/") => Ok(Response::new(Body::from(
            "Try POSTing data to /echo such as: `curl localhost:3000/echo -XPOST -d 'hello world'`",
        ))),

        // Simply echo the body back to the client.
        (&Method::POST, "/echo") => Ok(Response::new(req.into_body())),

        // Convert to uppercase before sending back to client using a stream.
        (&Method::POST, "/echo/uppercase") => {
            let chunk_stream = req.into_body().map_ok(|chunk| {
                chunk
                    .iter()
                    .map(|byte| byte.to_ascii_uppercase())
                    .collect::<Vec<u8>>()
            });
            Ok(Response::new(Body::wrap_stream(chunk_stream)))
        }

        // Reverse the entire body before sending back to the client.
        //
        // Since we don't know the end yet, we can't simply stream
        // the chunks as they arrive as we did with the above uppercase endpoint.
        // So here we do `.await` on the future, waiting on concatenating the full body,
        // then afterwards the content can be reversed. Only then can we return a `Response`.
        (&Method::POST, "/echo/reversed") => {
            let whole_body = hyper::body::to_bytes(req.into_body()).await?;

            let reversed_body = whole_body.iter().rev().cloned().collect::<Vec<u8>>();
            Ok(Response::new(Body::from(reversed_body)))
        }

        // Return the 404 Not Found for other routes.
        _ => {
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::NOT_FOUND;
            Ok(not_found)
        }
    }
}

async fn handle_stream(
    req: Request<Body>,
    router: Arc<Router>,
) -> Result<Response<Body>, hyper::Error> {
    // this function will handle the stream
    // this will get spawned on every request according to tokios runtime
    // analyse the http request and serve back the response
    // let mut buffer = [0; 1024];
    // stream.read(&mut buffer).await.unwrap();

    // let route = Route::new(RouteType::Buffer(Box::new(buffer)));

    // tokio::spawn(async move {
    // if route.get_route() == "" && route.get_route_type() == "" {
    //     // println!("BAD Request");
    //     // handle_request(None, stream, 400).await;
    //     // return;
    //     let mut not_found = Response::default();
    //     *not_found.status_mut() = StatusCode::NOT_FOUND;
    //     return not_found;
    // }

    // match (req.method(), req.uri().path()) {

    println!("BCCCCC");
    match router.get_route(req.method(), req.uri().path()) {
        Some(a) => {
            println!("BCCCCC");

            return handle_request(Some(a), 200).await;
        }
        None => {
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::NOT_FOUND;
            return Ok(not_found);
        }
    };
    // })
}
