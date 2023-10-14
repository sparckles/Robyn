pub mod registry;

use crate::executors::web_socket_executors::execute_ws_function;
use crate::types::function_info::FunctionInfo;
use registry::{SendMessageToAll, SendText};

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use once_cell::sync::OnceCell;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;
use std::sync::RwLock;
use uuid::Uuid;

use registry::{Register, WebSocketRegistry};
use std::collections::HashMap;

/// Define HTTP actor
#[derive(Clone)]
#[pyclass]
pub struct WebSocketConnector {
    pub id: Uuid,
    pub router: HashMap<String, FunctionInfo>,
    pub task_locals: TaskLocals,
    pub registry_addr: Addr<WebSocketRegistry>,
}

// By default mailbox capacity is 16 messages.
impl Actor for WebSocketConnector {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let addr = ctx.address();
        // Register with global registry
        self.registry_addr.do_send(Register {
            id: self.id,
            addr: addr.clone(),
        });

        let function = self.router.get("connect").unwrap();
        execute_ws_function(function, None, &self.task_locals, ctx, self);

        debug!("Actor is alive");
    }

    fn stopped(&mut self, ctx: &mut Self::Context) {
        let function = self.router.get("close").unwrap();
        execute_ws_function(function, None, &self.task_locals, ctx, self);
        debug!("Actor is dead");
    }
}

impl Handler<SendText> for WebSocketConnector {
    type Result = ();

    fn handle(&mut self, msg: SendText, ctx: &mut Self::Context) {
        if self.id == msg.recipient_id {
            ctx.text(msg.message);
        }
    }
}

/// Handler for ws::Message message
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for WebSocketConnector {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                debug!("Ping message {:?}", msg);
                let function = self.router.get("connect").unwrap();
                debug!("{:?}", function.handler);
                execute_ws_function(function, None, &self.task_locals, ctx, self);
                ctx.pong(&msg)
            }
            Ok(ws::Message::Pong(msg)) => {
                debug!("Pong message {:?}", msg);
            }
            Ok(ws::Message::Text(text)) => {
                // need to also pass this text as a param
                debug!("Text message received {:?}", text);
                let function = self.router.get("message").unwrap();
                execute_ws_function(
                    function,
                    Some(text.to_string()),
                    &self.task_locals,
                    ctx,
                    self,
                );
            }
            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(_close_reason)) => {
                debug!("Socket was closed");
                let function = self.router.get("close").unwrap();
                execute_ws_function(function, None, &self.task_locals, ctx, self);
            }
            _ => (),
        }
    }
}

#[pymethods]
impl WebSocketConnector {
    pub fn sync_send_to(&self, recipient_id: String, message: String) {
        let recipient_id = Uuid::parse_str(&recipient_id).unwrap();

        match (self.registry_addr).try_send(SendText {
            message: message.to_string(),
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

        let awaitable = pyo3_asyncio::tokio::future_into_py(py, async move {
            match (registry).try_send(SendText {
                message: message.to_string(),
                sender_id,
                recipient_id,
            }) {
                Ok(_) => println!("Message sent successfully"),
                Err(e) => println!("Failed to send message: {}", e),
            }
            Ok(())
        })?;

        Ok(awaitable.into_py(py))
    }

    pub fn sync_broadcast(&self, message: String) {
        let registry = self.registry_addr.clone();
        match registry.try_send(SendMessageToAll {
            message: message.to_string(),
            sender_id: self.id,
        }) {
            Ok(_) => println!("Message sent successfully"),
            Err(e) => println!("Failed to send message: {}", e),
        }
    }

    pub fn async_broadcast(&self, py: Python, message: String) -> PyResult<Py<PyAny>> {
        let registry = self.registry_addr.clone();
        let sender_id = self.id;

        let awaitable = pyo3_asyncio::tokio::future_into_py(py, async move {
            match registry.try_send(SendMessageToAll {
                message: message.to_string(),
                sender_id,
            }) {
                Ok(_) => println!("Message sent successfully"),
                Err(e) => println!("Failed to send message: {}", e),
            }
            Ok(())
        })?;

        Ok(awaitable.into_py(py))
    }

    #[getter]
    pub fn get_id(&self) -> String {
        self.id.to_string()
    }
}

static REGISTRY_ADDRESSES: OnceCell<RwLock<HashMap<String, Addr<WebSocketRegistry>>>> =
    OnceCell::new();

fn get_or_init_registry_for_endpoint(endpoint: String) -> Addr<WebSocketRegistry> {
    let map_lock = REGISTRY_ADDRESSES.get_or_init(|| RwLock::new(HashMap::new()));

    {
        let map = map_lock.read().unwrap();
        if let Some(registry_addr) = map.get(&endpoint) {
            return registry_addr.clone();
        }
    }

    let new_registry = WebSocketRegistry::new().start();

    {
        let mut map = map_lock.write().unwrap();
        map.insert(endpoint.to_string(), new_registry.clone());
    }

    new_registry
}

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
    endpoint: String,
) -> Result<HttpResponse, Error> {
    let registry_addr = get_or_init_registry_for_endpoint(endpoint);

    ws::start(
        WebSocketConnector {
            router,
            task_locals,
            id: Uuid::new_v4(),
            registry_addr,
        },
        &req,
        stream,
    )
}
