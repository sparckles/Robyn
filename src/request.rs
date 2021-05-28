use std::net::TcpStream;

pub struct Request {
    stream: TcpStream,
}

impl Request {
    pub fn new(stream: TcpStream) -> Self {
        Self { stream }
    }
}
