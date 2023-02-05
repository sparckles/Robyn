use crate::executors::{execute_event_handler, execute_http_function, execute_middleware_function};
use crate::io_helpers::{apply_dashmap_headers, apply_hashmap_headers};
use crate::types::Request;

use crate::routers::const_router::ConstRouter;
use crate::routers::Router;

use crate::routers::http_router::HttpRouter;
use crate::routers::types::MiddlewareRoute;
use crate::routers::{middleware_router::MiddlewareRouter, web_socket_router::WebSocketRouter};
use crate::shared_socket::SocketHeld;
use crate::types::{FunctionInfo, Headers};
use crate::web_socket_connection::start_web_socket;

use std::collections::HashMap;
use std::convert::TryInto;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering::{Relaxed, SeqCst};
use std::sync::{Arc, RwLock};

use std::process::abort;
use std::thread;

use actix_files::Files;
use actix_http::{KeepAlive, StatusCode};
use actix_web::web::Bytes;
use actix_web::*;
use dashmap::DashMap;

// pyO3 module
use log::debug;
use pyo3::prelude::*;

static STARTED: AtomicBool = AtomicBool::new(false);

#[derive(Clone)]
struct Directory {
    route: String,
    directory_path: String,
    index_file: Option<String>,
    show_files_listing: bool,
}

