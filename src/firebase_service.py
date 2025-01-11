import firebase_admin
from firebase_admin import credentials, db
import base64
import os
from dotenv import load_dotenv

def init_firebase():
    load_dotenv()
    db_url = os.getenv("FIREBASE_DB_URL")
    if not db_url:
        raise ValueError("FIREBASE_DB_URL not found in environment variables")
        
    cred = credentials.Certificate("firebase/smart-security-project-firebase-adminsdk.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': db_url
    })
    return db.reference('faces')

import re

def sanitize_key(key):
    # Replace illegal characters with underscores
    return re.sub(r'[\.\$#\[\]/]', '_', key)

def upload_image_data(camera_id, image_type, image_data, image_name, timestamp, print_message):
    try:
        # Sanitize the image_name to ensure it's a valid Firebase key
        sanitized_image_name = sanitize_key(image_name)
        
        data = {
            'cameraId': camera_id,
            'imageType': image_type,
            'imageData': image_data,
            'imageName': sanitized_image_name,
            'timestamp': timestamp
        }
        
        # Use the sanitized filename as the key in Firebase
        ref = db.reference('faces').child(sanitized_image_name)
        ref.set(data)
        print(print_message + f"Uploaded")

        return True
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return False