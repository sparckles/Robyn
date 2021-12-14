use crate::types::PyFunction;

use actix::prelude::*;
use actix::{Actor, AsyncContext, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use actix_web_actors::ws::WebsocketContext;
use pyo3::prelude::*;

use std::collections::HashMap;
use std::sync::Arc;

/// Define HTTP actor
struct MyWs {
    router: Arc<HashMap<String, (PyFunction, u8)>>,
}

// By default mailbox capacity is 16 messages.
impl Actor for MyWs {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut WebsocketContext<Self>) {
        println!("Actor is alive");
    }

    fn stopped(&mut self, _ctx: &mut WebsocketContext<Self>) {
        println!("Actor is alive");
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
                println!("Ping message {:?}", msg);
                let handler_function = &self.router.get("connect").unwrap().0;
                let _number_of_params = &self.router.get("connect").unwrap().1;
                println!("{:?}", handler_function);
                match handler_function {
                    PyFunction::SyncFunction(handler) => Python::with_gil(|py| {
                        let handler = handler.as_ref(py);
                        // call execute function
                        let op = handler.call0().unwrap();
                        let op: &str = op.extract().unwrap();

                        println!("{}", op);
                    }),
                    PyFunction::CoRoutine(handler) => {
                        println!("Async functions are not supported in WS right now.");
                    }
                }
                ctx.pong(&msg)
            }

            Ok(ws::Message::Pong(msg)) => {
                println!("Pong message {:?}", msg);
                ctx.pong(&msg)
            }

            Ok(ws::Message::Text(text)) => {
                // need to also passs this text as a param
                let handler_function = &self.router.get("message").unwrap().0;
                let _number_of_params = &self.router.get("message").unwrap().1;
                println!("{:?}", handler_function);
                match handler_function {
                    PyFunction::SyncFunction(handler) => Python::with_gil(|py| {
                        let handler = handler.as_ref(py);
                        // call execute function
                        let op = handler.call0().unwrap();
                        let op: &str = op.extract().unwrap();

                        return ctx.text(op);
                        // return ctx.text(op);
                    }),
                    PyFunction::CoRoutine(handler) => {
                        println!("{:?}", handler);
                        let fut = Python::with_gil(|py| {
                            let handler = handler.as_ref(py);
                            pyo3_asyncio::tokio::into_future(handler.call0().unwrap()).unwrap()
                        });
                        tokio::spawn(async {
                            let output = fut.await.unwrap();

                            Python::with_gil(|py| {
                                println!("Bruhhh moment");
                                let contents: &str = output.extract(py).unwrap();
                                println!("{:?}", contents);
                            });
                        });
                        let f = async move {};
                        let fut = actix::fut::wrap_future::<_, Self>(f);
                        // fut.spawn(self);
                        ctx.spawn(fut);
                        // ctx.add_stream("Hello, world");
                        return ctx.text("Async Functions are not supported in WS right now.");
                    }
                }
            }

            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(_close_reason)) => {
                println!("Socket was closed");
                let router = &self.router;
                let handler_function = &self.router.get("close").unwrap().0;
                let number_of_params = &self.router.get("close").unwrap().1;
                println!("{:?}", handler_function);
                match handler_function {
                    PyFunction::SyncFunction(handler) => Python::with_gil(|py| {
                        let handler = handler.as_ref(py);
                        // call execute function
                        let op = handler.call0().unwrap();
                        let op: &str = op.extract().unwrap();

                        println!("{:?}", op);
                    }),
                    PyFunction::CoRoutine(handler) => {
                        println!("Async functions are not supported in WS right now.");
                    }
                }
            }
            _ => (),
        }
    }
}

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: Arc<HashMap<String, (PyFunction, u8)>>,
) -> Result<HttpResponse, Error> {
    // execute the async function here
    let resp = ws::start(MyWs { router }, &req, stream);
    println!("{:?}", resp);
    resp
}
