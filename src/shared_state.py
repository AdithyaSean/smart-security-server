import threading
from queue import Queue

# Shared state for the application
camera_streams = {}
camera_caps = {}
sensor_addresses = {}
stop_event = threading.Event()

# Frame buffers for each camera
frame_queues = {
    1: Queue(maxsize=10),
    2: Queue(maxsize=10)
}

# Sensor data buffer
sensor_data = {
    'motion_detected': False
}

def get_frame(camera_id):
    """Get a frame from the specified camera's queue"""
    try:
        return frame_queues[camera_id].get_nowait()
    except:
        return None

def put_frame(camera_id, frame):
    """Put a frame into the specified camera's queue"""
    try:
        frame_queues[camera_id].put_nowait(frame)
    except:
        pass

def update_sensor_data(value):
    """Update the latest sensor reading"""
    sensor_data['motion_detected'] = bool(value)