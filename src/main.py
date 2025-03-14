import os
import cv2
import json
from datetime import datetime
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from src.network_scanner import get_network_devices
from src.shared_state import camera_streams, camera_caps, sensor_addresses, sensor_data, stop_event, put_frame, update_sensor_data
from src.firebase_service import init_firebase, upload_image_data, get_firebase_app
from src.discovery_service import DiscoveryService
from src.face_service import FaceService

# Initialize Firebase and get app instance
firebase_app = init_firebase()

directories_to_create = ["faces", "secrets"]
for directory in directories_to_create:
    os.makedirs(directory, exist_ok=True)

def get_sensor_trigger_status():
    """Check if motion is detected"""
    return sensor_data.get('motion_detected', False)

def process_camera(camera: dict, camera_id: int, stop_event: threading.Event, face_service: FaceService):
    print(f"Processing camera {camera_id} with info: {json.dumps(camera, indent=2)}")
    camera_streams[camera_id] = camera
    
    # Construct camera URL using original camera stream path
    try:
        camera_url = f"http://{camera['ip']}:{camera['port']}{camera['stream_path']}"
        print(f"Opening camera stream at: {camera_url}")
    except KeyError as e:
        print(f"Error constructing URL - missing key: {e}")
        print(f"Available keys: {list(camera.keys())}")
        return

    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera {camera_id} at URL: {camera_url}")
        return

    print(f"Successfully opened camera {camera_id} stream")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 5)

    frame_count = 0
    skip_frames = 5
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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
                        
                        # Check if face is unknown
                        is_unknown = face_service.is_face_unknown(face)
                        
                        # Upload image with notification if unknown
                        upload_image_data(
                            camera_id, 
                            "face", 
                            face_image_path, 
                            face_image_name, 
                            timestamp, 
                            f"Camera {camera_id} - {'Unknown' if is_unknown else ''} Face Detected - ",
                            notify=is_unknown
                        )
        
        time.sleep(0.01)  # Small delay to prevent CPU overload

    cap.release()
    print(f"Camera {camera_id} released.")

def monitor_sensor(sensor: dict, stop_event: threading.Event):
    """Monitor sensor stream"""
    while not stop_event.is_set():
        try:
            response = requests.get(f"http://{sensor['ip']}:81/stream")
            if response.status_code == 200:
                if update_sensor_data(response.text):
                    print(f"Motion detection state changed: {response.text} from sensor {sensor['name']} ({sensor['mac']})")
        except Exception as e:
            print(f"Error reading from sensor {sensor['name']} ({sensor['mac']}): {str(e)}")
        time.sleep(0.1)

def main():
    # Initialize face service with Firebase app
    face_service = FaceService(get_firebase_app())
    global stop_event
    stop_event = threading.Event()

    print("Initializing discovery service...")
    discovery_service = DiscoveryService()
    print("Starting discovery service...")
    discovery_service.start()

    print("Getting device information using MAC addresses...")
    devices = get_network_devices()

    # Initialize cameras
    cameras = devices['cameras']
    print(f"\nFound cameras: {json.dumps(cameras, indent=2)}")
    
    if len(cameras) < 1:  # Changed from 2 to 1 since we have one ESP32CAM
        print(f"Error: No cameras found.")
        return

    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            futures = [executor.submit(process_camera, camera, i, stop_event, face_service) 
                      for i, camera in enumerate(cameras, 1)]
            print("All cameras started.")
            
            # Initialize sensor addresses
            sensors = devices['sensors']
            if not sensors:
                print("Warning: No ultrasonic sensors found.")
            else:
                # Start sensor monitoring threads
                sensor_threads = []
                for sensor in sensors:
                    thread = threading.Thread(target=monitor_sensor, args=(sensor, stop_event))
                    thread.start()
                    sensor_threads.append(thread)
                    print(f"Started monitoring sensor: {sensor['name']} at {sensor['ip']}")
            
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
            discovery_service.stop()
            print("Discovery service stopped.")
            executor.shutdown(wait=True)
            print("Executor shut down.")

if __name__ == "__main__":
    try:
        main()
        print("\nProgram interrupted by user. Exiting...")
        stop_event.set()
        os._exit(0)
    except Exception as e:
        print(f"Error in main: {str(e)}")
        stop_event.set()
        os._exit(1)
