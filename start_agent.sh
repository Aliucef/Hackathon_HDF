#!/bin/bash
# Start HackApp Agent

cd "$(dirname "$0")/hackapp"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting HackApp Agent..."
python3 agent/main.py
