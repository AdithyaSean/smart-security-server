# Smart Security Server

A lightweight FastAPI server for the Automated Home Security System that monitors sensors and provides status updates.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Quick Start

1. Clone the repository:
```bash
git clone [repository-url]
cd smart-security-server
```

2. Run the server:
```bash
./run.sh
```

The script will:
- Create a Python virtual environment
- Install required dependencies
- Start the FastAPI server on port 2003

## API Endpoints

- `GET /sensor_status` - Get current sensor status
- `POST /sensor_data` - Update sensor data

## Development

The server uses FastAPI for the web framework and runs on uvicorn. Key files:

- `src/main.py` - Main FastAPI application
- `src/discovery_service.py` - Device discovery service
- `src/network_scanner.py` - Network device scanning
- `src/shared_state.py` - Shared state management
