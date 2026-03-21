use actix::{ActorContext, ActorFutureExt, AsyncContext, WrapFuture};
use actix_web_actors::ws::WebsocketContext;
use log::warn;
use pyo3::prelude::*;
use pyo3_async_runtimes::TaskLocals;

use crate::types::function_info::FunctionInfo;
use crate::websockets::{WebSocketConnector, WsPayload};

fn extract_ws_return(_py: Python, output: &Bound<'_, PyAny>) -> Option<WsPayload> {
    if output.is_none() {
        return None;
    }
    if let Ok(s) = output.extract::<String>() {
        Some(WsPayload::Text(s))
    } else if let Ok(b) = output.extract::<Vec<u8>>() {
        Some(WsPayload::Binary(b))
    } else {
        let type_name = output
            .get_type()
            .name()
            .map(|n| n.to_string())
            .unwrap_or_else(|_| "<unknown>".into());
        warn!(
            "extract_ws_return: unsupported return type '{}' from WebSocket handler; expected str, bytes, or None",
            type_name
        );
        None
    }
}

pub fn execute_ws_function(
    function: &FunctionInfo,
    task_locals: &TaskLocals,
    ctx: &mut WebsocketContext<WebSocketConnector>,
    ws: &WebSocketConnector,
) {
    if function.is_async {
        let fut = Python::with_gil(|py| {
            let handler = function.handler.bind(py).downcast().unwrap();
            pyo3_async_runtimes::into_future_with_locals(
                task_locals,
                handler.call1((ws.clone(),)).unwrap(),
            )
            .unwrap()
        });
        let f = async {
            let output = fut.await.unwrap();
            Python::with_gil(|py| extract_ws_return(py, output.bind(py)))
        }
        .into_actor(ws)
        .map(|res, _, ctx| match res {
            Some(WsPayload::Text(s)) => ctx.text(s),
            Some(WsPayload::Binary(b)) => ctx.binary(b),
            Some(WsPayload::Close) => ctx.stop(),
            None => {}
        });
        ctx.spawn(f);
    } else {
        Python::with_gil(|py| {
            let handler = function.handler.bind(py).downcast().unwrap();
            let result = handler.call1((ws.clone(),)).unwrap();
            match extract_ws_return(py, &result) {
                Some(WsPayload::Text(s)) => ctx.text(s),
                Some(WsPayload::Binary(b)) => ctx.binary(b),
                Some(WsPayload::Close) => ctx.stop(),
                None => {}
            }
        });
    }
}