#[pyclass]
pub struct Server {
    router: Arc<HttpRouter>,
    const_router: Arc<ConstRouter>,
    websocket_router: Arc<WebSocketRouter>,
    middleware_router: Arc<MiddlewareRouter>,
    global_request_headers: Arc<DashMap<String, String>>,
    directories: Arc<RwLock<Vec<Directory>>>,
    startup_handler: Option<Arc<FunctionInfo>>,
    shutdown_handler: Option<Arc<FunctionInfo>>,
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            router: Arc::new(HttpRouter::new()),
            const_router: Arc::new(ConstRouter::new()),
            websocket_router: Arc::new(WebSocketRouter::new()),
            middleware_router: Arc::new(MiddlewareRouter::new()),
            global_request_headers: Arc::new(DashMap::new()),
            directories: Arc::new(RwLock::new(Vec::new())),
            startup_handler: None,
            shutdown_handler: None,
        }
    }

    pub fn start(
        &mut self,
        py: Python,
        socket: &PyCell<SocketHeld>,
        workers: usize,
    ) -> PyResult<()> {
        pyo3_log::init();

        if STARTED
            .compare_exchange(false, true, SeqCst, Relaxed)
            .is_err()
        {
            debug!("Robyn is already running...");
            return Ok(());
        }

        let raw_socket = socket.try_borrow_mut()?.get_socket();

        let router = self.router.clone();
        let const_router = self.const_router.clone();
        let middleware_router = self.middleware_router.clone();
        let web_socket_router = self.websocket_router.clone();
        let global_request_headers = self.global_request_headers.clone();
        let directories = self.directories.clone();
        let workers = Arc::new(workers);

        let asyncio = py.import("asyncio")?;
        let event_loop = asyncio.call_method0("new_event_loop")?;
        asyncio.call_method1("set_event_loop", (event_loop,))?;

        let startup_handler = self.startup_handler.clone();
        let shutdown_handler = self.shutdown_handler.clone();

        let task_locals = pyo3_asyncio::TaskLocals::new(event_loop).copy_context(py)?;
        let task_locals_copy = task_locals.clone();

        thread::spawn(move || {
            actix_web::rt::System::new().block_on(async move {
                debug!("The number of workers are {}", workers.clone());
                execute_event_handler(startup_handler, &task_locals_copy)
                    .await
                    .unwrap();

                HttpServer::new(move || {
                    let mut app = App::new();

                    let task_locals = task_locals_copy.clone();
                    let directories = directories.read().unwrap();

                    // this loop matches three types of directory serving
                    // 1. Serves a build folder. e.g. the build folder generated from yarn build
                    // 2. Shows file listing
                    // 3. Just serves the file without any redirection to sub links
                    for directory in directories.iter() {
                        if let Some(index_file) = &directory.index_file {
                            app = app.service(
                                Files::new(&directory.route, &directory.directory_path)
                                    .index_file(index_file)
                                    .redirect_to_slash_directory(),
                            );
                        } else if directory.show_files_listing {
                            app = app.service(
                                Files::new(&directory.route, &directory.directory_path)
                                    .redirect_to_slash_directory()
                                    .show_files_listing(),
                            );
                        } else {
                            app = app
                                .service(Files::new(&directory.route, &directory.directory_path));
                        }
                    }

                    app = app
                        .app_data(web::Data::new(router.clone()))
                        .app_data(web::Data::new(const_router.clone()))
                        .app_data(web::Data::new(middleware_router.clone()))
                        .app_data(web::Data::new(global_request_headers.clone()));

                    let web_socket_map = web_socket_router.get_web_socket_map();
                    for (elem, value) in (web_socket_map.read().unwrap()).iter() {
                        let route = elem.clone();
                        let params = value.clone();
                        let task_locals = task_locals.clone();
                        app = app.route(
                            &route.clone(),
                            web::get().to(move |stream: web::Payload, req: HttpRequest| {
                                start_web_socket(req, stream, params.clone(), task_locals.clone())
                            }),
                        );
                    }

                    app.default_service(web::route().to(
                        move |router: web::Data<Arc<HttpRouter>>,
                              const_router: web::Data<Arc<ConstRouter>>,
                              middleware_router: web::Data<Arc<MiddlewareRouter>>,
                              global_request_headers,
                              body,
                              req| {
                            pyo3_asyncio::tokio::scope_local(task_locals.clone(), async move {
                                index(
                                    router,
                                    const_router,
                                    middleware_router,
                                    global_request_headers,
                                    body,
                                    req,
                                )
                                .await
                            })
                        },
                    ))
                })
                .keep_alive(KeepAlive::Os)
                .workers(*workers.clone())
                .client_request_timeout(std::time::Duration::from_secs(0))
                .listen(raw_socket.try_into().unwrap())
                .unwrap()
                .run()
                .await
                .unwrap();
            });
        });

        let event_loop = (*event_loop).call_method0("run_forever");
        if event_loop.is_err() {
            debug!("Ctrl c handler");
            Python::with_gil(|py| {
                pyo3_asyncio::tokio::run(py, async move {
                    execute_event_handler(shutdown_handler, &task_locals.clone())
                        .await
                        .unwrap();
                    Ok(())
                })
            })?;
            abort();
        }
        Ok(())
    }

    pub fn add_directory(
        &mut self,
        route: String,
        directory_path: String,
        index_file: Option<String>,
        show_files_listing: bool,
    ) {
        self.directories.write().unwrap().push(Directory {
            route,
            directory_path,
            index_file,
            show_files_listing,
        });
    }

    /// Adds a new header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn add_request_header(&self, key: &str, value: &str) {
        self.global_request_headers
            .insert(key.to_string(), value.to_string());
    }

    /// Removes a new header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn remove_header(&self, key: &str) {
        self.global_request_headers.remove(key);
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_route(
        &self,
        py: Python,
        route_type: &str,
        route: &str,
        function: FunctionInfo,
        is_const: bool,
    ) {
        debug!("Route added for {} {} ", route_type, route);
        let asyncio = py.import("asyncio").unwrap();
        let event_loop = asyncio.call_method0("get_event_loop").unwrap();

        if is_const {
            match self
                .const_router
                .add_route(route_type, route, function, Some(event_loop))
            {
                Ok(_) => (),
                Err(e) => {
                    debug!("Error adding const route {}", e);
                }
            }
        } else {
            match self.router.add_route(route_type, route, function, None) {
                Ok(_) => (),
                Err(e) => {
                    debug!("Error adding route {}", e);
                }
            }
        }
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_middleware_route(&self, route_type: &str, route: &str, function: FunctionInfo) {
        debug!("MiddleWare Route added for {} {} ", route_type, route);
        self.middleware_router
            .add_route(route_type, route, function, None)
            .unwrap();
    }

    /// Add a new web socket route to the routing tables
    /// can be called after the server has been started
    pub fn add_web_socket_route(
        &mut self,
        route: &str,
        connect_route: FunctionInfo,
        close_route: FunctionInfo,
        message_route: FunctionInfo,
    ) {
        self.websocket_router
            .add_websocket_route(route, connect_route, close_route, message_route);
    }

    /// Add a new startup handler
    pub fn add_startup_handler(&mut self, function: FunctionInfo) {
        debug!("Adding startup handler");
        self.startup_handler = Some(Arc::new(function));
        debug!("{:?}", self.startup_handler);
    }

    /// Add a new shutdown handler
    pub fn add_shutdown_handler(&mut self, function: FunctionInfo) {
        debug!("Adding shutdown handler:");
        self.shutdown_handler = Some(Arc::new(function));
        debug!("{:?}", self.shutdown_handler);
    }
}

