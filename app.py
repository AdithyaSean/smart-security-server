from flask import Flask, Response, request, jsonify
import threading
import socket
import cv2
import time
from src.shared_state import camera_streams, stop_event, get_frame, sensor_data, update_sensor_data
from datetime import datetime
import os
from flask_cors import CORS

OPERATION_MODE = os.getenv("OPERATION_MODE", 'simulation')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def generate_frames(camera_id):
    while not stop_event.is_set():
        try:
            frame = get_frame(camera_id)
            if frame is None:
                time.sleep(0.01)  # Wait briefly if no frame is available
                continue
                
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print(f"Failed to encode frame from camera {camera_id}")
                continue
                
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error generating frame for camera {camera_id}: {str(e)}")
            time.sleep(0.1)  # Wait a bit longer on error
            continue
        
@app.route('/mode')
def get_mode():
    """Endpoint to check current operation mode"""
    return jsonify({"mode": OPERATION_MODE})

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    camera = camera_streams.get(camera_id)
    if camera:
        print(f"Serving video feed for camera {camera_id}: {camera.get('name', 'Unknown')}")
        response = Response(generate_frames(camera_id),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', '0')
        return response
    return f"Camera {camera_id} not found", 404

@app.route('/sensor_data', methods=['POST'])
def sensor_data():
    try:
        data = request.get_json()
        value = data.get('value')
        if value is not None:
            update_sensor_data(int(value))
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "error", "message": "No value provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/sensor_status')
def get_sensor_status():
    """Endpoint to check sensor status"""
    return jsonify(sensor_data)

# Find a free port for the Flask server
def find_free_port():
    # Use just port 2003 since this server is now identified by MAC address
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('0.0.0.0', 2003)) != 0:
            return 2003
        # If 2003 is not available, try a random port
        s.bind(('0.0.0.0', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

def start_flask_app():
    port = 2003  # Use fixed port 2003 to match discovery service
    print(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, threaded=True)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.start()

    # Start the main camera processing
    from src.main import main
    main()
