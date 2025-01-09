import socket
import requests
from typing import List
import ipaddress

def scan_network_for_cameras(subnet: str = "192.168.1.0/24") -> List[str]:
    """Scan the network for ESP32 cameras."""
    cameras = []
    network = ipaddress.IPv4Network(subnet)
    
    for ip in network.hosts():
        ip_str = str(ip)
        try:
            # Try to connect to the ESP32-CAM stream port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((ip_str, 81))
            if result == 0:
                # Verify it's an ESP32-CAM by trying to access the stream
                url = f"http://{ip_str}:81/stream"
                response = requests.get(url, timeout=0.5, stream=True)
                if response.status_code == 200:
                    cameras.append(url)
                    if len(cameras) >= 2:  # Stop after finding 2 cameras
                        break
            sock.close()
        except:
            continue
    
    return cameras
