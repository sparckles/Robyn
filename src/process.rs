use tokio::io::AsyncWriteExt;
use tokio::net::TcpStream;
// pyO3 module
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

enum PyFunction {
    CoRoutine(Py<PyAny>),
    SyncFunction(Py<PyAny>),
}

pub async fn handle_message(process_object: Py<PyAny>, mut stream: TcpStream) {
    let function: PyFunction = Python::with_gil(|py| {
        let process_object_wrapper: &PyAny = process_object.as_ref(py);
        let py_dict = process_object_wrapper.downcast::<PyDict>().unwrap();
        let is_async: bool = py_dict.get_item("is_async").unwrap().extract().unwrap();
        let handler: &PyAny = py_dict.get_item("handler").unwrap();
        if is_async {
            let coro = handler.call0().unwrap();
            PyFunction::CoRoutine(coro.into())
        } else {
            PyFunction::SyncFunction(handler.into())
        }
    });

    let contents = match function {
        PyFunction::CoRoutine(coro) => {
            let x = Python::with_gil(|py| {
                let x = coro.as_ref(py);
                pyo3_asyncio::into_future(x).unwrap()
            });
            let output = x.await.unwrap();
            Python::with_gil(|py| -> PyResult<String> {
                let contents: &str = output.extract(py).unwrap();
                Ok(contents.to_string())
            })
            .unwrap()
        }
        PyFunction::SyncFunction(x) => tokio::task::spawn_blocking(move || {
            Python::with_gil(|py| {
                let y = x.as_ref(py);
                let s: &str = (&y).call0().unwrap().extract().unwrap();
                String::from(s)
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
