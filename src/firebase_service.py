import firebase_admin
from firebase_admin import credentials, db
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    def __init__(self, credential_path=os.getenv('FIREBASE_CRED_PATH')):
        self.cred = credentials.Certificate(credential_path)
        db_url = os.getenv('FIREBASE_DB_URL')
        if not db_url:
            raise ValueError("FIREBASE_DB_URL environment variable is not set.")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(self.cred, {
                'databaseURL': db_url
            })
        self.db_ref = db.reference('images')
        
    def upload_image_data(self, image_path, image_type, camera_id):
        if not os.path.exists(image_path):
            raise ValueError("Image path does not exist")
        if not isinstance(camera_id, (int, str)):
            raise ValueError("Invalid camera_id type")
        try:
            with open(image_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            timestamp = datetime.now().isoformat()
            image_name = os.path.basename(image_path)
            
            data = {
                'timestamp': timestamp,
                'camera_id': camera_id,
                'image_type': image_type,
                'image_data': encoded_image,
                'local_path': image_path,
                'image_name': image_name
            }
            
            self.db_ref.child(f'camera_{camera_id}').push(data)
            return True
        except Exception as e:
            print(f"Firebase upload error: {str(e)}")
            return False
