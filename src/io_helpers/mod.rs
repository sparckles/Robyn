use std::fs::File;
use std::io::Read;

use actix_web::HttpResponseBuilder;
use anyhow::Result;

use crate::types::headers::Headers;

// this should be something else
// probably inside the submodule of the http router
#[inline]
pub fn apply_hashmap_headers(response: &mut HttpResponseBuilder, headers: &Headers) {
    for iter in headers.headers.iter() {
        let (key, values) = iter.pair();
        for value in values {
            response.append_header((key.clone(), value.clone()));
        }
    }
}

/// A function to read lossy files and serve it as a html response
///
/// # Arguments
///
/// * `file_path` - The file path that we want the function to read
///
// ideally this should be async
pub fn read_file(file_path: &str) -> Result<Vec<u8>> {
    let mut file = File::open(file_path)?;
    let mut buf = vec![];
    file.read_to_end(&mut buf)?;
    Ok(buf)
}
