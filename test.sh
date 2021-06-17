#!/bin/sh

cargo build --release
cp target/release/librobyn.dylib ./robyn.so
python3 test.py
