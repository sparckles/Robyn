#!/bin/bash

set -x

maturin develop
poetry lock 
