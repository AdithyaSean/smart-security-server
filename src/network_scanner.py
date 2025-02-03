import socket
import cv2
from typing import List, Dict
import ipaddress
import time
import json
import os
import dotenv
import requests

dotenv.load_dotenv()

LAST_KNOWN_IPS_FILE = os.getenv("LAST_KNOWN_IPS_FILE")

def load_last_known_ips():
    """Load the last known device IPs from a file."""
    if os.path.exists(LAST_KNOWN_IPS_FILE):
        with open(LAST_KNOWN_IPS_FILE, 'r') as file:
            data = json.load(file)
            return data.get('cameras', []), data.get('sensors', [])
    return [], []

def save_last_known_ips(camera_ips, sensor_ips):
    """Save the last known device IPs to a file."""
    with open(LAST_KNOWN_IPS_FILE, 'w') as file:
        json.dump({
            'cameras': camera_ips,
            'sensors': sensor_ips
        }, file)

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

def verify_ultrasonic_sensor(ip: str, port: int = 2003) -> bool:
    """Verify that the ultrasonic sensor is responding."""
    try:
        # First check if device responds on port 2003
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            # Try a GET request to verify it's the sonar sensor
            url = f"http://{ip}:{port}/mode"
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"Found sonar sensor at {ip}:{port}")
                return True
        return False
    except Exception as e:
        print(f"Error verifying sensor at {ip}: {str(e)}")
        return False

def scan_network_for_devices(subnet: str = "192.168.2.0/24") -> Dict[str, List[str]]:
    """Scan the network for cameras and ultrasonic sensors."""
    cameras = []
    sensors = []
    network = ipaddress.IPv4Network(subnet)
    
    for i, ip in enumerate(network.hosts()):
        if i >= 20:  # Limit scan to first 20 addresses
            break
            
        ip_str = str(ip)
        print(f"Scanning {ip_str}...")
        
        # Check for sonar sensor first
        if verify_ultrasonic_sensor(ip_str):
            sensors.append(ip_str)
            continue # Skip camera check if sensor found
            
        # Then check for cameras
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            if sock.connect_ex((ip_str, 81)) == 0:
                url = f"http://{ip_str}:81/stream"
                if verify_camera_stream(url):
                    cameras.append(url)
            sock.close()
        except Exception as e:
            print(f"Error scanning {ip_str}: {str(e)}")
            
    return {'cameras': cameras, 'sensors': sensors}

def get_network_devices():
    """Get all network devices, trying last known IPs first."""
    camera_ips, sensor_ips = load_last_known_ips()
    devices = {'cameras': [], 'sensors': []}

    # Try last known camera IPs
    for ip in camera_ips:
        url = f"http://{ip}:81/stream"
        if verify_camera_stream(url):
            devices['cameras'].append(url)

    # Try last known sensor IPs
    for ip in sensor_ips:
        if verify_ultrasonic_sensor(ip):
            devices['sensors'].append(ip)

    # If not enough devices found, scan network
    if len(devices['cameras']) < 2 or len(devices['sensors']) < 1:
        print("Not enough devices found in last known IPs. Scanning network...")
        devices = scan_network_for_devices()

    # Save the new IPs
    if devices['cameras'] or devices['sensors']:
        new_camera_ips = [url.split("//")[1].split(":")[0] for url in devices['cameras']]
        save_last_known_ips(new_camera_ips, devices['sensors'])
        print(f"Found devices: {devices}")

    return devices