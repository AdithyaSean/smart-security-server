import os
import cv2
from datetime import datetime
import numpy as np
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from src.camera_scanner import get_camera_urls
from src.shared_state import camera_streams, camera_caps, stop_event, put_frame
from src.firebase_service import init_firebase, upload_image_data

init_firebase()

# Create necessary directories
directories_to_create = ["faces", "secrets"]
for directory in directories_to_create:
    os.makedirs(directory, exist_ok=True)

def process_camera(camera_url: str, camera_id: int, stop_event: threading.Event):
    camera_streams[camera_id] = camera_url
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera {camera_id}")
        return

    # Set lower resolution and frame rate
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 5)

    previous_intensity = None
    frame_count = 0
    skip_frames = 5  # Process every 5th frame
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Firebase upload interval
    upload_interval = 60  # Upload every 60 seconds
    last_upload_time = time.time()

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame from camera {camera_id}")
            time.sleep(1)
            continue

        frame_count += 1
        if frame_count % skip_frames != 0:
            continue

        intensity = np.mean(frame)

        # Store frame in shared buffer for Flask server
        put_frame(camera_id, frame)

        # Check for significant intensity change
        if previous_intensity is not None and abs(intensity - previous_intensity) > 1.0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            detected_faces = len(faces)

            if detected_faces > 0:
                for (x, y, w, h) in faces:
                    print(f"Camera {camera_id} - Faces Detected - {detected_faces}")
                    face = frame[y:y+h, x:x+w]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    face_image = f"faces/camera_{camera_id}_time_{timestamp}_frame_{frame_count}.jpg"
                    cv2.imwrite(face_image, face)
                    
                    # Upload only if the interval has passed
                    if time.time() - last_upload_time > upload_interval:
                        upload_image_data(face_image, "face", camera_id)
                        last_upload_time = time.time()

        previous_intensity = intensity

    cap.release()
    print(f"Camera {camera_id} released.")

def main():
    global stop_event
    stop_event = threading.Event()  # Initialize stop_event

    # Get camera URLs, trying last known IPs first, then scanning if necessary
    print("Getting ESP32-cam URLs...")
    camera_urls = get_camera_urls()
    
    if len(camera_urls) < 2:
        print(f"Error: Found only {len(camera_urls)} cameras. Need at least 2.")
        return
    
    # Populate camera_streams and initialize camera_caps
    for i, camera_url in enumerate(camera_urls[:2], 1):
        camera_streams[i] = camera_url
        cap = cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            print(f"Error: Could not open video stream from camera {i}")
        else:
            camera_caps[i] = cap

    # Create a thread pool
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            futures = [executor.submit(process_camera, camera_url, i, stop_event) for i, camera_url in enumerate(camera_urls[:2], 1)]
            
            # Wait for KeyboardInterrupt
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Shutting down...")
            stop_event.set()
            
            # Wait for threads to finish
            for future in futures:
                future.result()
            
            print("All cameras released. Exiting...")

if __name__ == "__main__":
    main()