import firebase_admin
from firebase_admin import credentials, db
import base64
import os
from dotenv import load_dotenv
import logging

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

def upload_image_data(timestamp, camera_id, image_type, face_image):
    try:
        with open(face_image, 'rb') as f:
            data = {
                'timestamp': timestamp,
                'camera_id': camera_id,
                'image_type': image_type,
                'image_data': base64.b64encode(f.read()).decode('utf-8'),
                'image_name': os.path.basename(face_image)
            }
        ref = db.reference('faces').child(f'camera_{camera_id}')
        ref.push(data)
        return True
    except Exception as e:
        logging.error(f"Firebase upload error: {e}")
        return False