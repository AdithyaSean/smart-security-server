import firebase_admin
from firebase_admin import credentials, db, storage, messaging, get_app
import os
from dotenv import load_dotenv

# Topic for face detection notifications
FACE_NOTIFICATION_TOPIC = 'unknown_faces'

def init_firebase():
    load_dotenv()
    db_url = os.getenv("FIREBASE_DB_URL")
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
    cred_path = os.getenv("FIREBASE_CRED_PATH")
    
    if not db_url or not storage_bucket:
        raise ValueError("Firebase configuration not found in environment variables")
    
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred, {
                'databaseURL': db_url,
                'storageBucket': storage_bucket
            })
        else:
            app = get_app()
        
        # Verify storage bucket connection
        bucket = storage.bucket()
        if not bucket:
            raise ValueError("Failed to connect to Firebase Storage bucket")
            
        print(f"Firebase initialized successfully with bucket: {storage_bucket}")
        return app
        
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")
        raise

def get_firebase_app():
    """Get the Firebase app instance, initializing if necessary"""
    try:
        return get_app()
    except ValueError:
        return init_firebase()

def send_notification(title: str, body: str, image_url: str = None):
    """Send FCM notification to subscribed devices"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                'image_url': image_url if image_url else ''
            },
            topic=FACE_NOTIFICATION_TOPIC,
        )
        response = messaging.send(message)
        print(f"Notification sent successfully: {response}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def upload_image_data(camera_id, image_type, image_path, image_name, timestamp, print_message, notify=False):
    try:
        # Verify file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get bucket with explicit project ID
        bucket = storage.bucket()
        
        # Create storage path with timestamp for better organization
        storage_path = f"camera_{camera_id}/{image_name}"
        blob = bucket.blob(storage_path)
        
        # Upload with content type
        blob.upload_from_filename(
            image_path,
            content_type='image/jpeg'
        )
        
        # Generate signed URL instead of public URL for better security
        image_url = blob.generate_signed_url(
            version='v4',
            expiration=7200,  # 2 hours
            method='GET'
        )

        # Store metadata in Realtime Database
        data = {
            'cameraId': camera_id,
            'imageType': image_type,
            'imageUrl': image_url,
            'imageName': image_name,
            'timestamp': timestamp,
            'storagePath': storage_path
        }
        
        ref = db.reference('images').child(f"camera_{camera_id}")
        ref.push(data)
        
        print(f"{print_message}Uploaded to: {storage_path}")
        
        # Send notification if requested
        if notify:
            send_notification(
                "Unknown Face Detected",
                f"An unknown face was detected by Camera {camera_id}",
                image_url
            )
        
        # Clean up local file
        os.remove(image_path)
        return True
        
    except Exception as e:
        print(f"Firebase upload error for camera {camera_id}: {str(e)}")
        return False
