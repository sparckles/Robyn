use crate::executors::execute_event_handler;
use crate::io_helpers::apply_headers;
use crate::request_handler::{handle_http_middleware_request, handle_http_request};

use crate::routers::const_router::ConstRouter;
use crate::routers::router::Router;
use crate::routers::{middleware_router::MiddlewareRouter, web_socket_router::WebSocketRouter};
use crate::shared_socket::SocketHeld;
use crate::types::{Headers, PyFunction};
use crate::web_socket_connection::start_web_socket;

use std::cell::RefCell;
use std::collections::HashMap;
use std::convert::TryInto;
use std::rc::Rc;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering::{Relaxed, SeqCst};
use std::sync::{Arc, RwLock};

use std::thread;

use actix_files::Files;
use actix_http::header::HeaderMap;
use actix_http::KeepAlive;
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
    router: Arc<Router>,
    const_router: Arc<ConstRouter>,
    websocket_router: Arc<WebSocketRouter>,
    middleware_router: Arc<MiddlewareRouter>,
    global_headers: Arc<DashMap<String, String>>,
    directories: Arc<RwLock<Vec<Directory>>>,
    startup_handler: Option<Arc<PyFunction>>,
    shutdown_handler: Option<Arc<PyFunction>>,
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            router: Arc::new(Router::new()),
            const_router: Arc::new(ConstRouter::new()),
            websocket_router: Arc::new(WebSocketRouter::new()),
            middleware_router: Arc::new(MiddlewareRouter::new()),
            global_headers: Arc::new(DashMap::new()),
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

        let borrow = socket.try_borrow_mut()?;
        let held_socket: &SocketHeld = &*borrow;

        let raw_socket = held_socket.get_socket();

        let router = self.router.clone();
        let const_router = self.const_router.clone();
        let middleware_router = self.middleware_router.clone();
        let web_socket_router = self.websocket_router.clone();
        let global_headers = self.global_headers.clone();
        let directories = self.directories.clone();
        let workers = Arc::new(workers);

        let asyncio = py.import("asyncio").unwrap();

        let event_loop = asyncio.call_method0("new_event_loop").unwrap();
        asyncio
            .call_method1("set_event_loop", (event_loop,))
            .unwrap();
        let event_loop_hdl = Arc::new(PyObject::from(event_loop));
        let event_loop_cleanup = event_loop_hdl.clone();
        let startup_handler = self.startup_handler.clone();
        let shutdown_handler = self.shutdown_handler.clone();

        thread::spawn(move || {
            //init_current_thread_once();
            let copied_event_loop = event_loop_hdl.clone();
            actix_web::rt::System::new().block_on(async move {
                debug!("The number of workers are {}", workers.clone());
                execute_event_handler(startup_handler, copied_event_loop.clone())
                    .await
                    .unwrap();

                HttpServer::new(move || {
                    let mut app = App::new();
                    let event_loop_hdl = copied_event_loop.clone();
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
                        .app_data(web::Data::new(global_headers.clone()));

                    let web_socket_map = web_socket_router.get_web_socket_map();
                    for (elem, value) in (web_socket_map.read().unwrap()).iter() {
                        let route = elem.clone();
                        let params = value.clone();
                        let event_loop_hdl = event_loop_hdl.clone();
                        app = app.route(
                            &route.clone(),
                            web::get().to(
                                move |_router: web::Data<Arc<Router>>,
                                      _global_headers: web::Data<Arc<Headers>>,
                                      stream: web::Payload,
                                      req: HttpRequest| {
                                    start_web_socket(
                                        req,
                                        stream,
                                        params.clone(),
                                        event_loop_hdl.clone(),
                                    )
                                },
                            ),
                        );
                    }

                    app.default_service(web::route().to(
                        move |router,
                              const_router: web::Data<Arc<ConstRouter>>,
                              middleware_router: web::Data<Arc<MiddlewareRouter>>,
                              global_headers,
                              payload,
                              req| {
                            pyo3_asyncio::tokio::scope_local(
                                (*event_loop_hdl).clone(),
                                async move {
                                    index(
                                        router,
                                        const_router,
                                        middleware_router,
                                        global_headers,
                                        payload,
                                        req,
                                    )
                                    .await
                                },
                            )
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
                let event_loop_hdl = event_loop_cleanup.clone();
                pyo3_asyncio::tokio::run(py, async move {
                    execute_event_handler(shutdown_handler, event_loop_hdl.clone())
                        .await
                        .unwrap();
                    Ok(())
                })
                .unwrap();
            })
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
    pub fn add_header(&self, key: &str, value: &str) {
        self.global_headers
            .insert(key.to_string(), value.to_string());
    }

    /// Removes a new header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn remove_header(&self, key: &str) {
        self.global_headers.remove(key);
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    #[allow(clippy::too_many_arguments)]
    pub fn add_route(
        &self,
        py: Python,
        route_type: &str,
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
        const_route: bool,
    ) {
        debug!("Route added for {} {} ", route_type, route);
        // let event_loop = pyo3_asyncio::tokio::get_current_loop(py).unwrap();
        let asyncio = py.import("asyncio").unwrap();
        let event_loop = asyncio.call_method0("get_event_loop").unwrap();

        if const_route {
            self.const_router
                .add_route(
                    route_type,
                    route,
                    handler,
                    is_async,
                    number_of_params,
                    event_loop,
                )
                .unwrap();
        } else {
            self.router
                .add_route(route_type, route, handler, is_async, number_of_params)
                .unwrap();
        }
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_middleware_route(
        &self,
        route_type: &str,
        route: &str,
        handler: Py<PyAny>,
        is_async: bool,
        number_of_params: u8,
    ) {
        debug!("MiddleWare Route added for {} {} ", route_type, route);
        self.middleware_router
            .add_route(route_type, route, handler, is_async, number_of_params)
            .unwrap();
    }

    /// Add a new web socket route to the routing tables
    /// can be called after the server has been started
    pub fn add_web_socket_route(
        &mut self,
        route: &str,
        // handler, is_async, number of params
        connect_route: (Py<PyAny>, bool, u8),
        close_route: (Py<PyAny>, bool, u8),
        message_route: (Py<PyAny>, bool, u8),
    ) {
        self.websocket_router
            .add_websocket_route(route, connect_route, close_route, message_route);
    }

    /// Add a new startup handler
    pub fn add_startup_handler(&mut self, handler: Py<PyAny>, is_async: bool) {
        debug!("Adding startup handler");
        match is_async {
            true => self.startup_handler = Some(Arc::new(PyFunction::CoRoutine(handler))),
            false => self.startup_handler = Some(Arc::new(PyFunction::SyncFunction(handler))),
        };
        debug!("{:?}", self.startup_handler);
    }

    /// Add a new shutdown handler
    pub fn add_shutdown_handler(&mut self, handler: Py<PyAny>, is_async: bool) {
        debug!("Adding shutdown handler");
        match is_async {
            true => self.shutdown_handler = Some(Arc::new(PyFunction::CoRoutine(handler))),
            false => self.shutdown_handler = Some(Arc::new(PyFunction::SyncFunction(handler))),
        };
        debug!("{:?}", self.startup_handler);
        debug!("{:?}", self.shutdown_handler);
    }
}

impl Default for Server {
    fn default() -> Self {
        Self::new()
    }
}

async fn merge_headers(
    global_headers: &Arc<Headers>,
    request_headers: &HeaderMap,
) -> HashMap<String, String> {
    let mut headers = HashMap::new();

    for elem in (global_headers).iter() {
        headers.insert(elem.key().clone(), elem.value().clone());
    }

    for (key, value) in (request_headers).iter() {
        headers.insert(
            key.to_string().clone(),
            // test if this crashes or not
            value.to_str().unwrap().to_string().clone(),
        );
    }

    headers
}

/// This is our service handler. It receives a Request, routes on it
/// path, and returns a Future of a Response.
async fn index(
    router: web::Data<Arc<Router>>,
    const_router: web::Data<Arc<ConstRouter>>,
    middleware_router: web::Data<Arc<MiddlewareRouter>>,
    global_headers: web::Data<Arc<Headers>>,
    mut payload: web::Payload,
    req: HttpRequest,
) -> impl Responder {
    let queries = Rc::new(RefCell::new(HashMap::new()));

    if !req.query_string().is_empty() {
        let split = req.query_string().split('&');
        for s in split {
            let params = s.split_once('=').unwrap_or((s, ""));
            queries
                .borrow_mut()
                .insert(params.0.to_string(), params.1.to_string());
        }
    }

    let headers = merge_headers(&global_headers, req.headers()).await;

    // need a better name for this
    let tuple_params = match middleware_router.get_route("BEFORE_REQUEST", req.uri().path()) {
        Some(((handler_function, number_of_params), route_params)) => {
            let x = handle_http_middleware_request(
                handler_function,
                number_of_params,
                &headers,
                &mut payload,
                &req,
                route_params,
                queries.clone(),
            )
            .await;
            debug!("Middleware contents {:?}", x);
            x
        }
        None => HashMap::new(),
    };

    debug!("These are the tuple params {:?}", tuple_params);

    let headers_dup = if !tuple_params.is_empty() {
        tuple_params.get("headers").unwrap().clone()
    } else {
        headers
    };

    debug!("These are the request headers {:?}", headers_dup);

    let response = if const_router
        .get_route(req.method().clone(), req.uri().path())
        .is_some()
    {
        let mut response = HttpResponse::Ok();
        apply_headers(&mut response, headers_dup.clone());
        response.body(
            const_router
                .get_route(req.method().clone(), req.uri().path())
                .unwrap(),
        )
    } else {
        match router.get_route(req.method().clone(), req.uri().path()) {
            Some(((handler_function, number_of_params), route_params)) => {
                handle_http_request(
                    handler_function,
                    number_of_params,
                    headers_dup.clone(),
                    &mut payload,
                    &req,
                    route_params,
                    queries.clone(),
                )
                .await
            }
            None => {
                let mut response = HttpResponse::Ok();
                apply_headers(&mut response, headers_dup.clone());
                response.finish()
            }
        }
    };

    match middleware_router.get_route("AFTER_REQUEST", req.uri().path()) {
        Some(((handler_function, number_of_params), route_params)) => {
            let x = handle_http_middleware_request(
                handler_function,
                number_of_params,
                &headers_dup,
                &mut payload,
                &req,
                route_params,
                queries.clone(),
            )
            .await;
            debug!("{:?}", x);
        }
        None => {}
    };

    response
}
