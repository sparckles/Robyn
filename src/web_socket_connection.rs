use actix::{Actor, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use actix_web_actors::ws::WebsocketContext;

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

    fn stopped(&mut self, ctx: &mut WebsocketContext<Self>) {
        println!("Actor is stopped");
    }
}

/// Handler for ws::Message message
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for MyWs {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                println!("Ping message {:?}", msg);
                ctx.pong(&msg)
            }

            Ok(ws::Message::Pong(msg)) => {
                println!("Pong message {:?}", msg);
                ctx.pong(&msg)
            }

            Ok(ws::Message::Text(text)) => {
                let router = &self.router;
                // let (tuple, route_params) = router.get_route(Method::GET, "WS").unwrap();
                // println!("{:?}", tuple);
                let handler_function = &self.router.get("message").unwrap().0;
                let number_of_params = &self.router.get("message").unwrap().1;
                println!("{:?}", handler_function);
                match handler_function {
                    PyFunction::SyncFunction(handler) => Python::with_gil(|py| {
                        let handler = handler.as_ref(py);
                        // call execute function
                        let op = handler.call0().unwrap();
                        let op: &str = op.extract().unwrap();

                        return ctx.text(op);
                    }),
                    PyFunction::CoRoutine(handler) => {
                        println!("Async functions are not supported in WS right now.");
                        return ctx.text("Async Functions are not supported in WS right now.");
                    }
                }
                // let async_exection_function = execute_function(handler_function, number_of_params);

                // // do some compute-heavy work or call synchronous code
                // let res = Runtime::new()
                //     .unwrap()
                //     .block_on(async_exection_function)
                //     .unwrap();

                // return ctx.text(res);
            }

            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(close_reason)) => {
                println!("Socket was closed");
            }
            _ => (),
        }
    }
}

use crate::types::PyFunction;
use actix_web::*;
use dashmap::DashMap;
use pyo3::prelude::*;
use std::collections::HashMap;

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
    router: Arc<HashMap<String, (PyFunction, u8)>>,
) -> Result<HttpResponse, Error> {
    let resp = ws::start(MyWs { router }, &req, stream);
    println!("{:?}", resp);
    resp
}

// pub async fn start_web_socket(
//     router: web::Data<Arc<Router>>,
//     headers: web::Data<Arc<Headers>>,
//     stream: web::Payload,
//     req: HttpRequest,
// ) -> Result<HttpResponse, Error> {
//     let resp = ws::start(MyWs {}, &req, stream);
//     println!("{:?}", resp);
//     resp
// }

// async fn index(
//     router: web::Data<Arc<Router>>,
//     headers: web::Data<Arc<Headers>>,
//     stream: web::Payload,
//     req: HttpRequest,
// ) -> impl Responder {
//     match router.get_route(req.method().clone(), req.uri().path()) {
//         Some(((handler_function, number_of_params), route_params)) => {
//             handle_request(
//                 handler_function,
//                 number_of_params,
//                 &headers,
//                 &mut payload,
//                 &req,
//                 route_params,
//             )
//             .await
//         }
//         None => {
//             let mut response = HttpResponse::Ok();
//             apply_headers(&mut response, &headers);
//             response.finish()
//         }
//     }
// }
