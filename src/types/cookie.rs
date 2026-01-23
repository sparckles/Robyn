use actix_web::cookie::{Cookie as ActixCookie, SameSite};
use log::debug;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::fmt;

/// Error type for cookie validation failures
#[derive(Debug, Clone)]
pub enum CookieError {
    InvalidSameSite(String),
}

impl fmt::Display for CookieError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CookieError::InvalidSameSite(msg) => write!(f, "Invalid SameSite value: {}", msg),
        }
    }
}

impl std::error::Error for CookieError {}

/// Parse SameSite value (case-insensitive)
fn parse_same_site(value: &str) -> Result<SameSite, CookieError> {
    match value.to_lowercase().as_str() {
        "strict" => Ok(SameSite::Strict),
        "lax" => Ok(SameSite::Lax),
        "none" => Ok(SameSite::None),
        _ => Err(CookieError::InvalidSameSite(format!(
            "must be 'Strict', 'Lax', or 'None', got '{}'",
            value
        ))),
    }
}

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
    pub expires: Option<String>,
    #[pyo3(get, set)]
    pub secure: bool,
    #[pyo3(get, set)]
    pub http_only: bool,
    #[pyo3(get, set)]
    pub same_site: Option<String>,
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

    /// Create a cookie configured for deletion (expires immediately with max_age=0)
    #[staticmethod]
    pub fn deleted() -> Self {
        Self {
            value: String::new(),
            path: Some("/".to_string()),
            domain: None,
            max_age: Some(0),
            expires: None,
            secure: false,
            http_only: false,
            same_site: None,
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
        // Note: expires is skipped as max_age is the modern/preferred approach
        // The expires field is kept for API compatibility but not used in serialization
        if self.expires.is_some() {
            debug!("Cookie 'expires' attribute is deprecated; use 'max_age' instead");
        }
        if self.secure {
            builder = builder.secure(true);
        }
        if self.http_only {
            builder = builder.http_only(true);
        }
        if let Some(ref same_site) = self.same_site {
            builder = builder.same_site(parse_same_site(same_site)?);
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

    /// Set a cookie with the given name
    pub fn set(&mut self, name: String, cookie: Cookie) {
        self.cookies.insert(name, cookie);
    }

    /// Get a cookie by name
    pub fn get(&self, name: String) -> Option<Cookie> {
        self.cookies.get(&name).cloned()
    }

    /// Remove a cookie from the collection (does not delete it from the browser)
    pub fn remove(&mut self, name: &str) {
        self.cookies.remove(name);
    }

    /// Mark a cookie for deletion by setting it to expire immediately.
    /// This sets max_age=0 which tells the browser to delete the cookie.
    pub fn delete(&mut self, name: String) {
        self.cookies.insert(name, Cookie::deleted());
    }

    /// Check if the collection is empty
    pub fn is_empty(&self) -> bool {
        self.cookies.is_empty()
    }

    /// Get the number of cookies
    pub fn len(&self) -> usize {
        self.cookies.len()
    }

    /// Get all cookie names
    pub fn keys(&self) -> Vec<String> {
        self.cookies.keys().cloned().collect()
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

    pub fn __iter__(slf: PyRef<'_, Self>) -> CookiesIter {
        CookiesIter {
            keys: slf.cookies.keys().cloned().collect(),
            index: 0,
        }
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.cookies)
    }
}

/// Iterator for Cookies collection
#[pyclass]
pub struct CookiesIter {
    keys: Vec<String>,
    index: usize,
}

#[pymethods]
impl CookiesIter {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<String> {
        if slf.index < slf.keys.len() {
            let key = slf.keys[slf.index].clone();
            slf.index += 1;
            Some(key)
        } else {
            None
        }
    }
}
