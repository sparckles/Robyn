use std::thread;
mod process;
mod request;
mod router;
mod server;
mod types;

use server::Server;
use std::io::prelude::*;
use std::net::TcpStream;
use std::time::Duration;

// pyO3 module
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use std::future::Future;

#[pyfunction]
pub fn start_server() {
    let _listener = Server::new();
}

#[pymodule]
pub fn robyn(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(start_server))?;
    m.add_class::<Server>()?;
    pyo3_asyncio::try_init(py).unwrap();
    pyo3::prepare_freethreaded_python();

    Ok(())
}

// let mut contents = String::new();

pub fn handle_connection<'a, F>(
    mut stream: TcpStream,
    runtime: tokio::runtime::Runtime,
    contents: &'a mut String,
    test: &dyn Fn(&'a mut String, String, String, TcpStream) -> F,
) where
    F: Future<Output = ()> + 'a,
{
    let mut buffer = [0; 1024];
    stream.read(&mut buffer).unwrap();

    let get = b"GET / HTTP/1.1\r\n";
    let sleep = b"GET /sleep HTTP/1.1\r\n";

    let (status_line, filename) = if buffer.starts_with(get) {
        ("HTTP/1.1 200 OK", "hello.html")
    } else if buffer.starts_with(sleep) {
        thread::sleep(Duration::from_secs(5));
        ("HTTP/1.1 200 OK", "hello.html")
    } else {
        ("HTTP/1.1 404 NOT FOUND", "404.html")
    };

    let future = test(
        contents,
        String::from(filename),
        String::from(status_line),
        stream,
    );
    runtime.block_on(future);
}
