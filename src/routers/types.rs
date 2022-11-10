#[derive(Debug, PartialEq, Eq, Hash)]
pub enum MiddlewareRoute {
    BeforeRequest,
    AfterRequest,
}

impl MiddlewareRoute {
    pub fn from_str(input: &str) -> MiddlewareRoute {
        match input {
            "BEFORE_REQUEST" => MiddlewareRoute::BeforeRequest,
            "AFTER_REQUEST" => MiddlewareRoute::AfterRequest,
            _ => panic!("Invalid route type enum."),
        }
    }
}
