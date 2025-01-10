Here's the updated README with the complete installation and usage instructions:

### README.md

# Automated Home Security System

Automated Home Security System is a Python project that utilizes computer vision techniques to detect changes in intensity and faces in images captured from a network camera through URL. It also enhances the detected faces using various image processing techniques like contrast enhancement and sharpening.

## Features

- Real-time network camera monitoring
- Intensity change detection
- Face detection and segmentation
- Image enhancement with night vision capabilities
- Automatic saving of original and enhanced images
- Firebase integration for cloud storage

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- A stable network connection
- Git (for cloning the repository)

## Setup

1. Clone the repository:
```sh
git clone https://github.com/yourusername/Automated-Home-Security-System.git
cd Automated-Home-Security-System
```

2. Create a virtual environment and activate it:
```sh
# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# On Windows
python -m venv .venv
.venv\Scripts\activate
```

3. Install the dependencies:
```sh
pip install -r requirements.txt
```

4. Configure Firebase:
   - Copy `.env.example` to `.env`
   - Update with your Firebase credentials and database URL

## Project Structure

```
smart-security-server/
├── src/
│   ├── main.py             # Main monitoring script
│   ├── enhance.py          # Image enhancement module
│   ├── segment.py          # Face detection and segmentation
│   ├── camera_scanner.py   # Network camera discovery
│   └── firebase_service.py # Firebase integration
├── firebase/               # Firebase credentials
├── requirements.txt        # Project dependencies
├── .env.example            # Environment variables template
└── README.md               # Project documentation
```

## Usage

1. Make sure your ESP32 cameras are connected to the network and streaming.

2. Run the main script:
```sh
python src/main.py
```

3. The program will:
   - Scan network for ESP32 cameras
   - Monitor multiple camera streams
   - Detect intensity changes
   - Perform face detection and enhancement
   - Upload processed images to Firebase
   - Store locally in organized directories:
     - `original/`: Raw captured frames
     - `segmented/`: Detected face segments
     - `enhanced/`: Enhanced face images

The system uses [`FirebaseService`](src/firebase_service.py) to handle cloud storage and [`camera_scanner`](src/camera_scanner.py) for automatic camera discovery.

## Troubleshooting

1. If the video stream doesn't capture properly:
   - Check if the network connection is stable
   - Verify device permissions
   - Try reconnecting the video source

2. If face detection isn't working:
   - Ensure proper lighting conditions
   - Make sure faces are clearly visible
   - Try adjusting your distance from the camera

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

