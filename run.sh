#!/bin/bash

# Function to check if Python packages are installed
check_python_packages() {
    source .venv/bin/activate 2>/dev/null || return 1
    pip freeze | grep -q "^fastapi==\|^uvicorn==\|^requests==" || return 1
    return 0
}

# Check if we need to install/reinstall dependencies
if [ ! -d ".venv" ] || ! check_python_packages; then
    echo "Setting up virtual environment and installing dependencies..."
    rm -rf .venv
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
else
    echo "Dependencies already installed. Activating virtual environment..."
    source .venv/bin/activate
fi

# Load environment variables from .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Starting server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 2003
