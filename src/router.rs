use dashmap::DashMap;
// pyo3 modules
use pyo3::prelude::*;

pub enum RouteType {
    Route((String, String)),
    Buffer(Box<[u8]>),
}

#[derive(PartialEq, Eq, Hash, Debug)]
pub struct Route {
    route: String,
    route_type: String,
}

impl Route {
    pub fn new(route: RouteType) -> Self {
        match route {
            RouteType::Buffer(buffer) => {
                let stream = String::from_utf8((&buffer).to_vec()).unwrap();

                let mut route_type = "";
                if stream.contains("GET") {
                    route_type = "GET";
                } else if stream.contains("POST") {
                    route_type = "POST";
                } else if stream.contains("PUT") {
                    route_type = "PUT";
                } else if stream.contains("UPDATE") {
                    route_type = "UPDATE";
                } else if stream.contains("DELETE") {
                    route_type = "DELETE";
                } else if stream.contains("PATCH") {
                    route_type = "PATCH";
                }

                let stream = stream
                    .split_whitespace()
                    .filter(|x| x.starts_with("/"))
                    .nth(0)
                    .unwrap();

                Self {
                    route: stream.to_string(),
                    route_type: String::from(route_type),
                }
            }
            RouteType::Route((route, route_type)) => Self { route, route_type },
        }
    }

    pub fn get_route(&self) -> String {
        self.route.clone()
    }

    pub fn get_route_type(&self) -> String {
        self.route_type.clone()
    }
}

// this should ideally be a hashmap of hashmaps but not really

pub struct Router {
    get_routes: DashMap<Route, Py<PyAny>>,
    post_routes: DashMap<Route, Py<PyAny>>,
    put_routes: DashMap<Route, Py<PyAny>>,
    update_routes: DashMap<Route, Py<PyAny>>,
    delete_routes: DashMap<Route, Py<PyAny>>,
    patch_routes: DashMap<Route, Py<PyAny>>,
}
// these should be of the type struct and not the type router
// request_stream: &TcpStream,
// request_type: Option<RequestType>,
// headers: Vec<String>,
// body: Vec<String>

impl Router {
    pub fn new() -> Self {
        Self {
            get_routes: DashMap::new(),
            post_routes: DashMap::new(),
            put_routes: DashMap::new(),
            update_routes: DashMap::new(),
            delete_routes: DashMap::new(),
            patch_routes: DashMap::new(),
        }
    }

    #[inline]
    fn get_relevant_map(&self, route: &str) -> Option<&DashMap<Route, Py<PyAny>>> {
        match route {
            "GET" => Some(&self.get_routes),
            "POST" => Some(&self.post_routes),
            "PUT" => Some(&self.put_routes),
            "UPDATE" => Some(&self.update_routes),
            "DELETE" => Some(&self.delete_routes),
            "PATCH" => Some(&self.patch_routes),
            _ => None,
        }
    }

    pub fn add_route(&self, route_type: &str, route: Route, handler: Py<PyAny>) {
        let table = match self.get_relevant_map(route_type) {
            Some(table) => table,
            None => return,
        };

        table.insert(route, handler);
    }

    pub fn get_route(&self, route: Route) -> Option<Py<PyAny>> {
        let table = self.get_relevant_map(route.get_route_type().as_str())?;
        Some(table.get(&route)?.clone())
    }
}
