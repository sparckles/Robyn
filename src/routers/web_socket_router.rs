use parking_lot::RwLock;
use std::collections::HashMap;

use log::debug;

use crate::types::function_info::FunctionInfo;

/// Contains the thread safe hashmaps of different routes
type WebSocketRoutes = RwLock<HashMap<String, HashMap<String, FunctionInfo>>>;
/// Tracks which endpoints use the new channel-based message delivery
type WebSocketChannelFlags = RwLock<HashMap<String, bool>>;

pub struct WebSocketRouter {
    web_socket_routes: WebSocketRoutes,
    channel_flags: WebSocketChannelFlags,
}

impl WebSocketRouter {
    pub fn new() -> Self {
        Self {
            web_socket_routes: RwLock::new(HashMap::new()),
            channel_flags: RwLock::new(HashMap::new()),
        }
    }

    #[inline]
    pub fn get_web_socket_map(&self) -> &WebSocketRoutes {
        &self.web_socket_routes
    }

    #[inline]
    pub fn get_channel_flags(&self) -> &WebSocketChannelFlags {
        &self.channel_flags
    }

    // Checks if the functions is an async function
    // Inserts them in the router according to their nature(CoRoutine/SyncFunction)
    pub fn add_websocket_route(
        &self,
        route: &str,
        connect_route: FunctionInfo,
        close_route: FunctionInfo,
        message_route: FunctionInfo,
        use_channel: bool,
    ) {
        let table = self.get_web_socket_map();

        let insert_in_router = |function: FunctionInfo, socket_type: &str| {
            debug!("socket type is {:?} {:?}", table, route);

            table
                .write()
                .entry(route.to_string())
                .or_default()
                .insert(socket_type.to_string(), function)
        };

        insert_in_router(connect_route, "connect");
        insert_in_router(close_route, "close");
        insert_in_router(message_route, "message");

        self.channel_flags
            .write()
            .insert(route.to_string(), use_channel);
    }
}
