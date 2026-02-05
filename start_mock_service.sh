#!/bin/bash
# Start Mock External Service

cd "$(dirname "$0")/hackapp"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting Mock External Service..."
python3 mock_service/app.py
