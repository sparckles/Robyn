pub mod registry;

use crate::executors::web_socket_executors::execute_ws_function;
use crate::types::function_info::FunctionInfo;
use crate::types::multimap::QueryParams;
use registry::{Close, SendMessageToAll, SendText};

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use once_cell::sync::OnceCell;
use parking_lot::RwLock;
use pyo3::prelude::*;
use pyo3::IntoPyObject;
use pyo3_async_runtimes::TaskLocals;
use std::sync::Arc;
use tokio::sync::mpsc;
use uuid::Uuid;

use crate::runtime;

use registry::{Register, WebSocketRegistry};
use std::collections::HashMap;

/// A Rust-backed channel receiver exposed to Python.
/// Python handlers call `await channel.receive()` to get the next message.
/// Returns the message string, or None when the connection is closed.
#[pyclass]
pub struct WebSocketChannel {
    receiver: Arc<tokio::sync::Mutex<mpsc::UnboundedReceiver<Option<String>>>>,
}

#[pymethods]
impl WebSocketChannel {
    /// Await the next message from the WebSocket.
    /// Returns the message string, or None if the connection was closed.
    fn receive<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let receiver = self.receiver.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut rx = receiver.lock().await;
            match rx.recv().await {
                Some(Some(msg)) => Ok(Some(msg)),
                Some(None) | None => Ok(None),
            }
        })
    }
}

/// Define HTTP actor
#[pyclass]
pub struct WebSocketConnector {
    pub id: Uuid,
    pub router: HashMap<String, FunctionInfo>,
    pub task_locals: TaskLocals,
    pub registry_addr: Addr<WebSocketRegistry>,
    pub query_params: QueryParams,
    /// Sender side of the message channel (stays in the Actix actor).
    pub message_sender: Option<mpsc::UnboundedSender<Option<String>>>,
    /// Receiver side exposed to Python via WebSocketChannel.
    pub message_channel: Option<Py<WebSocketChannel>>,
}

// By default mailbox capacity is 16 messages.
impl Actor for WebSocketConnector {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let addr = ctx.address();
        self.registry_addr.do_send(Register {
            id: self.id,
            addr: addr.clone(),
        });

        let (tx, rx) = mpsc::unbounded_channel::<Option<String>>();
        self.message_sender = Some(tx);
        self.message_channel = Python::with_gil(|py| {
            Some(
                Py::new(
                    py,
                    WebSocketChannel {
                        receiver: Arc::new(tokio::sync::Mutex::new(rx)),
                    },
                )
                .unwrap(),
            )
        });

        let function = self.router.get("connect").unwrap();
        execute_ws_function(function, &self.task_locals, ctx, self);

        debug!("Actor is alive");
    }

    fn stopped(&mut self, ctx: &mut Self::Context) {
        // Drop the sender to close the channel.
        // This causes any pending `channel.receive()` in Python to return None,
        // which the WebSocketAdapter converts to WebSocketDisconnect.
        self.message_sender.take();

        let function = self.router.get("close").unwrap();
        execute_ws_function(function, &self.task_locals, ctx, self);
        debug!("Actor is dead");
    }
}

impl Clone for WebSocketConnector {
    fn clone(&self) -> Self {
        let task_locals_clone = Python::with_gil(|py| self.task_locals.clone_ref(py));

        Self {
            id: self.id,
            router: self.router.clone(),
            task_locals: task_locals_clone,
            registry_addr: self.registry_addr.clone(),
            query_params: self.query_params.clone(),
            message_sender: self.message_sender.clone(),
            message_channel: Python::with_gil(|py| {
                self.message_channel.as_ref().map(|c| c.clone_ref(py))
            }),
        }
    }
}

impl Handler<SendText> for WebSocketConnector {
    type Result = ();

    fn handle(&mut self, msg: SendText, ctx: &mut Self::Context) {
        if self.id == msg.recipient_id {
            ctx.text(msg.message.clone());
            if msg.message == "Connection closed" {
                // Close the WebSocket connection
                ctx.stop();
            }
        }
    }
}

/// Handler for ws::Message message
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for WebSocketConnector {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                debug!("Ping message {:?}", msg);
                ctx.pong(&msg)
            }
            Ok(ws::Message::Pong(msg)) => {
                debug!("Pong message {:?}", msg);
            }
            Ok(ws::Message::Text(text)) => {
                debug!("Text message received {:?}", text);
                if let Some(ref sender) = self.message_sender {
                    let _ = sender.send(Some(text.to_string()));
                }
            }
            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(_close_reason)) => {
                debug!("Socket was closed");
                // Drop sender to signal channel closure so receive() returns None.
                // The close handler is called once from stopped().
                self.message_sender.take();
                ctx.stop();
            }
            _ => (),
        }
    }
}

