#!/bin/bash

# Default mode is simulation, but allow test mode
MODE=${1:-simulation}

print_usage() {
    echo "Usage: $0 [simulation|production|test]"
    echo "  simulation  : Run in simulation mode (default)"
    echo "  production : Run in production mode"
    echo "  test       : Run dependency tests only"
}

# Handle arguments
case "$MODE" in
    simulation|production|test)
        ;;
    -h|--help)
        print_usage
        exit 0
        ;;
    *)
        echo "Error: Invalid mode '$MODE'"
        print_usage
        exit 1
        ;;
esac

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system packages based on the platform
install_system_packages() {
    if command_exists apt-get; then
        # Check if we're on a Raspberry Pi
        if [ -f /etc/rpi-issue ]; then
            echo "Installing system packages for Raspberry Pi..."
            sudo apt-get update
            sudo apt-get install -y \
                python3-opencv \
                python3-pip \
                python3-venv \
                cmake \
                build-essential \
                libopencv-dev \
                python3-dev \
                libatlas-base-dev \
                python3-h5py \
                libhdf5-dev \
                libhdf5-serial-dev \
                libv4l-dev \
                libxvidcore-dev \
                libx264-dev \
                libgtk-3-dev \
                pkg-config
        else
            # Regular Debian/Ubuntu
            echo "Installing system packages for Debian-based system..."
            sudo apt-get update
            sudo apt-get install -y \
                python3-opencv \
                python3-pip \
                python3.12-venv \
                cmake \
                build-essential \
                libopencv-dev \
                python3-dev \
                libx11-dev \
                libatlas-base-dev \
                libgtk-3-dev \
                pkg-config
        fi
    elif command_exists pacman; then
        # Arch Linux
        echo "Installing system packages for Arch-based system..."
        sudo pacman -Sy --noconfirm \
            opencv \
            python-pip \
            python-virtualenv \
            cmake \
            base-devel \
            gtk3
    else
        echo "Unsupported package manager. Please install required packages manually."
        exit 1
    fi
}

# Check and install system packages
echo "Checking system dependencies..."
install_system_packages

# Clean up any existing virtual environment
rm -rf .venv

# Create new virtual environment
echo "Creating virtual environment..."
# Use Python 3.12 if available, otherwise fallback to Python 3
if command_exists python3.12; then
    python3.12 -m venv .venv --system-site-packages
else
    python3 -m venv .venv --system-site-packages
fi
source .venv/bin/activate

# Upgrade pip and install Python packages
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Load environment variables from .env
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export OPERATION_MODE=$MODE

# Configure for headless operation if in production mode
if [ "$MODE" = "production" ]; then
    export OPENCV_VIDEOIO_DEBUG=1
    export OPENCV_VIDEOIO_PRIORITY_LIST=v4l2,msmf,dshow
    # Disable GUI if no display is available
    if [ -z "$DISPLAY" ]; then
        export OPENCV_VIDEOIO_PRIORITY_LIST=v4l2
        export OPENCV_HEAD_LESS=1
    fi
fi

# Run the application or tests
if [ "$MODE" = "test" ]; then
    echo "Running dependency tests..."
    python src/test_setup.py
    
    echo -e "\nRunning notification system tests..."
    python src/test_notifications.py
else
    echo "Starting application in $MODE mode..."
    exec python src/main.py
fi
