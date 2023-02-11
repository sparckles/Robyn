use std::sync::RwLock;
use std::{collections::HashMap, collections::HashSet, str::FromStr};

use actix_web::http::Method;

use anyhow::{Context, Result};

type RouteMap = RwLock<HashSet<String>>;

/// Contains the thread safe hashmaps of different routes
pub struct RouteSet {
    routes: HashMap<Method, RouteMap>,
}

impl RouteSet {
    pub fn add_route(
        &self,
        route_type: &str,
        route: &str,
    ) -> Result<()> {
        let table = self
            .get_relevant_map_str(route_type)
            .context("No relevant map")?;

        table.write().unwrap().insert(route.to_string());

        Ok(())
    }

    pub fn has_route(
        &self,
        route_method: &Method,
        route: &str,
    ) -> Option<bool> {
        let table = self.routes.get(route_method)?;
        let route_map = table.read().ok()?;

        Some(route_map.contains(route))
    }

    pub fn new() -> Self {
        let mut routes = HashMap::new();
        routes.insert(Method::GET, RwLock::new(HashSet::new()));
        routes.insert(Method::POST, RwLock::new(HashSet::new()));
        routes.insert(Method::PUT, RwLock::new(HashSet::new()));
        routes.insert(Method::DELETE, RwLock::new(HashSet::new()));
        routes.insert(Method::PATCH, RwLock::new(HashSet::new()));
        routes.insert(Method::HEAD, RwLock::new(HashSet::new()));
        routes.insert(Method::OPTIONS, RwLock::new(HashSet::new()));
        routes.insert(Method::CONNECT, RwLock::new(HashSet::new()));
        routes.insert(Method::TRACE, RwLock::new(HashSet::new()));
        Self { routes }
    }

    #[inline]
    fn get_relevant_map_str(&self, route: &str) -> Option<&RouteMap> {
        match route {
            "WS" => None,
            _ => self.routes.get(&Method::from_str(route).ok()?),
        }
    }
}
