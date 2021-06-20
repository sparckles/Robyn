use tokio::io::AsyncWriteExt;
use tokio::net::TcpStream;
// pyO3 module
use pyo3::prelude::*;

pub async fn handle_message(handler: Py<PyAny>, mut stream: TcpStream) {
    let f = Python::with_gil(|py| {
        let coro = handler.as_ref(py).call0().unwrap();
        pyo3_asyncio::into_future(&coro).unwrap()
    });

    let output = f.await.unwrap();
    let status_line = "HTTP/1.1 200 OK";
    let contents = Python::with_gil(|py| -> PyResult<String> {
        let contents: &str = output.extract(py).unwrap();
        Ok(contents.to_string())
    })
    .unwrap();

    let len = contents.len();
    let response = format!(
        "{}\r\nContent-Length: {}\r\n\r\n{}",
        status_line, len, contents
    );

    stream.write_all(response.as_bytes()).await.unwrap();
}
