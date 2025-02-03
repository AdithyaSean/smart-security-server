import os
import cv2
from datetime import datetime
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from src.network_scanner import get_network_devices
from src.shared_state import camera_streams, camera_caps, sensor_addresses, sensor_data, stop_event, put_frame, update_sensor_data
from src.firebase_service import init_firebase, upload_image_data

init_firebase()

directories_to_create = ["faces", "secrets"]
for directory in directories_to_create:
    os.makedirs(directory, exist_ok=True)

def get_sensor_trigger_status():
    """Check if motion is detected"""
    return sensor_data.get('motion_detected', False)

def process_camera(camera_url: str, camera_id: int, stop_event: threading.Event):
    camera_streams[camera_id] = camera_url
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera {camera_id}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 5)

    face_type = "face"
    frame_count = 0
    skip_frames = 5
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Add recording state variables
    recording_active = False
    recording_start_time = None
    RECORDING_DURATION = 10  # Record for 10 seconds after trigger

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame from camera {camera_id}")
            time.sleep(1)
            continue

        # Always put frame in queue for live viewing
        put_frame(camera_id, frame)

        # Only process if motion detected
        if get_sensor_trigger_status():
            frame_count += 1
            if frame_count % skip_frames == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                if len(faces) > 0:
                    timestamp = int(datetime.now().strftime("%Y%m%d%H%M%S"))
                    for (x, y, w, h) in faces:
                        face = frame[y:y+h, x:x+w]
                        face_image_name = f"camera_{camera_id}_time_{timestamp}.jpg"
                        face_image_path = f"faces/{face_image_name}"
                        cv2.imwrite(face_image_path, face)
                        upload_image_data(camera_id, "face", face_image_path, face_image_name, timestamp, f"Camera {camera_id} - Face Detected - ")
        
        time.sleep(0.01)  # Small delay to prevent CPU overload

    cap.release()
    print(f"Camera {camera_id} released.")

def monitor_sensor(sensor_ip: str, stop_event: threading.Event):
    """Monitor sensor stream on port 81"""
    while not stop_event.is_set():
        try:
            response = requests.get(f"http://{sensor_ip}:81/stream")
            if response.status_code == 200:
                if update_sensor_data(response.text):
                    print(f"Motion detection state changed: {response.text}")
        except:
            pass
        time.sleep(0.1)

def main():
    global stop_event
    stop_event = threading.Event()

    print("Getting ESP32-cam URLs...")
    devices = get_network_devices()

    # Initialize cameras
    if len(devices['cameras']) < 2:
        print(f"Error: Found only {len(devices['cameras'])} cameras. Need at least 2.")
        return

    # Initialize sensor addresses
    if not devices['sensors']:
        print("Warning: No ultrasonic sensors found.")
    else:
        for i, sensor_ip in enumerate(devices['sensors'], 1):
            sensor_addresses[i] = sensor_ip
            print(f"Sensor {i} initialized at {sensor_ip}")

    # Initialize camera streams
    for i, camera_url in enumerate(devices['cameras'][:2], 1):
        camera_streams[i] = camera_url
        cap = cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            print(f"Error: Could not open video stream from camera {i}")
        else:
            camera_caps[i] = cap
            print(f"Camera {i} initialized.")

    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            futures = [executor.submit(process_camera, camera_url, i, stop_event) 
                      for i, camera_url in enumerate(devices['cameras'][:2], 1)]
            print("All cameras started.")
            
            # Start sensor monitoring threads
            sensor_threads = []
            for sensor_ip in devices['sensors']:
                thread = threading.Thread(target=monitor_sensor, args=(sensor_ip, stop_event))
                thread.start()
                sensor_threads.append(thread)
            
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Shutting down...")
            stop_event.set()
            
            for future in futures:
                try:
                    future.result(timeout=10)
                except Exception as e:
                    print(f"Error waiting for thread: {e}")
            
            print("All cameras released. Exiting...")
        finally:
            executor.shutdown(wait=True)
            print("Executor shut down.")

if __name__ == "__main__":
    try:
        main()
        print("\nProgram interrupted by user. Exiting...")
        stop_event.set()
        os._exit(0)
    except Exception as e:
        print(f"Error in main: {e}")
        stop_event.set()
        os._exit(1)
        os._exit(1)
