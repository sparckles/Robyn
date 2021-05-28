use std::net::TcpStream;

pub struct Response {
    stream: TcpStream,
    handler: Box<&PyAny>,
}

impl Response {
    pub fn new(stream: TcpStream, handler: &PyAny) -> Self {
        Self {
            stream,
            handler: Box::new(handler),
        }
    }
}
