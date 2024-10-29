#!/bin/bash

# Enable core dumps
ulimit -c unlimited
echo '/tmp/core.%e.%p' | sudo tee /proc/sys/kernel/core_pattern

# Run tests with xvfb
xvfb-run -a pytest -v test_minimal.py || true

# List files in /tmp to check for core dumps
ls -l /tmp
