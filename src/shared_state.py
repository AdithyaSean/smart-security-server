import threading
from queue import Queue

# Shared state for the application
camera_streams = {}
camera_caps = {}
stop_event = threading.Event()

# Frame buffers for each camera
frame_queues = {
    1: Queue(maxsize=10),  # Buffer for camera 1
    2: Queue(maxsize=10)   # Buffer for camera 2
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
        pass  # Drop frame if queue is full
