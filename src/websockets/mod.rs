pub mod registry;

use crate::executors::web_socket_executors::execute_ws_function;
use crate::types::function_info::FunctionInfo;
use registry::{SendMessageToAll, SendText};

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;
use uuid::Uuid;

use registry::{Register, WebSocketRegistry};
use std::collections::HashMap;

/// Define HTTP actor
#[derive(Clone)]
#[pyclass]
pub struct MyWs {
    pub id: Uuid,
    pub router: HashMap<String, FunctionInfo>,
    pub task_locals: TaskLocals,
    pub registry_addr: Addr<WebSocketRegistry>,
}

// By default mailbox capacity is 16 messages.
impl Actor for MyWs {
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

impl Handler<SendText> for MyWs {
    type Result = ();

    fn handle(&mut self, msg: SendText, ctx: &mut Self::Context) {
        if self.id == msg.recipient_id {
            ctx.text(msg.message);
        }
    }
}

/// Handler for ws::Message message
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for MyWs {
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
impl MyWs {
    pub fn send_to(&self, recipient_id: String, message: String) {
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

    pub fn broadcast(&self, message: String) {
        // TODO: this should spawn a new thread?
        let sys = System::new();

        sys.block_on(async {
            let registry = self.registry_addr.clone();
            match (&registry).try_send(SendMessageToAll {
                message: message.to_string(),
                sender_id: self.id,
            }) {
                Ok(_) => println!("Message sent successfully"),
                Err(e) => println!("Failed to send message: {}", e),
            }
        });
    }

    #[getter]
    pub fn get_id(&self) -> String {
        self.id.to_string()
    }
}

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
) -> Result<HttpResponse, Error> {
    let registry_addr = WebSocketRegistry::new().start();

    let result = ws::start(
        MyWs {
            router,
            task_locals,
            id: Uuid::new_v4(),
            registry_addr, // Assuming you add this field to the MyWs struct
        },
        &req,
        stream,
    );

    result
}
