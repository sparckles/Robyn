use std::collections::HashMap;
use std::sync::{Arc, Mutex};

pub type MemoryStore = Arc<Mutex<HashMap<String, Vec<u32>>>>;

pub fn get_calls_count(
    memory_store: &MemoryStore,
    limit_key: String,
    limit_ttl: u32,
    current_timestamp: u32
) -> usize {
    let mut cache = memory_store.lock().unwrap();
    let ttl = current_timestamp - limit_ttl;
    if let Some(timestamps) = cache.get_mut(&limit_key) {
        let mut valid_timestamps: Vec<u32> = timestamps
            .iter()
            .copied()
            .filter(|timestamp| timestamp >= &&ttl)
            .collect();
        valid_timestamps.push(current_timestamp);
        *timestamps = valid_timestamps;
    } else {
        cache.insert(limit_key.to_owned(), vec![current_timestamp]);
    }

    cache.get(&limit_key).unwrap().len()
}
