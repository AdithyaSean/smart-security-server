from flask import Flask, Response, request, jsonify
import threading
import socket
import cv2
import time
from src.shared_state import camera_streams, stop_event, get_frame, sensor_data, update_sensor_data
from datetime import datetime
import os

OPERATION_MODE = os.getenv("OPERATION_MODE", 'simulation')

app = Flask(__name__)

def generate_frames(camera_id):
    while not stop_event.is_set():
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
        
@app.route('/mode')
def get_mode():
    """Endpoint to check current operation mode"""
    return jsonify({"mode": OPERATION_MODE})

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    camera_url = camera_streams.get(camera_id)
    if camera_url:
        return Response(generate_frames(camera_id),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not found", 404

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

# Find a free port for the Flask server if port 2003 or 4620 is already in use
def find_free_port(preferred_ports=[2003, 4620]):
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('0.0.0.0', port)) != 0:
                return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]

def start_flask_app():
    port = find_free_port()
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.start()

    # Start the main camera processing
    from src.main import main
    main()
