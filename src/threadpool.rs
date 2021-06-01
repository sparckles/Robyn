use futures::Future;
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use tokio;

// pyO3 module
use pyo3::prelude::*;

use crate::types::{AsyncFunction, Job, PyFuture};

#[pyclass]
struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Message>>>) -> Worker {
        let t = thread::spawn(move || {
            let rt = tokio::runtime::Runtime::new().unwrap();
            pyo3_asyncio::tokio::init(rt);
            // let v = pyo3_asyncio::tokio::get_runtime();
            loop {
                let message = receiver.lock().unwrap().recv().unwrap(); // message should be the optional containing the future

                match message {
                    Message::NewJob(job) => {
                        println!("Worker {} got a job; executing.", id);
                        Python::with_gil(|py| {
                            pyo3_asyncio::tokio::run_until_complete(py, async {
                                let j: PyAny = job.into();
                                let f = pyo3_asyncio::into_future(&job).unwrap();

                                f.await;
                                // (*job).await;
                                Ok(())
                            })
                            .unwrap();
                        });
                    }

                    Message::Terminate => {
                        println!("Worker {} was told to terminate.", id);
                        break;
                    }
                }
            }
        });

        // let thread = thread::spawn(move || loop {
        //     // need to create a method to initialize the runtime here
        //     // inside that runtime need a way to fetch that message
        //     // and complete it
        //     // stream will be sent along side
        //     let message = receiver.lock().unwrap().recv().unwrap();

        // });

        Worker {
            id,
            thread: Some(t),
        }
    }
}

type Test = Box<dyn FnOnce() + Send + 'static>;

pub enum Message {
    NewJob(Py<PyAny>),
    Terminate,
}

pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: mpsc::Sender<Message>,
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

        let (sender, receiver) = mpsc::channel();

        let receiver = Arc::new(Mutex::new(receiver));

        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool { workers, sender }
    }

    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);

        // self.sender.send(Message::NewJob(job)).unwrap();
    }

    pub fn push_async(&self, f: Py<PyAny>)
    // where
    //     F: PyFuture<'static>,
    // F: Future<Output = ()> + Send + 'static + Sync,
    // F: FnOnce() + Send + 'static + Sync
    {
        self.sender.send(Message::NewJob(f)).unwrap();
    }
    // pub fn push_async(&self, f: &'static PyFuture) {
    //     // let job = pyo3_asyncio::into_future(f).unwrap();
    // }
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
