import socket
from zeroconf import ServiceInfo, Zeroconf
from typing import Dict, List
from .network_scanner import scan_network_for_devices

class DiscoveryService:
    def __init__(self, port: int = 2003):
        self.zeroconf = Zeroconf()
        self.port = port
        self.services = []

    def _get_local_ip(self) -> str:
        """Get the local IP address of the server."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def register_camera(self, camera_info: Dict):
        """Register a camera as an mDNS service."""
        service_name = f"camera-{camera_info['name']}._smartcam._tcp.local."
        # Convert numeric camera ID from name (e.g. "esp32cam 1" -> "1")
        camera_id = camera_info['name'].split()[-1]
        video_feed_path = f"/video_feed/{camera_id}"
        info = ServiceInfo(
            "_smartcam._tcp.local.",
            service_name,
            port=self.port,
            properties={
                'name': camera_info['name'].encode('utf-8'),
                'path': video_feed_path.encode('utf-8')
            },
            addresses=[socket.inet_aton(self._get_local_ip())]  # Use server IP instead of camera IP
        )
        self.zeroconf.register_service(info)
        self.services.append(info)

    def start(self):
        """Start the discovery service."""
        discovered_devices = scan_network_for_devices()
        
        # Register each camera as a service
        for camera in discovered_devices['cameras']:
            camera_info = {
                'name': camera['name'],
                'ip': camera['ip'],  # This is needed for internal video capture
                'stream_path': camera['stream_path']  # Use original stream path for internal capture
            }
            self.register_camera(camera_info)

    def stop(self):
        """Stop the discovery service."""
        for service in self.services:
            self.zeroconf.unregister_service(service)
        self.zeroconf.close()
        self.services.clear()
