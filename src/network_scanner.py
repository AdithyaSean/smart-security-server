import json
import os
import ipaddress
import socket
import cv2
from typing import List
from dotenv import load_dotenv

load_dotenv()

LAST_KNOWN_IPS_FILE = os.getenv('LAST_KNOWN_IPS_FILE')

def load_last_known_ips():
    """Load the last known device IPs from a file."""
    if os.path.exists(LAST_KNOWN_IPS_FILE):
        with open(LAST_KNOWN_IPS_FILE, 'r') as file:
            data = json.load(file)
            return data.get('cameras', []), data.get('sensor', "192.168.2.6")  # Default sensor IP
    return [], "192.168.2.6"

def save_last_known_ips(camera_ips: List[str], sensor_ip: str):
    """Save the last known device IPs to a file."""
    with open(LAST_KNOWN_IPS_FILE, 'w') as file:
        json.dump({
            'cameras': camera_ips,
            'sensor': sensor_ip
        }, file)

def verify_camera_stream(url: str) -> bool:
    try:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return False
        ret, _ = cap.read()
        cap.release()
        return ret
    except:
        return False

def scan_network_for_cameras(subnet: str = "192.168.2.0/24") -> List[str]:
    """Scan network for camera streams only."""
    cameras = []
    network = ipaddress.IPv4Network(subnet)
    
    for i, ip in enumerate(network.hosts()):
        if i >= 20:
          # Limit scan
            break
            
        ip_str = str(ip)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            if sock.connect_ex((ip_str, 81)) == 0:
                url = f"http://{ip_str}:81/stream"
                if verify_camera_stream(url):
                    cameras.append(url)
            sock.close()
        except:
            pass
            
    return cameras

def get_network_devices():
    """Get cameras and sensor IP."""
    camera_ips, sensor_ip = load_last_known_ips()
    
    if not camera_ips:
        print("Scanning for cameras...")
        camera_ips = scan_network_for_cameras()
        if camera_ips:
            save_last_known_ips(camera_ips, sensor_ip)
    
    return {'cameras': camera_ips, 'sensors': [sensor_ip]}