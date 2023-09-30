use actix::prelude::*;
use actix::Actor;
use pyo3::prelude::*;
use uuid::Uuid;

use std::collections::HashMap;

use crate::websockets::MyWs;

#[derive(Default)]
#[pyclass]
pub struct WebSocketRegistry {
    // A map of client IDs to their Actor addresses.
    clients: HashMap<Uuid, Addr<MyWs>>,
}

impl actix::Supervised for WebSocketRegistry {}

impl SystemService for WebSocketRegistry {}

impl Actor for WebSocketRegistry {
    type Context = Context<Self>;
}

pub struct Register {
    pub id: Uuid,
    pub addr: Addr<MyWs>,
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

// New message for sending text to a specific client
pub struct SendText {
    pub id: Uuid,
    pub message: String,
}

impl Message for SendText {
    type Result = ();
}

impl WebSocketRegistry {
    pub fn send_message_to_client_(&self, client_id: Uuid, message: String) {
        if let Some(client_addr) = self.clients.get(&client_id) {
            client_addr.do_send(SendText {
                id: client_id,
                message,
            });
        }
    }
}

impl Handler<SendText> for WebSocketRegistry {
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

impl Handler<SendMessageToAll> for WebSocketRegistry {
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

#[pyfunction]
pub fn send_message_to_ws_client(client_id_str: &str, message: &str) -> PyResult<()> {
    let client_id = Uuid::parse_str(client_id_str)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;
    WebSocketRegistry::from_registry().do_send(SendText {
        id: client_id,
        message: message.to_string(),
    });
    Ok(())
}

#[pyfunction]
pub fn send_message_to_all_ws(message: &str) -> PyResult<()> {
    let sys = System::new();

    sys.block_on(async {
        WebSocketRegistry::from_registry().do_send(SendMessageToAll(message.to_string()));
    });

    Ok(())
}
