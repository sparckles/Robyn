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
            Python::with_gil(|py| output.extract::<Option<String>>(py).unwrap())
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
            let handler = function.handler.bind(py).downcast().unwrap();
            if let Some(op) = handler
                .call1((ws.clone(),))
                .unwrap()
                .extract::<Option<String>>()
                .unwrap()
            {
                ctx.text(op);
            }
        });
    }
}
