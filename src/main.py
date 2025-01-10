import os
import cv2
from datetime import datetime
import numpy as np
from src.segment import detect_faces
from src.camera_scanner import scan_network_for_cameras
import threading
import time
from src.firebase_service import FirebaseService
from src.shared_state import camera_streams, camera_caps, stop_event, put_frame

# Directory names
directories_to_create = ["original", "segmented", "enhanced"]

# Create directories if they don't exist
for directory in directories_to_create:
    os.makedirs(directory, exist_ok=True)

def process_camera(camera_url: str, camera_id: int, stop_event: threading.Event):
    camera_streams[camera_id] = camera_url  # Store camera URL globally
    firebase_service = FirebaseService()
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera {camera_id}")
        return

    previous_intensity = None
    frame_counter = 0
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame from camera {camera_id}")
            time.sleep(1)
            continue

        intensity = np.mean(frame)
        print(f"Camera {camera_id} Intensity:", int(intensity))

        # Store frame in shared buffer for Flask server
        put_frame(camera_id, frame)

        # Save frame only if faces are detected
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        frame_path_original = f"original/cam{camera_id}_frame_{timestamp}_{frame_counter}.jpg"
        cv2.imwrite(frame_path_original, frame)
        
        # Check for faces and process if found
        if detect_faces(frame_path_original, intensity, camera_id):
            frame_counter += 1
            firebase_service.upload_image_data(frame_path_original, 'original', camera_id)

    cap.release()
    print(f"Camera {camera_id} released.")

def main():
    global stop_event
    stop_event = threading.Event()  # Initialize stop_event

    # Scan for cameras
    print("Scanning for ESP32 cameras...")
    camera_urls = scan_network_for_cameras()
    
    if len(camera_urls) < 2:
        print(f"Error: Found only {len(camera_urls)} cameras. Need at least 2.")
        # Fallback to known camera IPs if scan fails
        print("Falling back to known camera IPs...")
        camera_urls = [
            "http://192.168.1.7:81/stream",
            "http://192.168.1.8:81/stream"
        ]
    
    # Populate camera_streams and initialize camera_caps
    for i, camera_url in enumerate(camera_urls[:2], 1):
        camera_streams[i] = camera_url
        cap = cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            print(f"Error: Could not open video stream from camera {i}")
        else:
            camera_caps[i] = cap

    # Create threads for each camera
    threads = []
    
    try:
        for i, camera_url in enumerate(camera_urls[:2], 1):
            thread = threading.Thread(
                target=process_camera,
                args=(camera_url, i, stop_event)
            )
            threads.append(thread)
            thread.start()
            
        # Wait for KeyboardInterrupt
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Shutting down...")
        stop_event.set()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join()
        
        print("All cameras released. Exiting...")

if __name__ == "__main__":
    main()
