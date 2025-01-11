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

def upload_image_data(face_image, image_type, camera_id, timestamp, print_message):
    try:
        with open(face_image, 'rb') as f:
            data = {
                'camera_id': camera_id,
                'image_type': image_type,
                'image_data': base64.b64encode(f.read()).decode('utf-8'),
                'image_name': face_image,
                'timestamp': timestamp
            }
        ref = db.reference('faces').child(f'camera_{camera_id}')
        ref.push(data)
        print(print_message + f"Uploaded")
        return True
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return False