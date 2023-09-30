mod registry;

use crate::executors::web_socket_executors::execute_ws_function;
use crate::types::function_info::FunctionInfo;
use registry::SendText;

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use pyo3_asyncio::TaskLocals;
use uuid::Uuid;

pub use registry::{send_message_to_all_ws, send_message_to_ws_client};
use registry::{Register, WebSocketRegistry};
use std::collections::HashMap;

/// Define HTTP actor
#[derive(Clone)]
pub struct MyWs {
    pub id: Uuid,
    pub router: HashMap<String, FunctionInfo>,
    pub task_locals: TaskLocals,
}

// By default mailbox capacity is 16 messages.
impl Actor for MyWs {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let addr = ctx.address();
        // Register with global registry
        WebSocketRegistry::from_registry().do_send(Register {
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
        if self.id == msg.id {
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

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
) -> Result<HttpResponse, Error> {
    let result = ws::start(
        MyWs {
            router,
            task_locals,
            id: Uuid::new_v4(),
        },
        &req,
        stream,
    );

    result
}
