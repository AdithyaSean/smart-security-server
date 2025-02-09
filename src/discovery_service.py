import socket
from zeroconf import ServiceInfo, Zeroconf
import logging
import threading
from typing import Dict, List, Optional
from .network_scanner import scan_network_for_devices
import time
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, port: int = 2003):
        self.zeroconf = Zeroconf()
        self.port = port
        self.services = []
        self.running = False
        self.scan_thread: Optional[threading.Thread] = None
        self.local_ip = self._get_local_ip()
        self.registered_cameras = {}  # Keep track of registered cameras
        self.last_scan_time = 0
        self.min_scan_interval = 30  # Minimum seconds between scans
        
        # Load MAC address configuration
        self.mac_config = self._load_mac_config()
        
        logger.info(f"Discovery Service initialized with port {port} and IP {self.local_ip}")

    def _load_mac_config(self) -> Dict:
        """Load MAC address configuration from json file."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'mac_address_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded MAC configuration with {len(config.get('devices', []))} devices")
                return config
        except Exception as e:
            logger.error(f"Failed to load MAC config: {e}")
            return {"devices": []}

    def _get_local_ip(self) -> str:
        """Get the local IP address of the server."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
            logger.info(f"Local IP detected: {ip}")
        except Exception as e:
            logger.error(f"Failed to get local IP: {e}")
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def _validate_camera(self, camera_info: Dict) -> bool:
        """Validate camera information against MAC address configuration."""
        try:
            if not camera_info.get('mac'):
                logger.warning(f"No MAC address in camera info: {camera_info}")
                return False

            # Check if MAC exists in config
            allowed_devices = [
                device for device in self.mac_config.get('devices', [])
                if device.get('role') == 'camera' and device.get('mac') == camera_info['mac']
            ]

            if not allowed_devices:
                logger.warning(f"Camera MAC {camera_info['mac']} not in allowed list")
                return False

            device_config = allowed_devices[0]
            
            # Update camera info with config values
            camera_info['name'] = device_config.get('name', camera_info['name'])
            camera_info['streamPath'] = device_config.get('stream_path', '/stream')
            
            logger.info(f"Validated camera: {camera_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Error validating camera: {e}")
            return False

    def register_camera(self, camera_info: Dict) -> bool:
        """Register a camera as an mDNS service."""
        try:
            if not self._validate_camera(camera_info):
                return False

            # Extract camera ID from name (e.g. "esp32cam 1" -> "1")
            camera_id = camera_info['name'].split()[-1]
            logger.info(f"Registering camera with ID: {camera_id}")
            
            # Use configured stream path
            video_feed_path = camera_info['streamPath']
            
            # Match Android client's service name format
            service_name = f"camera-{camera_info['name']}._smartcam._tcp.local."
            
            # Prepare service properties
            properties = {
                'name': camera_info['name'].encode('utf-8'),
                'path': video_feed_path.encode('utf-8'),
                'id': str(camera_id).encode('utf-8'),
                'mac': camera_info['mac'].encode('utf-8')
            }

            logger.info(f"Creating service info: {service_name}")
            logger.debug(f"Service properties: {properties}")
            
            # Check if service already exists
            if service_name in self.registered_cameras:
                logger.info(f"Service {service_name} already registered, updating...")
                self.zeroconf.unregister_service(self.registered_cameras[service_name])
                self.services.remove(self.registered_cameras[service_name])
            
            info = ServiceInfo(
                "_smartcam._tcp.local.",
                service_name,
                port=self.port,
                properties=properties,
                addresses=[socket.inet_aton(self.local_ip)]
            )

            self.zeroconf.register_service(info)
            self.services.append(info)
            self.registered_cameras[service_name] = info
            logger.info(f"Successfully registered camera service: {camera_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to register camera service: {e}")
            return False

    def check_camera_alive(self, camera_info: Dict) -> bool:
        """Check if a camera is reachable."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            result = s.connect_ex((camera_info['host'], camera_info['port']))
            s.close()
            return result == 0
        except Exception as e:
            logger.error(f"Error checking camera {camera_info['name']}: {e}")
            return False

    def periodic_scan(self):
        """Periodically scan for cameras and update their status."""
        while self.running:
            try:
                current_time = time.time()
                if current_time - self.last_scan_time >= self.min_scan_interval:
                    logger.info("Starting periodic camera scan")
                    discovered_devices = scan_network_for_devices()
                    
                    if discovered_devices.get('cameras'):
                        for camera in discovered_devices['cameras']:
                            if self.check_camera_alive(camera):
                                self.register_camera(camera)
                            else:
                                logger.warning(f"Camera {camera['name']} is not reachable")
                    
                    self.last_scan_time = current_time
                    
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic scan: {e}")
                time.sleep(5)  # Wait before retrying

    def start(self):
        """Start the discovery service."""
        try:
            logger.info("Starting discovery service...")
            if self.running:
                logger.warning("Discovery service already running")
                return
                
            self.running = True
            discovered_devices = scan_network_for_devices()
            
            if not discovered_devices.get('cameras'):
                logger.warning("No cameras found in network scan")
            else:
                logger.info(f"Found {len(discovered_devices['cameras'])} cameras")
                for camera in discovered_devices['cameras']:
                    logger.info(f"Processing camera: {camera.get('name', 'Unknown')}")
                    self.register_camera(camera)

            # Start periodic scanning thread
            self.scan_thread = threading.Thread(target=self.periodic_scan)
            self.scan_thread.daemon = True
            self.scan_thread.start()
            
            logger.info(f"Successfully registered {len(self.services)} camera services")

        except Exception as e:
            logger.error(f"Failed to start discovery service: {e}")
            self.running = False

    def stop(self):
        """Stop the discovery service and unregister all services."""
        try:
            logger.info("Stopping discovery service...")
            self.running = False
            
            if self.scan_thread:
                self.scan_thread.join(timeout=5)
            
            for service in self.services:
                try:
                    logger.info(f"Unregistering service: {service.name}")
                    self.zeroconf.unregister_service(service)
                except Exception as e:
                    logger.error(f"Failed to unregister service {service.name}: {e}")

            self.zeroconf.close()
            self.services.clear()
            self.registered_cameras.clear()
            logger.info("Discovery service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping discovery service: {e}")
