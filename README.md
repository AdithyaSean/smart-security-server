# Smart Security System Server

Real-time security monitoring using computer vision and ESP32 cameras.

## Key Features
- 📹 Multi-camera monitoring with local network realtime tracking
- 🔍 Motion detection via intensity changes
- 👤 Face detection & enhancement with night vision capabilities
- ☁️ Firebase cloud integration for remote access
- 💾 Local image storage (faces)
- 🚨 Real-time alerts and notifications
- 📊 Activity logging and analytics

## System Overview

The Smart Security System provides comprehensive monitoring through:
1. **Network Camera Integration**: Automatically discovers and connects to ESP32 cameras on the local network
2. **Real-time Processing**: Analyzes video streams for motion and faces
3. **Enhanced Security**: Stores and processes images locally while maintaining cloud backups
4. **Intelligent Alerts**: Notifies users of significant events with processed images

## Quick Start

### Smart-Security-Server Submodule

1. Clone & setup:
```bash
git clone https://github.com/AdithyaSean/smart-security-server.git
cd smart-security-server
cp .env.example .env
```
or one liner command:
```bash
git clone https://github.com/AdithyaSean/smart-security-server.git && cd smart-security-server && cp .env.example .env
```

2. Configure `.env` with your Firebase credentials

3. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Run the system:
```sh
./run.sh
```

## Project Structure

```
smart-security-server/
├── src/                    # Core modules
│   ├── main.py             # Main monitoring and coordination
│   ├── enhance.py          # Image processing and enhancement
│   ├── segment.py          # Face detection and segmentation
│   ├── camera_scanner.py   # Network camera discovery
│   ├── firebase_service.py # Cloud storage integration
│   └── shared_state.py     # Shared resources and state management
├── templates/              # Web interface templates
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
├── run.sh                  # Startup script
├── app.py                  # Flask web server and API endpoints
└── README.md               # Documentation
```

## Web Interface

The system provides a Flask-based web interface with the following features:
- Real-time video streaming from multiple cameras
- Status monitoring of connected devices
- Configuration interface for system settings
- API endpoints for integration with other systems

### API Endpoints
- `/video_feed/<camera_id>`: Live video stream
- `/status`: System status and health check
- `/config`: System configuration management
- `/events`: Security event history

### app.py Features
- Flask web server implementation
- Video streaming using MJPEG
- REST API for system control
- WebSocket support for real-time updates
- Integration with core security modules

## Detailed Features

### Real-time Monitoring
- Continuous video stream analysis
- Automatic camera discovery on local network
- Multi-camera support with independent processing

### Intelligent Detection
- Motion detection through intensity changes
- Face detection using advanced algorithms
- Night vision enhancement for low-light conditions

### Data Management
- Local storage for detected faces images
- Cloud backup through Firebase integration
- Organized directory structure for easy access

## Troubleshooting

### Common Issues
- **500 Errors**: Verify output directories exist and are writable
- **Video Issues**: Check network connection and camera permissions
- **Face Detection**: Ensure proper lighting and clear visibility
- **Firebase Connection**: Verify credentials in .env file

## License
MIT License - See [LICENSE](LICENSE)
