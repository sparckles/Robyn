use std::collections::HashMap;
use std::fs::File;
use std::io::Read;

use actix_web::HttpResponseBuilder;
use anyhow::Result;
use dashmap::DashMap;

use crate::types::Request;

// this should be something else
// probably inside the submodule of the http router
#[inline]
pub fn apply_hashmap_headers(
    response: &mut HttpResponseBuilder,
    headers: &HashMap<String, String>,
) {
    for (key, val) in headers.iter() {
        response.insert_header((key.clone(), val.clone()));
    }
}

#[inline]
pub fn apply_dashmap_headers(
    response: &mut HttpResponseBuilder,
    headers: &DashMap<String, String>,
) {
    for h in headers.iter() {
        response.insert_header((h.key().clone(), h.value().clone()));
    }
}

#[inline]
pub fn apply_request_dashmap_headers(request: &mut Request, headers: &DashMap<String, String>) {
    for h in headers.iter() {
        request.insert_header(h.key(), h.value());
    }
}

/// A function to read lossy files and serve it as a html response
///
/// # Arguments
///
/// * `file_path` - The file path that we want the function to read
///
// ideally this should be async
pub fn read_file(file_path: &str) -> Result<String> {
    let mut file = File::open(file_path)?;
    let mut buf = vec![];
    file.read_to_end(&mut buf)?;
    Ok(String::from_utf8_lossy(&buf).to_string())
}
