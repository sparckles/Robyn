use crate::processor::handle_request;
use crate::router::Router;
use std::sync::Arc;
use std::thread;
// pyO3 module
use actix_web::*;
use pyo3::prelude::*;
use pyo3::types::PyAny;

// hyper modules
use pyo3_asyncio::run_forever;

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

        thread::spawn(move || {
            //init_current_thread_once();
            actix_web::rt::System::new().block_on(async move {
                let router = router.clone();

                let addr = format!("127.0.0.1:{}", port);

                HttpServer::new(move || {
                    App::new()
                        .app_data(web::Data::new(router.clone()))
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

    pub fn add_route(&self, route_type: &str, route: &str, handler: Py<PyAny>, is_async: bool) {
        println!("Route added for {} {} ", route_type, route);
        self.router.add_route(route_type, route, handler, is_async);
    }
}

/// This is our service handler. It receives a Request, routes on its
/// path, and returns a Future of a Response.
async fn index(router: web::Data<Arc<Router>>, req: HttpRequest) -> impl Responder {
    match router.get_route(req.method().clone(), req.uri().path()) {
        Some(handler_function) => handle_request(handler_function).await,
        None => HttpResponse::NotFound().into(),
    }
}
