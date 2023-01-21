use crate::types::FunctionInfo;

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use log::debug;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;
use uuid::Uuid;

use std::collections::HashMap;

/// Define HTTP actor
#[derive(Clone)]
struct MyWs {
    id: Uuid,
    router: HashMap<String, FunctionInfo>,
    task_locals: TaskLocals,
}

fn get_function_output<'a>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    ws: &MyWs,
) -> Result<&'a PyAny, PyErr> {
    let handler = function.handler.as_ref(py);

    // this makes the request object accessible across every route
    match function.number_of_params {
        0 => handler.call0(),
        1 => handler.call1((ws.id.to_string(),)),
        // this is done to accommodate any future params
        2_u8..=u8::MAX => handler.call1((ws.id.to_string(),)),
    }
}

fn execute_ws_function(
    function: &FunctionInfo,
    task_locals: &TaskLocals,
    ctx: &mut ws::WebsocketContext<MyWs>,
    ws: &MyWs,
    // add number of params here
) {
    if function.is_async {
        let fut = Python::with_gil(|py| {
            pyo3_asyncio::into_future_with_locals(
                task_locals,
                get_function_output(function, py, ws).unwrap(),
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
            let op: &str = get_function_output(function, py, ws)
                .unwrap()
                .extract()
                .unwrap();
            ctx.text(op);
        });
    }
}

// By default mailbox capacity is 16 messages.
impl Actor for MyWs {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let function = self.router.get("connect").unwrap();
        execute_ws_function(function, &self.task_locals, ctx, self);

        debug!("Actor is alive");
    }

    fn stopped(&mut self, ctx: &mut Self::Context) {
        let function = self.router.get("close").unwrap();
        execute_ws_function(function, &self.task_locals, ctx, self);

        debug!("Actor is dead");
    }
}

#[derive(Message)]
#[rtype(result = "Result<(), ()>")]
struct CommandRunner(String);

/// Handler for ws::Message message
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for MyWs {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                debug!("Ping message {:?}", msg);
                let function = self.router.get("connect").unwrap();
                debug!("{:?}", function.handler);
                execute_ws_function(function, &self.task_locals, ctx, self);
                ctx.pong(&msg)
            }
            Ok(ws::Message::Pong(msg)) => {
                debug!("Pong message {:?}", msg);
                ctx.pong(&msg)
            }
            Ok(ws::Message::Text(_text)) => {
                // need to also pass this text as a param
                let function = self.router.get("message").unwrap();
                execute_ws_function(function, &self.task_locals, ctx, self);
            }
            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(_close_reason)) => {
                debug!("Socket was closed");
                let function = self.router.get("close").unwrap();
                execute_ws_function(function, &self.task_locals, ctx, self);
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
    ws::start(
        MyWs {
            router,
            task_locals,
            id: Uuid::new_v4(),
        },
        &req,
        stream,
    )
}
