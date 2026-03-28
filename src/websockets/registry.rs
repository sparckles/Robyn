use actix::prelude::*;
use actix::Actor;
use pyo3::prelude::*;
use uuid::Uuid;

use std::collections::HashMap;

use super::WsPayload;
use crate::websockets::WebSocketConnector;

#[derive(Default)]
#[pyclass]
pub struct WebSocketRegistry {
    clients: HashMap<Uuid, Addr<WebSocketConnector>>,
}

impl actix::Supervised for WebSocketRegistry {}

impl SystemService for WebSocketRegistry {}

impl Actor for WebSocketRegistry {
    type Context = Context<Self>;
}

pub struct Register {
    pub id: Uuid,
    pub addr: Addr<WebSocketConnector>,
}

impl Message for Register {
    type Result = ();
}

impl Handler<Register> for WebSocketRegistry {
    type Result = ();

    fn handle(&mut self, msg: Register, _ctx: &mut Self::Context) {
        self.clients.insert(msg.id, msg.addr);
    }
}

pub struct SendMessage {
    pub recipient_id: Uuid,
    pub payload: WsPayload,
    pub sender_id: Uuid,
}

impl Message for SendMessage {
    type Result = ();
}

impl WebSocketRegistry {
    pub fn new() -> Self {
        Self {
            clients: HashMap::new(),
        }
    }

    pub fn start() -> Addr<Self> {
        Self::from_registry()
    }
}

impl Handler<SendMessage> for WebSocketRegistry {
    type Result = ();

    fn handle(&mut self, msg: SendMessage, _ctx: &mut Self::Context) {
        let recipient_id = msg.recipient_id;

        if let Some(client_addr) = self.clients.get(&recipient_id) {
            client_addr.do_send(msg);
        } else {
            log::warn!("No client found for id: {}", recipient_id);
        }
    }
}

pub struct SendMessageToAll {
    pub payload: WsPayload,
    pub sender_id: Uuid,
}

impl Message for SendMessageToAll {
    type Result = ();
}

impl Handler<SendMessageToAll> for WebSocketRegistry {
    type Result = ();

    fn handle(&mut self, msg: SendMessageToAll, _ctx: &mut Self::Context) {
        for (id, client) in &self.clients {
            client.do_send(SendMessage {
                recipient_id: *id,
                payload: msg.payload.clone(),
                sender_id: msg.sender_id,
            });
        }
    }
}

pub struct Close {
    pub id: Uuid,
}

impl Message for Close {
    type Result = ();
}

impl Handler<Close> for WebSocketRegistry {
    type Result = ();

    fn handle(&mut self, msg: Close, _ctx: &mut Self::Context) {
        if let Some(client) = self.clients.remove(&msg.id) {
            client.do_send(SendMessage {
                recipient_id: msg.id,
                payload: WsPayload::Text("Connection closed".to_string()),
                sender_id: msg.id,
            });
        }
    }
}
