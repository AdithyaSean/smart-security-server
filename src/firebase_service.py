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

def upload_image_data(camera_id, image_type, image_data, face_image, timestamp, print_message):
    try:
        data = {
            'cameraId': camera_id,
            'imageType': image_type,
            'imageData': image_data,
            'imageName': face_image,
            'timestamp': timestamp
        }
        
        # Use the face image path as the key
        ref = db.reference('faces').child(f'camera_{camera_id}').child(face_image)
        ref.set(data)
        print(print_message + f"Uploaded")

        return True
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return False