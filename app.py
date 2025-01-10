from flask import Flask, render_template, Response
import threading
import socket
import cv2
import time
from src.shared_state import camera_streams, stop_event, get_frame

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    camera_url = camera_streams.get(camera_id)
    if camera_url:
        return Response(generate_frames(camera_id),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not found", 404

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]

def start_flask_app():
    port = find_free_port()
    print(f"Server is running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.start()

    # Start the main camera processing
    from src.main import main
    main()
