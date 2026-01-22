use actix_web::cookie::{Cookie as ActixCookie, SameSite};
use pyo3::prelude::*;
use std::collections::HashMap;
use std::fmt;

/// Error type for cookie validation failures
#[derive(Debug, Clone)]
pub enum CookieError {
    InvalidSameSite(String),
    InvalidCookie(String),
}

impl fmt::Display for CookieError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CookieError::InvalidSameSite(msg) => write!(f, "Invalid SameSite value: {}", msg),
            CookieError::InvalidCookie(msg) => write!(f, "Invalid cookie: {}", msg),
        }
    }
}

impl std::error::Error for CookieError {}

/// A cookie with optional attributes following RFC 6265
#[pyclass(name = "Cookie")]
#[derive(Debug, Clone)]
pub struct Cookie {
    #[pyo3(get, set)]
    pub value: String,
    #[pyo3(get, set)]
    pub path: Option<String>,
    #[pyo3(get, set)]
    pub domain: Option<String>,
    #[pyo3(get, set)]
    pub max_age: Option<i64>,
    #[pyo3(get, set)]
    pub expires: Option<String>, // RFC 7231 date format
    #[pyo3(get, set)]
    pub secure: bool,
    #[pyo3(get, set)]
    pub http_only: bool,
    #[pyo3(get, set)]
    pub same_site: Option<String>, // "Strict", "Lax", or "None"
}

#[pymethods]
impl Cookie {
    #[new]
    #[pyo3(signature = (value, path=None, domain=None, max_age=None, expires=None, secure=false, http_only=false, same_site=None))]
    pub fn new(
        value: String,
        path: Option<String>,
        domain: Option<String>,
        max_age: Option<i64>,
        expires: Option<String>,
        secure: bool,
        http_only: bool,
        same_site: Option<String>,
    ) -> Self {
        Self {
            value,
            path,
            domain,
            max_age,
            expires,
            secure,
            http_only,
            same_site,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Cookie(value={:?}, path={:?}, domain={:?}, max_age={:?}, expires={:?}, secure={}, http_only={}, same_site={:?})",
            self.value, self.path, self.domain, self.max_age, self.expires, self.secure, self.http_only, self.same_site
        )
    }
}

impl Cookie {
    /// Serialize cookie to Set-Cookie header value format.
    ///
    /// Uses actix-web's cookie crate for RFC 6265 compliant serialization
    /// which handles proper validation and encoding of cookie values.
    ///
    /// Returns an error if SameSite has an invalid value.
    pub fn to_header_value(&self, name: &str) -> Result<String, CookieError> {
        // Use actix-web's cookie builder for RFC 6265 compliant serialization
        let mut builder = ActixCookie::build(name, &self.value);

        if let Some(ref path) = self.path {
            builder = builder.path(path.clone());
        }
        if let Some(ref domain) = self.domain {
            builder = builder.domain(domain.clone());
        }
        if let Some(max_age) = self.max_age {
            builder = builder.max_age(actix_web::cookie::time::Duration::seconds(max_age));
        }
        // Note: expires requires parsing the date string; for now we skip it
        // as max_age is the preferred modern approach
        if self.secure {
            builder = builder.secure(true);
        }
        if self.http_only {
            builder = builder.http_only(true);
        }
        if let Some(ref same_site) = self.same_site {
            let same_site_value = match same_site.as_str() {
                "Strict" => SameSite::Strict,
                "Lax" => SameSite::Lax,
                "None" => SameSite::None,
                _ => {
                    return Err(CookieError::InvalidSameSite(format!(
                        "must be 'Strict', 'Lax', or 'None', got '{}'",
                        same_site
                    )))
                }
            };
            builder = builder.same_site(same_site_value);
        }

        Ok(builder.finish().to_string())
    }
}

/// A collection of cookies keyed by name
#[pyclass(name = "Cookies")]
#[derive(Debug, Clone, Default)]
pub struct Cookies {
    pub cookies: HashMap<String, Cookie>,
}

#[pymethods]
impl Cookies {
    #[new]
    pub fn new() -> Self {
        Self {
            cookies: HashMap::new(),
        }
    }

    pub fn set(&mut self, name: String, cookie: Cookie) {
        self.cookies.insert(name, cookie);
    }

    pub fn get(&self, name: String) -> Option<Cookie> {
        self.cookies.get(&name).cloned()
    }

    pub fn remove(&mut self, name: &str) {
        self.cookies.remove(name);
    }

    pub fn is_empty(&self) -> bool {
        self.cookies.is_empty()
    }

    pub fn len(&self) -> usize {
        self.cookies.len()
    }

    pub fn __setitem__(&mut self, name: String, cookie: Cookie) {
        self.set(name, cookie);
    }

    pub fn __getitem__(&self, name: String) -> Option<Cookie> {
        self.get(name)
    }

    pub fn __contains__(&self, name: String) -> bool {
        self.cookies.contains_key(&name)
    }

    pub fn __len__(&self) -> usize {
        self.len()
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.cookies)
    }
}
