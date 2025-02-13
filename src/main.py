from fastapi import FastAPI, HTTPException
from typing import Dict, Optional
import json
import threading
import time
import requests
from src.shared_state import sensor_data, update_sensor_data
from src.discovery_service import DiscoveryService
from src.network_scanner import get_network_devices

app = FastAPI(title="Smart Security Server")

# Initialize discovery service
discovery_service = DiscoveryService()
stop_event = threading.Event()

def monitor_sensor(sensor: dict, stop_event: threading.Event):
    """Monitor sensor stream"""
    while not stop_event.is_set():
        try:
            response = requests.get(f"http://{sensor['ip']}:81/stream")
            if response.status_code == 200:
                if update_sensor_data(response.text):
                    print(f"Motion detection state changed: {response.text} from sensor {sensor['name']} ({sensor['mac']})")
        except Exception as e:
            print(f"Error reading from sensor {sensor['name']} ({sensor['mac']}): {str(e)}")
        time.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    print("Starting discovery service...")
    discovery_service.start()
    
    print("Getting device information using MAC addresses...")
    devices = get_network_devices()
    
    # Initialize sensors
    sensors = devices['sensors']
    if not sensors:
        print("Warning: No ultrasonic sensors found.")
    else:
        # Start sensor monitoring threads
        for sensor in sensors:
            thread = threading.Thread(target=monitor_sensor, args=(sensor, stop_event))
            thread.start()
            print(f"Started monitoring sensor: {sensor['name']} at {sensor['ip']}")

@app.on_event("shutdown")
async def shutdown_event():
    print("\nShutting down...")
    stop_event.set()
    discovery_service.stop()
    print("Discovery service stopped.")

@app.get("/sensor_status")
async def get_sensor_status() -> Dict[str, bool]:
    """Get current sensor status"""
    return sensor_data

@app.post("/sensor_data")
async def update_sensor_status(value: Optional[bool] = None):
    """Update sensor data"""
    try:
        if value is not None:
            update_sensor_data(value)
            return {"status": "success"}
        return {"status": "error", "message": "No value provided"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