#[pymethods]
impl WebSocketConnector {
    pub fn sync_send_to(&self, recipient_id: String, message: String) {
        let recipient_id = Uuid::parse_str(&recipient_id).unwrap();

        match self.registry_addr.try_send(SendText {
            message,
            sender_id: self.id,
            recipient_id,
        }) {
            Ok(_) => println!("Message sent successfully"),
            Err(e) => println!("Failed to send message: {}", e),
        }
    }

    pub fn async_send_to(
        &self,
        py: Python,
        recipient_id: String,
        message: String,
    ) -> PyResult<Py<PyAny>> {
        let registry = self.registry_addr.clone();
        let recipient_id = Uuid::parse_str(&recipient_id).unwrap();
        let sender_id = self.id;

        let awaitable = runtime::future_into_py(py, async move {
            match registry.try_send(SendText {
                message,
                sender_id,
                recipient_id,
            }) {
                Ok(_) => println!("Message sent successfully"),
                Err(e) => println!("Failed to send message: {}", e),
            }
            Ok(())
        })?;

        Ok(awaitable.into_pyobject(py)?.into_any().into())
    }

    pub fn sync_broadcast(&self, message: String) {
        let registry = self.registry_addr.clone();
        match registry.try_send(SendMessageToAll {
            message,
            sender_id: self.id,
        }) {
            Ok(_) => println!("Message sent successfully"),
            Err(e) => println!("Failed to send message: {}", e),
        }
    }

    pub fn async_broadcast(&self, py: Python, message: String) -> PyResult<Py<PyAny>> {
        let registry = self.registry_addr.clone();
        let sender_id = self.id;

        let awaitable = runtime::future_into_py(py, async move {
            match registry.try_send(SendMessageToAll { message, sender_id }) {
                Ok(_) => println!("Message sent successfully"),
                Err(e) => println!("Failed to send message: {}", e),
            }
            Ok(())
        })?;

        Ok(awaitable.into_pyobject(py)?.into_any().into())
    }

    pub fn close(&self) {
        self.registry_addr.do_send(Close { id: self.id });
    }

    #[getter]
    pub fn get_id(&self) -> String {
        self.id.to_string()
    }

    #[getter]
    pub fn get_query_params(&self) -> QueryParams {
        self.query_params.clone()
    }

    /// Get the message channel for WebSocket handlers.
    #[getter]
    pub fn get_message_channel(&self, py: Python) -> Option<Py<WebSocketChannel>> {
        self.message_channel.as_ref().map(|c| c.clone_ref(py))
    }
}

static REGISTRY_ADDRESSES: OnceCell<RwLock<HashMap<String, Addr<WebSocketRegistry>>>> =
    OnceCell::new();

fn get_or_init_registry_for_endpoint(endpoint: String) -> Addr<WebSocketRegistry> {
    let map_lock = REGISTRY_ADDRESSES.get_or_init(|| RwLock::new(HashMap::new()));

    {
        let map = map_lock.read();
        if let Some(registry_addr) = map.get(&endpoint) {
            return registry_addr.clone();
        }
    }

    let new_registry = WebSocketRegistry::new().start();

    {
        let mut map = map_lock.write();
        map.insert(endpoint, new_registry.clone());
    }

    new_registry
}

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
    endpoint: String,
    max_frame_size: usize,
) -> Result<HttpResponse, Error> {
    let registry_addr = get_or_init_registry_for_endpoint(endpoint);

    let mut query_params = QueryParams::new();

    if !req.query_string().is_empty() {
        let split = req.query_string().split('&');
        for s in split {
            let path_params = s.split_once('=').unwrap_or((s, ""));
            let key = path_params.0.to_string();
            let value = path_params.1.to_string();

            query_params.set(key, value);
        }
    }

    ws::WsResponseBuilder::new(
        WebSocketConnector {
            router,
            task_locals,
            id: Uuid::new_v4(),
            registry_addr,
            query_params,
            message_sender: None,
            message_channel: None,
        },
        &req,
        stream,
    )
    .frame_size(max_frame_size)
    .start()
}
