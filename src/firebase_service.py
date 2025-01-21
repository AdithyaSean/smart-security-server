import firebase_admin
from firebase_admin import credentials, db, storage
import os
from dotenv import load_dotenv

def init_firebase():
    load_dotenv()
    db_url = os.getenv("FIREBASE_DB_URL")
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
    
    if not db_url or not storage_bucket:
        raise ValueError("Firebase configuration not found in environment variables")
        
    cred = credentials.Certificate("firebase/smart-security-project-firebase-adminsdk.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': db_url,
        'storageBucket': storage_bucket
    })
    return db.reference('faces')

import re

def sanitize_key(key):
    # Replace illegal characters with underscores
    return re.sub(r'[\.\$#\[\]/]', '_', key)

def upload_image_data(camera_id, image_type, image_path, image_name, timestamp, print_message):
    try:
        # Upload image to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"images/{image_name}")
        blob.upload_from_filename(image_path)
        
        # Get public URL
        blob.make_public()
        image_url = blob.public_url

        # Store metadata in Realtime Database
        data = {
            'cameraId': camera_id,
            'imageType': image_type,
            'imageUrl': image_url,
            'imageName': image_name,
            'timestamp': timestamp
        }
        
        ref = db.reference('images').child("camera" + str(camera_id))
        ref.push(data)
        print(print_message + f"Uploaded: {image_url}")

        return True
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return False
