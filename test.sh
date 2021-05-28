#!/bin/sh

cargo build --release
cp target/release/libroadrunner.dylib ./roadrunner.so
python3 test.py
