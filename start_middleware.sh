#!/bin/bash
# Start HackApp Middleware

cd "$(dirname "$0")/hackapp"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting HackApp Middleware..."
python3 middleware/main.py
