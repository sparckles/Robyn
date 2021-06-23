use tokio::io::AsyncWriteExt;
use tokio::net::TcpStream;
// pyO3 module
use crate::types::PyFunction;
use pyo3::prelude::*;

// Handle message fetches the response function
// function is the response function fetched from the router
// tokio task is spawned depending on the type of function fetched (Sync/Async)

pub async fn handle_message(function: PyFunction, mut stream: TcpStream) {
    let contents = match function {
        PyFunction::CoRoutine(handler) => {
            let output = Python::with_gil(|py| {
                let coro = handler.as_ref(py).call0().unwrap();
                pyo3_asyncio::into_future(coro).unwrap()
            });
            let output = output.await.unwrap();
            Python::with_gil(|py| -> PyResult<String> {
                let contents: &str = output.extract(py).unwrap();
                Ok(contents.to_string())
            })
            .unwrap()
        }
        PyFunction::SyncFunction(handler) => tokio::task::spawn_blocking(move || {
            Python::with_gil(|py| {
                let handler = handler.as_ref(py);
                let output: &str = (&handler).call0().unwrap().extract().unwrap();
                output.to_string()
            })
        })
        .await
        .unwrap(),
    };

    let status_line = "HTTP/1.1 200 OK";

    let len = contents.len();
    let response = format!(
        "{}\r\nContent-Length: {}\r\n\r\n{}",
        status_line, len, contents
    );

    stream.write_all(response.as_bytes()).await.unwrap();
}
