use pyo3::prelude::*;
use std::collections::HashMap;

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
    /// Serialize cookie to Set-Cookie header value format
    pub fn to_header_value(&self, name: &str) -> String {
        let mut parts = vec![format!("{}={}", name, self.value)];

        if let Some(ref path) = self.path {
            parts.push(format!("Path={}", path));
        }
        if let Some(ref domain) = self.domain {
            parts.push(format!("Domain={}", domain));
        }
        if let Some(max_age) = self.max_age {
            parts.push(format!("Max-Age={}", max_age));
        }
        if let Some(ref expires) = self.expires {
            parts.push(format!("Expires={}", expires));
        }
        if self.secure {
            parts.push("Secure".to_string());
        }
        if self.http_only {
            parts.push("HttpOnly".to_string());
        }
        if let Some(ref same_site) = self.same_site {
            parts.push(format!("SameSite={}", same_site));
        }

        parts.join("; ")
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

