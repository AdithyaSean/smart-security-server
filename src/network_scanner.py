import json
import os
import subprocess
import cv2
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAC_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mac_address_config.json')

def load_mac_config() -> Dict:
    """Load the MAC address configuration from file."""
    try:
        if not os.path.exists(MAC_CONFIG_FILE):
            raise FileNotFoundError("MAC address configuration file not found")
        
        with open(MAC_CONFIG_FILE, 'r') as file:
            config = json.load(file)
            logger.info(f"Loaded {len(config.get('devices', []))} devices from config")
            return config
            
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing MAC address config: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading MAC config: {e}")
        raise

def verify_camera_stream(url: str, retries: int = 3) -> bool:
    """
    Verify if a camera stream is accessible with retries.
    
    Args:
        url: The camera stream URL to verify
        retries: Number of times to retry on failure
        
    Returns:
        bool: True if camera is accessible, False otherwise
    """
    logger.debug(f"Verifying camera stream: {url}")
    
    for attempt in range(retries):
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                logger.warning(f"Failed to open camera stream {url} (attempt {attempt + 1})")
                continue
                
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                logger.info(f"Successfully verified camera stream: {url}")
                return True
            else:
                logger.warning(f"Could not read frame from {url} (attempt {attempt + 1})")
                
        except Exception as e:
            logger.error(f"Error verifying camera stream {url} (attempt {attempt + 1}): {e}")
            
        if attempt < retries - 1:
            continue
            
    logger.error(f"Failed to verify camera stream after {retries} attempts: {url}")
    return False

def run_arp_scan() -> List[Dict[str, str]]:
    """Run arp-scan to discover devices on the network."""
    try:
        logger.info("Starting network scan with arp-scan")
        result = subprocess.run(
            ['sudo', 'arp-scan', '-l'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        devices = []
        for line in result.stdout.split('\n'):
            if '\t' in line:  # arp-scan output format: IP\tMAC\tVendor
                try:
                    ip, mac, vendor = line.split('\t')
                    device = {
                        'ip': ip.strip(),
                        'mac': mac.strip().lower(),
                        'vendor': vendor.strip()
                    }
                    devices.append(device)
                    logger.debug(f"Found device: {device}")
                except ValueError:
                    logger.warning(f"Malformed line in arp-scan output: {line}")
                    continue
        
        logger.info(f"Found {len(devices)} devices on network")
        return devices
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running arp-scan: {e}")
        if e.stderr:
            logger.error(f"arp-scan error output: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in network scan: {e}")
        return []

def find_device_by_mac(devices: List[Dict[str, str]], mac: str) -> Optional[Dict[str, str]]:
    """Find a device in the list by its MAC address."""
    mac = mac.lower()
    for device in devices:
        if device['mac'] == mac:
            logger.debug(f"Found device with MAC {mac}: {device}")
            return device
    logger.debug(f"No device found with MAC {mac}")
    return None

def scan_network_for_devices() -> Dict:
    """
    Scan network for all configured devices using MAC addresses.
    
    Returns:
        Dict containing lists of discovered cameras, sensors, and server info
    """
    logger.info("Starting network device scan")
    try:
        # Load device configuration
        config = load_mac_config()
        
        # Run network scan
        discovered_devices = run_arp_scan()
        if not discovered_devices:
            logger.warning("No devices found in network scan")
            return {'cameras': [], 'sensors': [], 'server': None}
        
        result = {
            'cameras': [],
            'sensors': [],
            'server': None
        }
        
        # Process each configured device
        for device in config['devices']:
            mac = device['mac'].lower()
            logger.info(f"Looking for configured device: {device['name']} ({mac})")
            
            discovered = find_device_by_mac(discovered_devices, mac)
            if not discovered:
                logger.warning(f"Device not found on network: {device['name']} ({mac})")
                continue
                
            ip = discovered['ip']
            logger.info(f"Found device {device['name']} at {ip}")
            
            if device['role'] == 'camera':
                url = f"http://{ip}:{device['port']}{device['stream_path']}"
                if verify_camera_stream(url):
                    camera_info = {
                        'url': url,
                        'ip': ip,
                        'port': device['port'],
                        'stream_path': device['stream_path'],
                        'mac': mac,
                        'name': device['name']
                    }
                    result['cameras'].append(camera_info)
                    logger.info(f"Added camera: {camera_info}")
                else:
                    logger.warning(f"Camera stream not accessible: {url}")
            
            elif device['role'] == 'sensor':
                sensor_info = {
                    'ip': ip,
                    'mac': mac,
                    'name': device['name']
                }
                result['sensors'].append(sensor_info)
                logger.info(f"Added sensor: {sensor_info}")
            
            elif device['role'] == 'server':
                server_info = {
                    'ip': ip,
                    'mac': mac,
                    'name': device['name']
                }
                result['server'] = server_info
                logger.info(f"Added server: {server_info}")
        
        logger.info(f"Scan complete. Found: {len(result['cameras'])} cameras, "
                   f"{len(result['sensors'])} sensors, "
                   f"{'1' if result['server'] else '0'} server")
        return result
        
    except Exception as e:
        logger.error(f"Error during network scan: {e}", exc_info=True)
        return {'cameras': [], 'sensors': [], 'server': None}

def get_network_devices() -> Dict:
    """
    Get all network devices. Main entry point for network scanning.
    
    Returns:
        Dict containing discovered devices
    """
    logger.info("Starting network device discovery")
    try:
        return scan_network_for_devices()
    except Exception as e:
        logger.error(f"Failed to get network devices: {e}", exc_info=True)
        return {'cameras': [], 'sensors': [], 'server': None}
