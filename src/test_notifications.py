import os
import cv2
import numpy as np
from face_service import FaceService
from firebase_admin import initialize_app, get_app, delete_app
from firebase_admin import credentials
import logging
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_notification_system():
    """Test the face detection and notification system"""
    try:
        # Initialize Firebase app for testing
        # Load Firebase credentials
        cred_path = os.getenv('FIREBASE_CRED_PATH')
        if not cred_path:
            logger.error("FIREBASE_CRED_PATH environment variable not set")
            return False

        # Get absolute path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_abs_path = os.path.join(project_root, cred_path)
        
        if not os.path.exists(cred_abs_path):
            logger.error(f"Firebase credentials file not found at: {cred_abs_path}")
            return False

        cred = credentials.Certificate(cred_abs_path)
        app = initialize_app(cred, name='test')
        
        # Create test image with a simulated face pattern
        test_img = np.zeros((300, 300, 3), dtype=np.uint8)
        # Draw a face-like circle and features
        cv2.circle(test_img, (150, 150), 100, (200, 200, 200), -1)  # Head
        cv2.circle(test_img, (110, 130), 20, (255, 255, 255), -1)   # Left eye
        cv2.circle(test_img, (190, 130), 20, (255, 255, 255), -1)   # Right eye
        cv2.ellipse(test_img, (150, 180), (50, 20), 0, 0, 180, (150, 150, 150), -1)  # Mouth
        face_service = FaceService(app)
        
        # Create a temporary file to store the test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, test_img)
            
            # Test unknown face detection and notification
            result = face_service.is_face_unknown(test_img, notify=True, image_path=tmp.name)
            
            if result:
                logger.info("Successfully detected unknown face and sent notification")
            else:
                logger.warning("Face was not detected as unknown")
        
        # Cleanup
        delete_app(app)
        os.unlink(tmp.name)
        return True
        
    except Exception as e:
        logger.error(f"Error testing notification system: {e}")
        try:
            delete_app(app)
        except:
            pass
        return False

if __name__ == "__main__":
    print("Testing notification system...")
    success = test_notification_system()
    print(f"Notification test {'passed' if success else 'failed'}")
