use crate::executors::{
    execute_after_middleware_function, execute_http_function, execute_middleware_function,
    execute_startup_handler,
};

use crate::routers::const_router::ConstRouter;
use crate::routers::Router;

use crate::routers::http_router::HttpRouter;
use crate::routers::{middleware_router::MiddlewareRouter, web_socket_router::WebSocketRouter};
use crate::shared_socket::SocketHeld;
use crate::types::cookie::Cookies;
use crate::types::function_info::{FunctionInfo, MiddlewareType};
use crate::types::headers::Headers;
use crate::types::request::Request;
use crate::types::response::{Response, ResponseType};
use crate::types::HttpMethod;
use crate::types::MiddlewareReturn;
use crate::websockets::start_web_socket;

use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering::{Relaxed, SeqCst};
use std::sync::{Arc, RwLock};

use std::process::exit;
use std::{env, thread};

use actix_files::Files;
use actix_http::KeepAlive;
use actix_web::*;

use log::error;
use once_cell::sync::OnceCell;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::pycell::PyRef;
use pyo3_async_runtimes::TaskLocals;

const MAX_PAYLOAD_SIZE: &str = "ROBYN_MAX_PAYLOAD_SIZE";
const DEFAULT_MAX_PAYLOAD_SIZE: usize = 1_000_000; // 1Mb

static STARTED: AtomicBool = AtomicBool::new(false);

#[derive(Clone)]
struct Directory {
    route: String,
    directory_path: String,
    show_files_listing: bool,
    index_file: Option<String>,
}

