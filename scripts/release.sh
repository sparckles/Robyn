#!/bin/bash

set -x

maturin develop
uv lock 
