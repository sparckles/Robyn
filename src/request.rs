use std::io::prelude::*;
use std::net::TcpStream;

#[derive(Copy, Clone, Debug)]
pub enum RequestType {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    UPDATE,
}

#[derive(Debug)]
pub struct Request {
    request_type: RequestType,
}

impl Request {
    pub fn new(buffer: &[u8]) -> Self {
        let request_type = if buffer.starts_with(b"GET") {
            RequestType::GET
        } else if buffer.starts_with(b"POST") {
            RequestType::POST
        } else if buffer.starts_with(b"PUT") {
            RequestType::PUT
        } else if buffer.starts_with(b"PATCH") {
            RequestType::PATCH
        } else if buffer.starts_with(b"DELETE") {
            RequestType::DELETE
        } else {
            RequestType::UPDATE
        };

        Self { request_type }
    }

    pub fn request_type(&self) -> RequestType {
        self.request_type
    }
}
