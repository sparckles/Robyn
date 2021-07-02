use crate::processor::{apply_headers, handle_request};
use crate::router::Router;
use crate::types::Headers;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering::{Relaxed, SeqCst};
use std::sync::Arc;
use std::thread;
// pyO3 module
use actix_web::*;
use dashmap::DashMap;
use pyo3::prelude::*;
use pyo3::types::PyAny;

// hyper modules
use pyo3_asyncio::run_forever;

static STARTED: AtomicBool = AtomicBool::new(false);

#[pyclass]
pub struct Server {
    router: Arc<Router>,
    headers: Arc<DashMap<String, String>>,
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
            headers: Arc::new(DashMap::new()),
        }
    }

    pub fn start(&mut self, py: Python, port: u16) {
        if STARTED
            .compare_exchange(false, true, SeqCst, Relaxed)
            .is_err()
        {
            println!("Already running...");
            return;
        }

        let router = self.router.clone();
        let headers = self.headers.clone();

        thread::spawn(move || {
            //init_current_thread_once();
            actix_web::rt::System::new().block_on(async move {
                let addr = format!("127.0.0.1:{}", port);

                HttpServer::new(move || {
                    App::new()
                        .app_data(web::Data::new(router.clone()))
                        .app_data(web::Data::new(headers.clone()))
                        .default_service(web::route().to(index))
                })
                .bind(addr)
                .unwrap()
                .run()
                .await
                .unwrap();
            });
        });

        run_forever(py).unwrap()
    }

    /// Adds a new header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn add_header(&self, key: &str, value: &str) {
        self.headers.insert(key.to_string(), value.to_string());
    }

    /// Removes a new header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn remove_header(&self, key: &str) {
        self.headers.remove(key);
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>, is_async: bool) {
        println!("Route added for {} {} ", route_type, route);
        self.router.add_route(route_type, route, handler, is_async);
    }
}

/// This is our service handler. It receives a Request, routes on it
/// path, and returns a Future of a Response.
async fn index(
    router: web::Data<Arc<Router>>,
    headers: web::Data<Arc<Headers>>,
    mut payload: web::Payload,
    req: HttpRequest,
) -> impl Responder {
    match router.get_route(req.method().clone(), req.uri().path()) {
        Some(handler_function) => {
            handle_request(handler_function, &headers, &mut payload, &req).await
        }
        None => {
            let mut response = HttpResponse::NotFound();
            apply_headers(&mut response, &headers);
            response.finish()
        }
    }
}