#[pyclass]
pub struct Server {
    router: Arc<HttpRouter>,
    const_router: Arc<ConstRouter>,
    websocket_router: Arc<WebSocketRouter>,
    middleware_router: Arc<MiddlewareRouter>,
    global_request_headers: Arc<Headers>,
    global_response_headers: Arc<Headers>,
    directories: Arc<RwLock<Vec<Directory>>>,
    startup_handler: Option<Arc<FunctionInfo>>,
    shutdown_handler: Option<Arc<FunctionInfo>>,
    excluded_response_headers_paths: Option<Vec<String>>,
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
            global_request_headers: Arc::new(Headers::new(None)),
            global_response_headers: Arc::new(Headers::new(None)),
            directories: Arc::new(RwLock::new(Vec::new())),
            startup_handler: None,
            shutdown_handler: None,
            excluded_response_headers_paths: None,
        }
    }

    pub fn start(
        &mut self,
        _py: Python,
        socket: PyRef<SocketHeld>,
        workers: usize,
    ) -> PyResult<()> {
        pyo3_log::init();

        static TASK_LOCALS: OnceCell<TaskLocals> = OnceCell::new();

        if STARTED
            .compare_exchange(false, true, SeqCst, Relaxed)
            .is_err()
        {
            return Ok(());
        }

        let raw_socket = socket.get_socket();

        let router = Arc::clone(&self.router);
        let const_router = Arc::clone(&self.const_router);
        let middleware_router = Arc::clone(&self.middleware_router);
        let web_socket_router = Arc::clone(&self.websocket_router);
        let global_request_headers = Arc::clone(&self.global_request_headers);
        let global_response_headers = Arc::clone(&self.global_response_headers);
        let directories = Arc::clone(&self.directories);

        let asyncio = _py.import("asyncio")?;
        let event_loop = asyncio.call_method0("new_event_loop")?;
        asyncio.call_method1("set_event_loop", (event_loop.clone(),))?;

        let startup_handler = self.startup_handler.clone();
        let shutdown_handler = self.shutdown_handler.clone();

        let excluded_response_headers_paths = self.excluded_response_headers_paths.clone();

        let _ = TASK_LOCALS.get_or_try_init(|| {
            Python::with_gil(|py| {
                pyo3_async_runtimes::TaskLocals::new(event_loop.clone().into()).copy_context(py)
            })
        });

        let max_payload_size = env::var(MAX_PAYLOAD_SIZE)
            .unwrap_or(DEFAULT_MAX_PAYLOAD_SIZE.to_string())
            .trim()
            .parse::<usize>()
            .map_err(|e| {
                PyValueError::new_err(format!(
                    "Failed to parse environment variable {MAX_PAYLOAD_SIZE} - {e}"
                ))
            })?;

        thread::spawn(move || {
            actix_web::rt::System::new().block_on(async move {
                let task_locals = Python::with_gil(|py| TASK_LOCALS.get().unwrap().clone_ref(py));
                execute_startup_handler(startup_handler, &task_locals)
                    .await
                    .unwrap();

                if !middleware_router.has_any_middleware() {
                    const_router.bake_global_headers(&global_response_headers);
                }

                HttpServer::new(move || {
                    let mut app = App::new();

                    let directories = directories.read().unwrap();

                    // this loop matches three types of directory serving
                    // 1. Serves a build folder. e.g. the build folder generated from yarn build
                    // 2. Shows file listing
                    // 3. Just serves the file without any redirection to sub links
                    for directory in directories.iter() {
                        let mut files = Files::new(&directory.route, &directory.directory_path)
                            .method_guard(guard::fn_guard(|_| true))
                            .redirect_to_slash_directory();
                        if let Some(index_file) = &directory.index_file {
                            files = files.index_file(index_file);
                        } else if directory.show_files_listing {
                            files = files.show_files_listing();
                        } else {
                            // To serve regular files only, nothing else.
                            let directory_path = directory.directory_path.clone();
                            let directory_route = directory.route.clone();
                            // This guard allows request if it corresponds to a regular file.
                            files = files.guard(guard::fn_guard(move |ctx| {
                                let route = ctx.head().uri.path();
                                // Resolve the path by combining directory path and requested path
                                let full_path = std::path::Path::new(&directory_path).join(
                                    route
                                        .trim_start_matches(&directory_route)
                                        .trim_start_matches("/"),
                                );
                                // Check if the path exists and is a regular file (not dir/symlink)
                                if let Ok(metadata) = std::fs::metadata(&full_path) {
                                    metadata.is_file()
                                } else {
                                    false
                                }
                            }));
                        }
                        app = app.service(files);
                    }

                    app = app
                        .app_data(web::Data::new(Arc::clone(&router)))
                        .app_data(web::Data::new(Arc::clone(&const_router)))
                        .app_data(web::Data::new(Arc::clone(&middleware_router)))
                        .app_data(web::Data::new(Arc::clone(&global_request_headers)))
                        .app_data(web::Data::new(Arc::clone(&global_response_headers)))
                        .app_data(web::Data::new(excluded_response_headers_paths.clone()));

                    let web_socket_map = web_socket_router.get_web_socket_map();
                    for (elem, value) in (web_socket_map.read()).iter() {
                        let endpoint = elem.clone();
                        let path_params = value.clone();
                        let endpoint_for_closure = endpoint.clone();
                        app = app.route(
                            &endpoint,
                            web::get().to(move |stream: web::Payload, req: HttpRequest| {
                                let endpoint_copy = endpoint_for_closure.clone();
                                let task_locals =
                                    Python::with_gil(|py| TASK_LOCALS.get().unwrap().clone_ref(py));
                                start_web_socket(
                                    req,
                                    stream,
                                    path_params.clone(),
                                    task_locals,
                                    endpoint_copy.to_string(),
                                    max_payload_size,
                                )
                            }),
                        );
                    }

                    app.app_data(web::PayloadConfig::new(max_payload_size))
                        .default_service(web::route().to(
                            move |router: web::Data<Arc<HttpRouter>>,
                                  const_router: web::Data<Arc<ConstRouter>>,
                                  middleware_router: web::Data<Arc<MiddlewareRouter>>,
                                  payload: web::Payload,
                                  global_request_headers: web::Data<Arc<Headers>>,
                                  global_response_headers: web::Data<Arc<Headers>>,
                                  response_headers_exclude_paths: web::Data<
                                Option<Vec<String>>,
                            >,
                                  req: HttpRequest| async move {
                                // Fast path: const routes bypass request parsing, Python, and middleware
                                // Only safe when no middlewares are registered (checked dynamically via AtomicBool)
                                if !middleware_router.has_any_middleware() {
                                    if let Ok(http_method) =
                                        HttpMethod::from_actix_method(req.method())
                                    {
                                        if let Some(cached) = const_router
                                            .get_cached_route(&http_method, req.uri().path())
                                        {
                                            if let Some(ref excluded) =
                                                *response_headers_exclude_paths.get_ref()
                                            {
                                                if excluded.contains(&req.uri().path().to_owned()) {
                                                    return cached
                                                        .to_http_response_without_global_headers();
                                                }
                                            }
                                            return cached.to_http_response();
                                        }
                                    }
                                }

                                // Normal path: dynamic routes (and const routes when middlewares exist) require Python
                                let req_ref = req.clone();
                                let task_locals =
                                    Python::with_gil(|py| TASK_LOCALS.get().unwrap().clone_ref(py));
                                let response = pyo3_async_runtimes::tokio::scope_local(
                                    task_locals,
                                    async move {
                                        index(
                                            router,
                                            const_router,
                                            payload,
                                            middleware_router,
                                            global_request_headers,
                                            global_response_headers,
                                            response_headers_exclude_paths,
                                            req,
                                        )
                                        .await
                                    },
                                )
                                .await;
                                response.respond_to(&req_ref)
                            },
                        ))
                })
                .keep_alive(KeepAlive::Os)
                .workers(workers)
                .client_request_timeout(std::time::Duration::from_secs(0))
                .listen(raw_socket.into())
                .unwrap()
                .run()
                .await
                .unwrap();
            });
        });

        let event_loop = event_loop.call_method0("run_forever");
        if event_loop.is_err() {
            if let Some(function) = shutdown_handler {
                if function.is_async {
                    let task_locals =
                        Python::with_gil(|py| TASK_LOCALS.get().unwrap().clone_ref(py));

                    pyo3_async_runtimes::tokio::run_until_complete(
                        task_locals.event_loop(_py),
                        pyo3_async_runtimes::into_future_with_locals(
                            &task_locals.clone_ref(_py),
                            function.handler.bind(_py).call0()?,
                        )
                        .unwrap(),
                    )
                    .unwrap();
                } else {
                    Python::with_gil(|py| function.handler.call0(py))?;
                }
            }

            exit(0);
        }
        Ok(())
    }

    pub fn add_directory(
        &mut self,
        route: String,
        directory_path: String,
        show_files_listing: bool,
        index_file: Option<String>,
    ) {
        self.directories.write().unwrap().push(Directory {
            route,
            directory_path,
            show_files_listing,
            index_file,
        });
    }

    /// Removes a new request header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn remove_header(&self, key: &str) {
        self.global_request_headers.headers.remove(key);
    }

    /// Removes a new response header to our concurrent hashmap
    /// this can be called after the server has started.
    pub fn remove_response_header(&self, key: &str) {
        self.global_response_headers.headers.remove(key);
    }

    pub fn apply_request_headers(&mut self, headers: &Headers) {
        self.global_request_headers = Arc::new(headers.clone());
    }

    pub fn apply_response_headers(&mut self, headers: &Headers) {
        self.global_response_headers = Arc::new(headers.clone());
    }

    pub fn set_response_headers_exclude_paths(
        &mut self,
        excluded_response_headers_paths: Option<Vec<String>>,
    ) {
        self.excluded_response_headers_paths = excluded_response_headers_paths;
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_route(
        &self,
        py: Python,
        route_type: &HttpMethod,
        route: &str,
        function: FunctionInfo,
        is_const: bool,
    ) {
        self._add_route(py, route_type, route, &function, is_const);
    }

    fn _add_route(
        &self,
        py: Python,
        route_type: &HttpMethod,
        route: &str,
        function: &FunctionInfo,
        is_const: bool,
    ) {
        let asyncio = py.import("asyncio").unwrap();
        let event_loop = asyncio.call_method0("get_event_loop").unwrap();

        if is_const {
            match self.const_router.add_route(
                py,
                route_type,
                route,
                function.clone(),
                Some(event_loop),
            ) {
                Ok(_) => (),
                Err(e) => {
                    log::debug!("Error adding const route {}", e);
                }
            }
        } else {
            match self
                .router
                .add_route(py, route_type, route, function.clone(), None)
            {
                Ok(_) => (),
                Err(e) => {
                    log::debug!("Error adding route {}", e);
                }
            }
        }
    }

    /// Add a new global middleware
    /// can be called after the server has been started
    pub fn add_global_middleware(&self, middleware_type: &MiddlewareType, function: FunctionInfo) {
        self.middleware_router
            .add_global_middleware(middleware_type, function)
            .unwrap();
    }

    /// Add a new route to the routing tables
    /// can be called after the server has been started
    pub fn add_middleware_route(
        &self,
        middleware_type: &MiddlewareType,
        route: &str,
        function: FunctionInfo,
        http_method: HttpMethod,
    ) {
        let mut endpoint_prefixed_with_method = http_method.to_string();

        if !route.starts_with('/') {
            endpoint_prefixed_with_method.push('/');
        }

        endpoint_prefixed_with_method.push_str(route);

        Python::with_gil(|py| {
            self.middleware_router
                .add_route(
                    py,
                    middleware_type,
                    &endpoint_prefixed_with_method,
                    function,
                    None,
                )
                .unwrap()
        });
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
        self.startup_handler = Some(Arc::new(function));
    }

    /// Add a new shutdown handler
    pub fn add_shutdown_handler(&mut self, function: FunctionInfo) {
        self.shutdown_handler = Some(Arc::new(function));
    }
}

