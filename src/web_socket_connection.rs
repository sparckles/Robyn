use crate::types::function_info::FunctionInfo;

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;
use std::thread;
use uuid::Uuid;

use std::collections::HashMap;

#[derive(Default)]
#[pyclass]
pub struct GlobalRegistry {
    // A map of client IDs to their Actor addresses.
    clients: HashMap<Uuid, Addr<MyWs>>,
}

impl actix::Supervised for GlobalRegistry {}

impl SystemService for GlobalRegistry {}

impl Actor for GlobalRegistry {
    type Context = Context<Self>;
}

struct Register {
    id: Uuid,
    addr: Addr<MyWs>,
}

impl Message for Register {
    type Result = ();
}

impl Handler<Register> for GlobalRegistry {
    type Result = ();

    fn handle(&mut self, msg: Register, _ctx: &mut Self::Context) {
        self.clients.insert(msg.id, msg.addr);
    }
}

// New message for sending text to a specific client
struct SendText {
    id: Uuid,
    message: String,
}

impl Message for SendText {
    type Result = ();
}

impl GlobalRegistry {
    pub fn send_message_to_client_(&self, client_id: Uuid, message: String) {
        if let Some(client_addr) = self.clients.get(&client_id) {
            client_addr.do_send(SendText {
                id: client_id,
                message,
            });
        }
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

impl Handler<SendText> for GlobalRegistry {
    type Result = ();

    fn handle(&mut self, msg: SendText, _ctx: &mut Self::Context) {
        if let Some(client_addr) = self.clients.get(&msg.id) {
            client_addr.do_send(msg);
        }
    }
}

struct SendMessageToAll(String);

impl Message for SendMessageToAll {
    type Result = ();
}

impl Handler<SendMessageToAll> for GlobalRegistry {
    type Result = ();

    fn handle(&mut self, msg: SendMessageToAll, _ctx: &mut Self::Context) {
        for (id, client) in &self.clients {
            client.do_send(SendText {
                id: *id,
                message: msg.0.clone(),
            });
        }
    }
}

#[pymethods]
impl GlobalRegistry {
    #[staticmethod]
    fn send_message_to_client(client_id_str: &str, message: &str) -> PyResult<()> {
        let client_id = Uuid::parse_str(client_id_str)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;
        GlobalRegistry::from_registry().do_send(SendText {
            id: client_id,
            message: message.to_string(),
        });
        Ok(())
    }

    #[staticmethod]
    fn send_message_to_all(message: &str) -> PyResult<()> {
        GlobalRegistry::from_registry().do_send(SendMessageToAll(message.to_string()));
        Ok(())
    }

    #[staticmethod]
    fn trigger_send_message_to_all(message: &str) -> PyResult<()> {
        let sys = System::new();

        sys.block_on(async {
            GlobalRegistry::from_registry().do_send(SendMessageToAll(message.to_string()));
        });

        Ok(())
    }
}
/// Define HTTP actor
#[derive(Clone)]
struct MyWs {
    id: Uuid,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
}

fn get_function_output<'a>(
    function: &'a FunctionInfo,
    fn_msg: Option<String>,
    py: Python<'a>,
    ws: &MyWs,
) -> Result<&'a PyAny, PyErr> {
    let handler = function.handler.as_ref(py);

    // this makes the request object accessible across every route
    match function.number_of_params {
        0 => handler.call0(),
        1 => handler.call1((ws.id.to_string(),)),
        // this is done to accommodate any future params
        2_u8..=u8::MAX => handler.call1((ws.id.to_string(), fn_msg.unwrap_or_default())),
    }
}

fn execute_ws_function(
    function: &FunctionInfo,
    text: Option<String>,
    task_locals: &TaskLocals,
    ctx: &mut ws::WebsocketContext<MyWs>,
    ws: &MyWs,
    // add number of params here
) {
    if function.is_async {
        let fut = Python::with_gil(|py| {
            pyo3_asyncio::into_future_with_locals(
                task_locals,
                get_function_output(function, text, py, ws).unwrap(),
            )
            .unwrap()
        });
        let f = async {
            let output = fut.await.unwrap();
            Python::with_gil(|py| output.extract::<&str>(py).unwrap().to_string())
        }
        .into_actor(ws)
        .map(|res, _, ctx| ctx.text(res));
        ctx.spawn(f);
    } else {
        Python::with_gil(|py| {
            if let Some(op) = get_function_output(function, text, py, ws)
                .unwrap()
                .extract::<Option<&str>>()
                .unwrap()
            {
                ctx.text(op);
            }
        });
    }
}

// By default mailbox capacity is 16 messages.
impl Actor for MyWs {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let addr = ctx.address();
        // Register with global registry
        GlobalRegistry::from_registry().do_send(Register {
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
