# Robyn

Robyn is a Python webserver that makes use of Rust bindings to make your webserver as fast as possible. || NodeJS equivalent of PythonVerse ??

Python server running on top of of Rust Async RunTime.

![Diagram](https://i.ibb.co/cNV4DJX/image.png)

![Diagram of the final Architecture](https://i.ibb.co/GHwTTqk/Untitled-2021-02-25-0125-1.png)

## Contributor Guidelines

Feel free to open an issue for any clarification or for any suggestions.

## Testing on Python

1. `cargo build --release`
2. `cp target/release/librobyn.dylib ./robyn.so`
3. `python3`
4. `import robyn`
5. `dir(robyn)`

## To Run

1. Add more routes in the test.py file(if you like). It only supports only get requests at the moment

2. Run `maturin develop`

3. Run `python3 test.py`

4. To measure the performance: `./server_test.sh`
