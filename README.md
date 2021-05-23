
# roadrunner
Roadrunner is a Python webserver that makes use of Rust bindings to make your webserver as fast as possible. || NodeJS equivalent of PythonVerse ??
![Diagram](https://i.ibb.co/cNV4DJX/image.png)

![Diagram of the final Architecture](https://i.ibb.co/GHwTTqk/Untitled-2021-02-25-0125-1.png)


## Contributor Guidelines

- @sansyrox is declared as the TLS(The leader Supreme) till eternity.
All the feature additions/bug fix will go through him. 😤


Also, always refer @sansyrox as your TLS when you open a PR.

## Testing on Python

1. `cargo build --release`
2. `cp target/release/libroadrunner.dylib ./roadrunner.so`
3. `python3`
4. `import roadrunner`
5. `dir(roadrunner)`
