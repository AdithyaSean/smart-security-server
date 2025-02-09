#!/bin/bash

# Remote Raspberry Pi details
PI_HOST="adithya.local"
PI_USER="adithya"
PI_DIR="/home/adithya/smart-security-server"

# Local project directory
LOCAL_DIR="$(pwd)"

echo "Preparing to deploy to Raspberry Pi..."

# Function to run commands on the Pi
run_on_pi() {
    ssh $PI_USER@$PI_HOST "$1"
}

# 1. Install Raspberry Pi specific dependencies
install_pi_deps() {
    echo "Installing Raspberry Pi dependencies..."
    run_on_pi "sudo apt-get update && \
               sudo apt-get install -y \
               python3-pip \
               python3-venv \
               cmake \
               build-essential \
               libopencv-dev \
               python3-opencv \
               libatlas-base-dev \
               python3-h5py \
               libhdf5-dev \
               libhdf5-serial-dev \
               libqtgui4 \
               libqt4-test \
               libilmbase-dev \
               libopenexr-dev \
               libgstreamer1.0-dev \
               libavcodec-dev \
               libavformat-dev \
               libswscale-dev \
               libv4l-dev"
}

# 2. Create systemd service file for automatic startup
create_service_file() {
    echo "Creating systemd service file..."
    cat > smart-security.service << EOF
[Unit]
Description=Smart Security System
After=network.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$PI_DIR
Environment=DISPLAY=:0
Environment=PYTHONPATH=$PI_DIR/src
ExecStart=/bin/bash $PI_DIR/run.sh production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Copy service file to Pi
    scp smart-security.service $PI_USER@$PI_HOST:/tmp/
    run_on_pi "sudo mv /tmp/smart-security.service /etc/systemd/system/"
    rm smart-security.service
}

# 3. Deploy application
deploy_app() {
    echo "Backing up existing installation..."
    run_on_pi "[ -d $PI_DIR ] && mv $PI_DIR ${PI_DIR}_backup_$(date +%Y%m%d_%H%M%S) || true"

    echo "Copying application files..."
    # Create directory and copy files
    run_on_pi "mkdir -p $PI_DIR"
    scp -r ./* $PI_USER@$PI_HOST:$PI_DIR/

    echo "Setting up Python virtual environment..."
    run_on_pi "cd $PI_DIR && \
               python3 -m venv .venv && \
               source .venv/bin/activate && \
               pip install --upgrade pip && \
               pip install -r requirements.txt"

    echo "Setting up service..."
    run_on_pi "sudo systemctl daemon-reload && \
               sudo systemctl enable smart-security.service && \
               sudo systemctl start smart-security.service"
}

# 4. Modify run.sh for headless operation
modify_run_script() {
    echo "Modifying run.sh for headless operation..."
    # Add headless mode configuration to run.sh
    run_on_pi "echo 'export OPENCV_VIDEOIO_DEBUG=1' >> $PI_DIR/run.sh && \
               echo 'export OPENCV_VIDEOIO_PRIORITY_LIST=v4l2,msmf,dshow' >> $PI_DIR/run.sh && \
               echo 'export PYTHONPATH=$PI_DIR/src:\$PYTHONPATH' >> $PI_DIR/run.sh"
}

# Main deployment process
echo "Starting deployment process..."

# Check if we can connect to the Pi
if ! ping -c 1 $PI_HOST &> /dev/null; then
    echo "Error: Cannot connect to Raspberry Pi at $PI_HOST"
    exit 1
fi

# Run deployment steps
install_pi_deps
create_service_file
deploy_app
modify_run_script

echo "Deployment complete! The service should now be running."
echo "To check status: ssh $PI_USER@$PI_HOST 'sudo systemctl status smart-security.service'"
echo "To view logs: ssh $PI_USER@$PI_HOST 'sudo journalctl -u smart-security.service -f'"
