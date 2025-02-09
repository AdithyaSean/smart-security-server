import json
import os
import subprocess
import cv2
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

MAC_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'src/secrets/mac_address_config.json')

def load_mac_config() -> Dict:
    """Load the MAC address configuration from file."""
    if os.path.exists(MAC_CONFIG_FILE):
        with open(MAC_CONFIG_FILE, 'r') as file:
            return json.load(file)
    raise FileNotFoundError("MAC address configuration file not found")

def verify_camera_stream(url: str) -> bool:
    """Verify if a camera stream is accessible."""
    try:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return False
        ret, _ = cap.read()
        cap.release()
        return ret
    except:
        return False

def run_arp_scan() -> List[Dict[str, str]]:
    """Run arp-scan to discover devices on the network."""
    try:
        result = subprocess.run(['sudo', 'arp-scan', '-l'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        devices = []
        for line in result.stdout.split('\n'):
            if '\t' in line:  # arp-scan output format: IP\tMAC\tVendor
                ip, mac, _ = line.split('\t')
                devices.append({'ip': ip.strip(), 'mac': mac.strip().lower()})
        return devices
    except subprocess.CalledProcessError as e:
        print(f"Error running arp-scan: {e}")
        return []

def find_device_by_mac(devices: List[Dict[str, str]], mac: str) -> Optional[Dict[str, str]]:
    """Find a device in the list by its MAC address."""
    mac = mac.lower()
    for device in devices:
        if device['mac'] == mac:
            return device
    return None

def scan_network_for_devices() -> Dict:
    """Scan network for all configured devices using MAC addresses."""
    try:
        config = load_mac_config()
        discovered_devices = run_arp_scan()
        
        result = {
            'cameras': [],
            'sensors': [],
            'server': None
        }
        
        for device in config['devices']:
            mac = device['mac'].lower()
            discovered = find_device_by_mac(discovered_devices, mac)
            
            if discovered:
                ip = discovered['ip']
                
                if device['role'] == 'camera':
                    url = f"http://{ip}:{device['port']}{device['stream_path']}"
                    if verify_camera_stream(url):
                        result['cameras'].append({
                            'url': url,
                            'ip': ip,
                            'mac': mac,
                            'name': device['name']
                        })
                
                elif device['role'] == 'sensor':
                    result['sensors'].append({
                        'ip': ip,
                        'mac': mac,
                        'name': device['name']
                    })
                
                elif device['role'] == 'server':
                    result['server'] = {
                        'ip': ip,
                        'mac': mac,
                        'name': device['name']
                    }
        
        return result
    except Exception as e:
        print(f"Error scanning network: {e}")
        return {'cameras': [], 'sensors': [], 'server': None}

def get_network_devices():
    """Get all network devices."""
    print("Scanning for devices using MAC addresses...")
    return scan_network_for_devices()
