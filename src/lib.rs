use std::thread;
mod request;
mod router;
mod server;
mod threadpool;
mod types;

use threadpool::ThreadPool;

use server::Server;
use std::io::prelude::*;
use std::net::TcpListener;
use std::net::TcpStream;
use std::time::Duration;

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3::wrap_pyfunction;

use std::future::Future;

// #[pyclass]
// struct Server {}

// #[pymethods]
// impl Server {
//     #[new]
//     fn new() -> Self {
//         Self {}
//     }

//     fn start(mut self_: PyRefMut<Self>, test: &PyAny) {
//         // let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
//         // let pool = ThreadPool::new(4);

//         let f = pyo3_asyncio::into_future(test).unwrap();

//         let rt = tokio::runtime::Runtime::new().unwrap();
//         // let rt = pyo3_asyncio::tokio::get_runtime();
//         pyo3_asyncio::tokio::init(rt);
//         // let v = pyo3_asyncio::tokio::get_runtime();
//         Python::with_gil(|py| {
//             pyo3_asyncio::tokio::run_until_complete(py, async move {
//                 tokio::time::sleep(Duration::from_secs(1)).await;
//                 f.await.unwrap();
//                 Ok(())
//             })
//             .unwrap();
//         });
//     }
// }

#[pyfunction]
pub fn start_server() {
    let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
    let pool = ThreadPool::new(4);

    // test()

    for stream in listener.incoming() {
        let stream = stream.unwrap();

        pool.execute(|| {
            let rt = tokio::runtime::Runtime::new().unwrap();
            let mut contents = String::new();
            handle_connection(stream, rt, &mut contents, &test_helper);
        });
    }
}

#[pymodule]
pub fn roadrunner(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(start_server))?;
    m.add_class::<Server>()?;
    pyo3_asyncio::try_init(py).unwrap();

    Ok(())
}

async fn read_file(filename: String) -> String {
    let con = tokio::fs::read_to_string(filename).await;
    con.unwrap()
}

async fn test_helper(
    contents: &mut String,
    filename: String,
    status_line: String,
    mut stream: TcpStream,
) {
    // this function will accept custom function and return
    *contents = tokio::task::spawn(read_file(filename.clone()))
        .await
        .unwrap();

    let len = contents.len();

    let response = format!(
        "{}\r\nContent-Length: {}\r\n\r\n{}",
        status_line, len, contents
    );

    stream.write(response.as_bytes()).unwrap();
    stream.flush().unwrap();
    // return String::from(contents.clone());
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
