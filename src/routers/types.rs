#[derive(Debug)]
pub enum MiddlewareRouteType {
    BeforeRequest,
    AfterRequest,
}

impl MiddlewareRouteType {
    pub fn from_str(input: &str) -> MiddlewareRouteType {
        match input {
            "BEFORE_REQUEST" => MiddlewareRouteType::BeforeRequest,
            "AFTER_REQUEST" => MiddlewareRouteType::AfterRequest,
            _ => panic!("Invalid route type enum."),
        }
    }
}