impl Default for Server {
    fn default() -> Self {
        Self::new()
    }
}

async fn index(
    router: web::Data<Arc<HttpRouter>>,
    const_router: web::Data<Arc<ConstRouter>>,
    payload: web::Payload,
    middleware_router: web::Data<Arc<MiddlewareRouter>>,
    global_request_headers: web::Data<Arc<Headers>>,
    global_response_headers: web::Data<Arc<Headers>>,
    excluded_response_headers_paths: web::Data<Option<Vec<String>>>,
    req: HttpRequest,
) -> ResponseType {
    if !HttpMethod::is_supported(req.method()) {
        return ResponseType::Standard(Response::method_not_allowed(None));
    }

    let http_method = match HttpMethod::from_actix_method(req.method()) {
        Ok(method) => method,
        Err(_) => return ResponseType::Standard(Response::method_not_allowed(None)),
    };

    let mut request: Request =
        match Request::from_actix_request(&req, payload, &global_request_headers).await {
            Ok(r) => r,
            Err(e) => {
                error!("Failed to parse request for `{}`: {}", req.path(), e);
                return ResponseType::Standard(Response::internal_server_error(None));
            }
        };

    let route = format!("{}{}", req.method(), request.url.path);

    // Allocate a single `contextvars.Context` for the full request lifecycle so
    // that writes made by a `before_request` hook are visible to the route
    // handler and to `after_request` hooks. asyncio copies the current context
    // for each task it creates, so without this shared object each phase would
    // see its own isolated snapshot (see issue #1380).
    //
    // This also provides per-request ContextVar isolation for sync handlers
    // (which run via `ctx.run(...)`): without a fresh context, a `ContextVar`
    // written inside a handler would persist in the worker thread's current
    // context and leak into the next request on that thread.
    let request_context: Py<PyAny> = match Python::with_gil(crate::asyncio::new_context) {
        Ok(ctx) => ctx,
        Err(e) => {
            error!("Failed to create request contextvars context: {}", e);
            return ResponseType::Standard(Response::internal_server_error(None));
        }
    };
    let ctx_ref = Some(&request_context);

    // Before middleware
    let before_middlewares =
        middleware_router.get_global_middlewares(&MiddlewareType::BeforeRequest);
    let route_before = middleware_router.get_route(&MiddlewareType::BeforeRequest, &route);

    let mut early_response: Option<Response> = None;
    if !before_middlewares.is_empty() || route_before.is_some() {
        let mut all_before = before_middlewares;
        if let Some((function, route_params)) = route_before {
            all_before.push(function);
            request.path_params = route_params;
        }
        for before_middleware in all_before {
            request = match execute_middleware_function(&request, &before_middleware, ctx_ref).await
            {
                Ok(MiddlewareReturn::Request(r)) => r,
                Ok(MiddlewareReturn::Response(r)) => {
                    early_response = Some(r);
                    break;
                }
                Err(e) => {
                    let msg = match e.downcast_ref::<PyErr>() {
                        Some(py_err) => get_traceback(py_err),
                        None => format!("{e:?}"),
                    };
                    error!(
                        "Error executing before middleware for `{}`: {}",
                        request.url.path, msg
                    );
                    return ResponseType::Standard(Response::internal_server_error(None));
                }
            };
        }
    }

    let mut response = if let Some(r) = early_response {
        ResponseType::Standard(r)
    } else if let Some(cached) = const_router.get_cached_route(&http_method, &request.url.path) {
        let mut resp = Response {
            status_code: cached.status.as_u16(),
            response_type: "text".to_string(),
            headers: Headers::new(None),
            description: cached.body.to_vec(),
            file_path: None,
            cookies: Cookies::new(),
        };
        for (k, v) in cached.headers.as_ref() {
            resp.headers.set(k.clone(), v.clone());
        }
        ResponseType::Standard(resp)
    } else if let Some((function, route_params)) = router.get_route(&http_method, &request.url.path)
    {
        request.path_params = route_params;
        match execute_http_function(&request, &function, ctx_ref).await {
            Ok(r) => r,
            Err(e) => {
                error!(
                    "Error executing route function for `{}`: {}",
                    request.url.path,
                    get_traceback(&e)
                );
                ResponseType::Standard(Response::internal_server_error(None))
            }
        }
    } else {
        ResponseType::Standard(Response::not_found(None))
    };

    let is_excluded = excluded_response_headers_paths
        .get_ref()
        .as_ref()
        .is_some_and(|paths| paths.contains(&request.url.path));

    if !is_excluded {
        response.headers_mut().set_missing(&global_response_headers);
    }

    // After middleware
    let after_middlewares = middleware_router.get_global_middlewares(&MiddlewareType::AfterRequest);
    let route_after = middleware_router.get_route(&MiddlewareType::AfterRequest, &route);

    if !after_middlewares.is_empty() || route_after.is_some() {
        let mut all_after = after_middlewares;
        if let Some((function, _)) = route_after {
            all_after.push(function);
        }
        for after_middleware in all_after {
            if let ResponseType::Standard(std_response) = response {
                response = match execute_after_middleware_function(
                    &request,
                    &std_response,
                    &after_middleware,
                    ctx_ref,
                )
                .await
                {
                    Ok(MiddlewareReturn::Request(_)) => {
                        error!("After middleware returned a request");
                        return ResponseType::Standard(Response::internal_server_error(None));
                    }
                    Ok(MiddlewareReturn::Response(r)) => ResponseType::Standard(r),
                    Err(e) => {
                        let msg = match e.downcast_ref::<PyErr>() {
                            Some(py_err) => get_traceback(py_err),
                            None => format!("{e:?}"),
                        };
                        error!(
                            "Error executing after middleware for `{}`: {}",
                            request.url.path, msg
                        );
                        return ResponseType::Standard(Response::internal_server_error(Some(
                            &std_response.headers,
                        )));
                    }
                };
            }
        }
    }

    response
}

fn get_traceback(error: &PyErr) -> String {
    Python::with_gil(|py| -> String {
        if let Some(traceback) = error.traceback(py) {
            let msg = match traceback.format() {
                Ok(msg) => format!("\n{msg} {error}"),
                Err(e) => e.to_string(),
            };
            return msg;
        };

        error.value(py).to_string()
    })
}
