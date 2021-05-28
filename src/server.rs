use crate::router::Router;
use crate::threadpool::ThreadPool;

pub struct Server {
    port: u32,
    number_of_threads: u32,
    router: Router, //,
    threadpool: ThreadPool,
}

impl Server {
    fn new(port: u32, number_of_threads: u32) -> Self {
        Self {
            port,
            number_of_threads,
            router: Router::new(),
            threadpool: ThreadPool::new(number_of_threads),
        }
    }

    fn start() {}
}
