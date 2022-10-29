use pyo3::prelude::*;

use log::debug;
use socket2::{Domain, Protocol, Socket, Type};
use std::net::{IpAddr, SocketAddr};

#[pyclass]
#[derive(Debug)]
pub struct SocketHeld {
    pub socket: Socket,
}

#[pymethods]
impl SocketHeld {
    #[new]
    pub fn new(ip: String, port: u16) -> PyResult<SocketHeld> {
        let ip: IpAddr = ip.parse()?;
        let socket = if ip.is_ipv4() {
            Socket::new(Domain::IPV4, Type::STREAM, Some(Protocol::TCP))?
        } else {
            Socket::new(Domain::IPV6, Type::STREAM, Some(Protocol::TCP))?
        };
        let address = SocketAddr::new(ip, port);
        debug!("{}", address);
        // reuse port is not available on windows
        #[cfg(not(target_os = "windows"))]
        socket.set_reuse_port(true)?;

        socket.set_reuse_address(true)?;
        socket.bind(&address.into())?;
        socket.listen(1024)?;

        Ok(SocketHeld { socket })
    }

    pub fn try_clone(&self) -> PyResult<SocketHeld> {
        let copied = self.socket.try_clone()?;
        Ok(SocketHeld { socket: copied })
    }
}

impl SocketHeld {
    pub fn get_socket(&self) -> Socket {
        self.socket.try_clone().unwrap()
    }
}
