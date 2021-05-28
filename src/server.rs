use crate::router::Router;
use crate::threadpool::ThreadPool;
use std::net::{TcpListener, TcpStream};

pub struct Server {
    port: u32,
    number_of_threads: usize,
    router: Router, //,
    threadpool: ThreadPool,
    listener: TcpListener,
}

impl Server {
    pub fn new(port: u32, number_of_threads: usize) -> Self {
        let url = format!("127.0.0.1:{}", port);
        Self {
            port,
            number_of_threads,
            router: Router::new(),
            threadpool: ThreadPool::new(number_of_threads),
            listener: TcpListener::bind(url).unwrap(),
        }
    }

    pub fn start(&mut self) {
        let listener = self.listener;
        let pool = self.threadpool;

        // test()

        for stream in listener.incoming() {
            let stream = stream.unwrap();

            // need to change on how we are passing the functions in the thread
            pool.execute(|| {
                let rt = tokio::runtime::Runtime::new().unwrap();
                // let mut contents = String::new();
                // handle_connection(stream, rt, &mut contents, &test_helper);
            });
        }
    }
}
