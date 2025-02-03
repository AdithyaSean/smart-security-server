#!/bin/bash

# Default mode is simulation
MODE=${1:-simulation}

# Check if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set PYTHONPATH to include the src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Export the mode as an environment variable
export OPERATION_MODE=$MODE

# Run the Flask application
python app.py