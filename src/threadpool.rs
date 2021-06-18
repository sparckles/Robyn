use crossbeam::channel::{unbounded, Receiver, Sender};
use std::io::prelude::*;
use std::net::TcpStream;
use std::thread;

// pyO3 module
use pyo3::prelude::*;
use pyo3::types::PyList;

struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize, receiver: Receiver<Message>) -> Worker {
        let t = thread::spawn(move || {
            loop {
                let message = receiver.recv().unwrap(); // message should be the optional containing the future
                match message {
                    Message::NewJob(mess) => {
                        let (handler, stream) = mess;
                        let mut stream = stream;
                        let f = Python::with_gil(|py| {
                            let coro = handler.as_ref(py).call0().unwrap();
                            pyo3_asyncio::into_future(&coro).unwrap()
                        });

                        // let mut buffer = [0; 1024];
                        // stream.read(&mut buffer).unwrap();
                        async_std::task::spawn(async move {
                            let output = f.await.unwrap();
                            let status_line = "HTTP/1.1 200 OK";
                            Python::with_gil(|py| {
                                let contents: &str = output.extract(py).unwrap();

                                let len = contents.len();
                                let response = format!(
                                    "{}\r\nContent-Length: {}\r\n\r\n{}",
                                    status_line, len, contents
                                );

                                stream.write(response.as_bytes()).unwrap();
                                stream.flush().unwrap();
                            });
                        });
                    }
                    Message::Terminate => {
                        println!("Worker has been told to terminale");
                    }
                }
            }
        });

        Worker {
            id,
            thread: Some(t),
        }
    }
}

// type Test = Box<dyn FnOnce() + Send + 'static>;

pub enum Message {
    NewJob((Py<PyAny>, TcpStream)),
    Terminate,
}

pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Sender<Message>,
}

impl ThreadPool {
    /// Create a new ThreadPool.
    ///
    /// The size is the number of threads in the pool.
    ///
    /// # Panics
    ///
    /// The `new` function will panic if the size is zero.
    pub fn new(size: usize) -> ThreadPool {
        assert!(size > 0);

        let (sender, receiver) = unbounded();

        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, receiver.clone()));
        }

        ThreadPool { workers, sender }
    }

    pub fn push_async(&self, f: Py<PyAny>, stream: TcpStream) {
        // println!("Sending a message");
        self.sender.send(Message::NewJob((f, stream))).unwrap();
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        println!("Sending terminate message to all workers.");

        for _ in &self.workers {
            self.sender.send(Message::Terminate).unwrap();
        }

        println!("Shutting down all workers.");

        for worker in &mut self.workers {
            println!("Shutting down worker {}", worker.id);

            if let Some(thread) = worker.thread.take() {
                thread.join().unwrap();
            }
        }
    }
}
