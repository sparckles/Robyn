use crossbeam::channel::{unbounded, Receiver, Sender};
use std::io::Error;
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

// pyO3 module
use pyo3::prelude::*;

struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize, receiver: Receiver<Message>) -> Worker {
        // It is recommended to *always* immediately set py to the pool's Python, to help
        // avoid creating references with invalid lifetimes.
        // let pool = unsafe { py.new_pool() };
        // let m = Mutex::new(pool);
        // let rt = tokio::runtime::Runtime::new().unwrap();

        let t = thread::spawn(move || {
            let py = unsafe { Python::assume_gil_acquired() };
            // pyo3_asyncio::tokio::init_current_thread();
            // let py = m.lock().unwrap();
            // let py = unsafe { pool.python() };
            // pool.python();
            // let pool = unsafe { py.new_pool() };
            // It is recommended to *always* immediately set py to the pool's Python, to help
            // avoid creating references with invalid lifetimes.
            // let py = unsafe { pool.python() };
            // pyo3_asyncio::tokio::get_runtime();

            loop {
                let message = receiver.recv().unwrap(); // message should be the optional containing the future
                match message {
                    Message::NewJob(j) => {
                        let coro = j.as_ref(py).call0().unwrap();
                        let f = pyo3_asyncio::into_future(&coro).unwrap();

                        pyo3_asyncio::async_std::run_until_complete(py, async move {
                            let x = f.await;
                            match x {
                                Err(x) => println!(" {}", x), // I am getting the error here
                                Ok(_) => (),
                            };
                            Ok(())
                        })
                        .unwrap();
                        // async_std::task::block_on(async move {
                        //     let x = f.await;
                        //     match (x) {
                        //         Err(x) => println!(" {}", x), // I am getting the error here
                        //         Ok(_) => (),
                        //     };
                        // });
                        // pyo3_asyncio::tokio::run_until_complete(py, async move {
                        //     println!("Hello world from rust");
                        //     f.await?;
                        //     Ok(())
                        // })
                        // .unwrap();
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
    NewJob(Py<PyAny>),
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

        // let receiver = Arc::new(Mutex::new(receiver));

        let mut workers = Vec::with_capacity(size);
        // let gil = Python::acquire_gil();
        // let py = gil.python();

        for id in 0..size {
            // let pool = unsafe { py.new_pool() };
            // It is recommended to *always* immediately set py to the pool's Python, to help
            // avoid creating references with invalid lifetimes.
            // let py = unsafe { pool.python() };
            workers.push(Worker::new(id, receiver.clone()));
        }

        ThreadPool { workers, sender }
    }

    pub fn push_async(&self, f: &Py<PyAny>)
    // where
    //     F: PyFuture<'static>,
    // F: Future<Output = ()> + Send + 'static + Sync,
    // F: FnOnce() + Send + 'static + Sync
    {
        // println!("Sending a message");
        self.sender.send(Message::NewJob(f.clone())).unwrap();
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
