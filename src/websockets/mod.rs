pub mod registry;

use crate::executors::web_socket_executors::execute_ws_function;
use crate::types::function_info::FunctionInfo;
use crate::types::multimap::QueryParams;
use registry::{Close, SendMessage, SendMessageToAll};

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use once_cell::sync::OnceCell;
use parking_lot::RwLock;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3::IntoPyObject;
use pyo3_async_runtimes::TaskLocals;
use std::sync::Arc;
use tokio::sync::mpsc;
use uuid::Uuid;

use crate::runtime;

use registry::{Register, WebSocketRegistry};
use std::collections::HashMap;

#[derive(Clone)]
pub enum WsPayload {
    Text(String),
    Binary(Vec<u8>),
}

fn extract_payload(message: &Bound<'_, PyAny>) -> PyResult<WsPayload> {
    if let Ok(s) = message.extract::<String>() {
        Ok(WsPayload::Text(s))
    } else if let Ok(b) = message.extract::<Vec<u8>>() {
        Ok(WsPayload::Binary(b))
    } else {
        Err(pyo3::exceptions::PyTypeError::new_err(
            "message must be str or bytes",
        ))
    }
}

/// A Rust-backed channel receiver exposed to Python.
/// Python handlers call `await channel.receive()` to get the next message.
/// Returns str for text frames, bytes for binary frames, or None when closed.
#[pyclass]
pub struct WebSocketChannel {
    receiver: Arc<tokio::sync::Mutex<mpsc::UnboundedReceiver<Option<WsPayload>>>>,
}

#[pymethods]
impl WebSocketChannel {
    /// Await the next message from the WebSocket.
    /// Returns str for text frames, bytes for binary frames, or None if closed.
    fn receive<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let receiver = self.receiver.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut rx = receiver.lock().await;
            match rx.recv().await {
                Some(Some(WsPayload::Text(s))) => Python::with_gil(|py| {
                    Ok(Some(s.into_pyobject(py).unwrap().into_any().unbind()))
                }),
                Some(Some(WsPayload::Binary(b))) => {
                    Python::with_gil(|py| Ok(Some(PyBytes::new(py, &b).into_any().unbind())))
                }
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
    pub message_sender: Option<mpsc::UnboundedSender<Option<WsPayload>>>,
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

        let (tx, rx) = mpsc::unbounded_channel::<Option<WsPayload>>();
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

        match self.router.get("connect") {
            Some(function) => execute_ws_function(function, &self.task_locals, ctx, self),
            None => log::error!("No 'connect' handler registered for WebSocket"),
        }

        debug!("Actor is alive");
    }

    fn stopped(&mut self, ctx: &mut Self::Context) {
        self.message_sender.take();

        match self.router.get("close") {
            Some(function) => execute_ws_function(function, &self.task_locals, ctx, self),
            None => log::error!("No 'close' handler registered for WebSocket"),
        }
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

impl Handler<SendMessage> for WebSocketConnector {
    type Result = ();

    fn handle(&mut self, msg: SendMessage, ctx: &mut Self::Context) {
        if self.id == msg.recipient_id {
            match &msg.payload {
                WsPayload::Text(s) => {
                    ctx.text(s.clone());
                    if s == "Connection closed" {
                        ctx.stop();
                    }
                }
                WsPayload::Binary(b) => {
                    ctx.binary(b.clone());
                }
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
                    let _ = sender.send(Some(WsPayload::Text(text.to_string())));
                }
            }
            Ok(ws::Message::Binary(bin)) => {
                debug!("Binary message received ({} bytes)", bin.len());
                if let Some(ref sender) = self.message_sender {
                    let _ = sender.send(Some(WsPayload::Binary(bin.to_vec())));
                }
            }
            Ok(ws::Message::Close(_close_reason)) => {
                debug!("Socket was closed");
                self.message_sender.take();
                ctx.stop();
            }
            _ => (),
        }
    }
}

#[pymethods]
impl WebSocketConnector {
    pub fn sync_send_to(&self, recipient_id: String, message: &Bound<'_, PyAny>) -> PyResult<()> {
        let payload = extract_payload(message)?;
        let recipient_id = Uuid::parse_str(&recipient_id).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid recipient_id '{}': {}",
                recipient_id, e
            ))
        })?;

        match self.registry_addr.try_send(SendMessage {
            payload,
            sender_id: self.id,
            recipient_id,
        }) {
            Ok(_) => log::debug!("Message sent successfully"),
            Err(e) => log::error!("Failed to send message: {}", e),
        }
        Ok(())
    }

    pub fn async_send_to(
        &self,
        py: Python,
        recipient_id: String,
        message: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let payload = extract_payload(message)?;
        let registry = self.registry_addr.clone();
        let recipient_id = Uuid::parse_str(&recipient_id).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid recipient_id '{}': {}",
                recipient_id, e
            ))
        })?;
        let sender_id = self.id;

        let awaitable = runtime::future_into_py(py, async move {
            registry
                .try_send(SendMessage {
                    payload,
                    sender_id,
                    recipient_id,
                })
                .map_err(|e| {
                    anyhow::anyhow!("Failed to enqueue message to registry: {e}")
                })
        })?;

        Ok(awaitable.into_pyobject(py)?.into_any().into())
    }

    pub fn sync_broadcast(&self, message: &Bound<'_, PyAny>) -> PyResult<()> {
        let payload = extract_payload(message)?;
        match self.registry_addr.try_send(SendMessageToAll {
            payload,
            sender_id: self.id,
        }) {
            Ok(_) => log::debug!("Broadcast sent successfully"),
            Err(e) => log::error!("Failed to broadcast message: {}", e),
        }
        Ok(())
    }

    pub fn async_broadcast(&self, py: Python, message: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let payload = extract_payload(message)?;
        let registry = self.registry_addr.clone();
        let sender_id = self.id;

        let awaitable = runtime::future_into_py(py, async move {
            registry
                .try_send(SendMessageToAll { payload, sender_id })
                .map_err(|e| {
                    anyhow::anyhow!("Failed to enqueue broadcast to registry: {e}")
                })
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