impl Default for Server {
    fn default() -> Self {
        Self::new()
    }
}

async fn apply_middleware(
    request: &mut Request,
    middleware_type: MiddlewareRoute,
    middleware_router: &MiddlewareRouter,
    route_uri: &str,
) {
    let mut modified_request = match middleware_router.get_route(&middleware_type, route_uri) {
        Some((function, route_params)) => {
            request.params = route_params;
            execute_middleware_function(request, function)
                .await
                .unwrap_or_default()
        }
        None => HashMap::new(),
    };

    debug!("This is the modified request {:?}", modified_request);

    if modified_request.contains_key("headers") {
        request.headers = modified_request.remove("headers").unwrap();
    }

    debug!("These are the request headers {:?}", &request.headers);
}

/// This is our service handler. It receives a Request, routes on it
/// path, and returns a Future of a Response.
async fn index(
    router: web::Data<Arc<HttpRouter>>,
    const_router: web::Data<Arc<ConstRouter>>,
    middleware_router: web::Data<Arc<MiddlewareRouter>>,
    global_request_headers: web::Data<Arc<Headers>>,
    body: Bytes,
    req: HttpRequest,
) -> impl Responder {
    let mut request = Request::from_actix_request(&req, body);

    apply_middleware(
        &mut request,
        MiddlewareRoute::BeforeRequest,
        &middleware_router,
        req.uri().path(),
    )
    .await;

    let mut response_builder = HttpResponse::Ok();
    apply_dashmap_headers(&mut response_builder, &global_request_headers);
    apply_hashmap_headers(&mut response_builder, &request.headers);

    let response = if let Some(r) = const_router.get_route(req.method(), req.uri().path()) {
        apply_hashmap_headers(&mut response_builder, &r.headers);
        response_builder
            .status(StatusCode::from_u16(r.status_code).unwrap())
            .body(r.body)
    } else if let Some((function, route_params)) = router.get_route(req.method(), req.uri().path())
    {
        request.params = route_params;
        match execute_http_function(&request, function).await {
            Ok(r) => {
                response_builder.status(StatusCode::from_u16(r.status_code).unwrap());
                apply_hashmap_headers(&mut response_builder, &r.headers);
                if !r.body.is_empty() {
                    response_builder.body(r.body)
                } else {
                    response_builder.finish()
                }
            }
            Err(e) => {
                debug!("Error: {:?}", e);
                response_builder.status(StatusCode::INTERNAL_SERVER_ERROR);
                response_builder.finish()
            }
        }
    } else {
        response_builder.status(StatusCode::NOT_FOUND);
        response_builder.body("Not found")
    };

    apply_middleware(
        &mut request,
        MiddlewareRoute::AfterRequest,
        &middleware_router,
        req.uri().path(),
    )
    .await;

    debug!("Response: {:?}", response);

    response
}
