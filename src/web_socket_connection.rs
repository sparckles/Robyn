use actix::{Actor, StreamHandler};
use actix_web::{web, Error, HttpRequest, HttpResponse};
use actix_web_actors::ws;
use actix_web_actors::ws::WebsocketContext;

/// Define HTTP actor
struct MyWs;

// pub fn write_raw(&mut self, msg: Message)
// [src][−]
// Write payload

// This is a low-level function that accepts framed messages that should be created using Frame::message(). If you want to send text or binary data you should prefer the text() or binary() convenience functions that handle the framing for you.

// pub fn text<T: Into<String>>(&mut self, text: T)
// [src][−]
// Send text frame

// pub fn binary<B: Into<Bytes>>(&mut self, data: B)
// [src][−]
// Send binary frame

// pub fn ping(&mut self, message: &[u8])
// [src][−]
// Send ping frame

// pub fn pong(&mut self, message: &[u8])
// [src][−]
// Send pong frame

// pub fn close(&mut self, reason: Option<CloseReason>)
// [src][−]
// Send close frame

// pub fn handle(&self) -> SpawnHandle
// [src][−]
// Handle of the running future

// SpawnHandle is the handle returned by AsyncContext::spawn() method.

// pub fn set_mailbox_capacity(&mut self, cap: usize)
// [src][−]
// Set mailbox capacity

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
                println!("Hello, how are you!");
                ctx.text(text)
            }
            Ok(ws::Message::Binary(bin)) => ctx.binary(bin),
            Ok(ws::Message::Close(close_reason)) => {
                println!("Socket was closed");
            }
            _ => (),
        }
    }
}

pub async fn start_web_socket(
    req: HttpRequest,
    stream: web::Payload,
) -> Result<HttpResponse, Error> {
    let resp = ws::start(MyWs {}, &req, stream);
    println!("{:?}", resp);
    resp
}
