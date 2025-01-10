import socket
import cv2
from typing import List
import ipaddress
import time
import json
import os
import dotenv

dotenv.load_dotenv()

LAST_KNOWN_IPS_FILE = os.getenv("LAST_KNOWN_IPS_FILE")

def load_last_known_ips():
    """Load the last known camera IPs from a file."""
    if os.path.exists(LAST_KNOWN_IPS_FILE):
        with open(LAST_KNOWN_IPS_FILE, 'r') as file:
            return json.load(file)
    return []

def save_last_known_ips(ips):
    """Save the last known camera IPs to a file."""
    with open(LAST_KNOWN_IPS_FILE, 'w') as file:
        json.dump(ips, file)

def verify_camera_stream(url: str) -> bool:
    """Verify that the camera stream is sending valid video frames."""
    try:
        # Try to read a few frames from the stream
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return False
            
        # Try reading 3 frames with a timeout
        start_time = time.time()
        frames_read = 0
        
        while frames_read < 3 and time.time() - start_time < 2.0:
            ret, frame = cap.read()
            if ret and frame is not None:
                # Verify frame has valid dimensions
                if frame.shape[0] > 0 and frame.shape[1] > 0:
                    frames_read += 1
                    
        cap.release()
        return frames_read >= 3
        
    except Exception as e:
        print(f"Error verifying camera stream: {str(e)}")
        return False

def scan_network_for_cameras(subnet: str = "192.168.1.0/24") -> List[str]:
    """Scan the network for ESP32 cameras."""
    cameras = []
    network = ipaddress.IPv4Network(subnet)
    
    for ip in network.hosts():
        ip_str = str(ip)
        try:
            # Try to connect to the ESP32-CAM stream port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Increased timeout
            result = sock.connect_ex((ip_str, 81))
            if result == 0:
                # Verify it's an ESP32-CAM by trying to access the stream
                url = f"http://{ip_str}:81/stream"
                if verify_camera_stream(url):
                    cameras.append(url)
                    if len(cameras) >= 2:  # Stop after finding 2 cameras
                        break
            sock.close()
        except Exception as e:
            print(f"Error scanning {ip_str}: {str(e)}")
            continue
    
    return cameras

def get_camera_urls():
    """Get camera URLs, trying last known IPs first, then scanning if necessary."""
    last_known_ips = load_last_known_ips()
    camera_urls = []

    # Try last known IPs first
    for ip in last_known_ips:
        url = f"http://{ip}:81/stream"
        if verify_camera_stream(url):
            camera_urls.append(url)
            if len(camera_urls) >= 2:
                break

    # If not enough cameras found, scan the network
    if len(camera_urls) < 2:
        print("Not enough cameras found in last known IPs. Scanning network...")
        camera_urls = scan_network_for_cameras()

    # Save the new IPs
    if camera_urls:
        new_ips = [url.split("//")[1].split(":")[0] for url in camera_urls]
        save_last_known_ips(new_ips)
        print(f"Found {len(camera_urls)} cameras: {camera_urls}")


    return camera_urls
