use actix::{ActorFutureExt, AsyncContext, WrapFuture};
use actix_web_actors::ws::WebsocketContext;
use pyo3::prelude::*;
use pyo3_async_runtimes::TaskLocals;

use crate::types::function_info::FunctionInfo;
use crate::websockets::WebSocketConnector;

pub fn execute_ws_function(
    function: &FunctionInfo,
    task_locals: &TaskLocals,
    ctx: &mut WebsocketContext<WebSocketConnector>,
    ws: &WebSocketConnector,
) {
    if function.is_async {
        let fut = match Python::with_gil(|py| {
            let handler = function.handler.bind(py).downcast()?;
            let result = handler.call1((ws.clone(),))?;
            pyo3_async_runtimes::into_future_with_locals(task_locals, result)
        }) {
            Ok(fut) => fut,
            Err(e) => {
                log::error!("Failed to call async WebSocket handler: {}", e);
                return;
            }
        };
        let f = async move {
            match fut.await {
                Ok(output) => Python::with_gil(|py| match output.extract::<Option<String>>(py) {
                    Ok(msg) => msg,
                    Err(e) => {
                        log::error!("Failed to extract WebSocket handler result: {}", e);
                        None
                    }
                }),
                Err(e) => {
                    log::error!("Async WebSocket handler failed: {}", e);
                    None
                }
            }
        }
        .into_actor(ws)
        .map(|res, _, ctx| {
            if let Some(msg) = res {
                ctx.text(msg);
            }
        });
        ctx.spawn(f);
    } else {
        Python::with_gil(|py| {
            let handler = match function.handler.bind(py).downcast() {
                Ok(h) => h,
                Err(e) => {
                    log::error!("Failed to get sync WebSocket handler: {}", e);
                    return;
                }
            };
            match handler.call1((ws.clone(),)) {
                Ok(result) => match result.extract::<Option<String>>() {
                    Ok(Some(op)) => ctx.text(op),
                    Ok(None) => {}
                    Err(e) => log::error!("Failed to extract WebSocket handler result: {}", e),
                },
                Err(e) => log::error!("Sync WebSocket handler call failed: {}", e),
            }
        });
    }
}
