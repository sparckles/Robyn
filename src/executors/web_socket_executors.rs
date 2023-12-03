use actix::prelude::*;
use actix::AsyncContext;
use actix_web_actors::ws;
use pyo3::prelude::*;
use pyo3_asyncio::TaskLocals;

use crate::types::function_info::FunctionInfo;
use crate::websockets::WebSocketConnector;

fn get_function_output<'a>(
    function: &'a FunctionInfo,
    fn_msg: Option<String>,
    py: Python<'a>,
    ws: &WebSocketConnector,
) -> Result<&'a PyAny, PyErr> {
    let handler = function.handler.as_ref(py);

    // this makes the request object accessible across every route

    let args = function.args.as_ref(py);
    let kwargs = function.kwargs.as_ref(py);

    match function.number_of_params {
        0 => handler.call0(),
        1 => {
            if args.get_item("ws").is_some() {
                handler.call1((ws.clone(),))
            } else if args.get_item("msg").is_some() {
                handler.call1((fn_msg.unwrap_or_default(),))
            } else {
                handler.call((), Some(kwargs))
            }
        }
        2 => {
            if args.get_item("ws").is_some() && args.get_item("msg").is_some() {
                handler.call1((ws.clone(), fn_msg.unwrap_or_default()))
            } else if args.get_item("ws").is_some() {
                handler.call((ws.clone(),), Some(kwargs))
            } else if args.get_item("msg").is_some() {
                handler.call((fn_msg.unwrap_or_default(),), Some(kwargs))
            } else {
                handler.call((), Some(kwargs))
            }
        }
        3 => {
            if args.get_item("ws").is_some() && args.get_item("msg").is_some() {
                handler.call((ws.clone(), fn_msg.unwrap_or_default()), Some(kwargs))
            } else if args.get_item("ws").is_some() {
                handler.call((ws.clone(),), Some(kwargs))
            } else if args.get_item("msg").is_some() {
                handler.call((fn_msg.unwrap_or_default(),), Some(kwargs))
            } else {
                handler.call((), Some(kwargs))
            }
        }
        4_u8..=u8::MAX => handler.call((ws.clone(), fn_msg.unwrap_or_default()), Some(kwargs)),
    }
}

pub fn execute_ws_function(
    function: &FunctionInfo,
    text: Option<String>,
    task_locals: &TaskLocals,
    ctx: &mut ws::WebsocketContext<WebSocketConnector>,
    ws: &WebSocketConnector,
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
