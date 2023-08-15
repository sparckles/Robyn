use env_logger;

pub fn enable_robyn_logs(log_message:&str) {
    if let Ok(enable_logs) = std::env::var("ENABLE_ROBYN_LOGS") {
        if enable_logs.to_lowercase() == "true" {
            env_logger::init();
            println!("{}", log_message);
        }
    }
}