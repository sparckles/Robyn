use roadrunner::ThreadPool;
// use std::fs;
use std::io::prelude::*;
use std::net::TcpListener;
use std::net::TcpStream;
use std::thread;
use std::time::Duration;

// pyO3 module
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyfunction]
fn start_server() {
    let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
    let pool = ThreadPool::new(4);

    for stream in listener.incoming() {
        let stream = stream.unwrap();

        pool.execute(|| {
            let rt = tokio::runtime::Runtime::new().unwrap();
            handle_connection(stream, rt);
        });
    }
}

#[pymodule]
fn roadrunner(_: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(start_server))?;
    Ok(())
}

fn main() {
    let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
    let pool = ThreadPool::new(4);

    for stream in listener.incoming() {
        let stream = stream.unwrap();

        pool.execute(|| {
            let rt = tokio::runtime::Runtime::new().unwrap();
            handle_connection(stream, rt);
        });
    }
}

async fn read_file(filename: String) -> String {
    let con = tokio::fs::read_to_string(filename).await;
    con.unwrap()
}

async fn test_helper(contents: &mut String, filename: String) {
    *contents = tokio::task::spawn(read_file(filename.clone()))
        .await
        .unwrap();
}

fn handle_connection(mut stream: TcpStream, runtime: tokio::runtime::Runtime) {
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

    let mut contents = String::new();
    let future = test_helper(&mut contents, String::from(filename));
    runtime.block_on(future);

    let response = format!(
        "{}\r\nContent-Length: {}\r\n\r\n{}",
        status_line,
        contents.len(),
        contents
    );

    stream.write(response.as_bytes()).unwrap();
    stream.flush().unwrap();
}
