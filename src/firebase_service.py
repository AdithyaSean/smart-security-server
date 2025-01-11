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
                'cameraId': camera_id,
                'imageType': image_type,
                'imageData': base64.b64encode(f.read()).decode('utf-8'),
                'imageName': face_image,
                'timestamp': timestamp
            }
        
        # Extract the file name without the path and extension
        file_name = os.path.splitext(os.path.basename(face_image))[0]
        
        # Use the file name as the key
        ref = db.reference('faces').child(f'camera_{camera_id}').child(file_name)
        ref.set(data)
        
        print(print_message + f"Uploaded")
        return True
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return False