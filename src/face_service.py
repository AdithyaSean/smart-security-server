import os
import cv2
import numpy as np
import face_recognition
from typing import Dict, List, Tuple, Optional
import pickle
import logging
from datetime import datetime
from face_unknown_notifier import FaceUnknownNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self, firebase_app=None):
        self.known_face_encodings = []
        self.known_face_paths = []
        self.encodings_file = "faces/known_faces.pkl"
        self.notifier = FaceUnknownNotifier(firebase_app)
        self.load_known_faces()

    def load_known_faces(self):
        """Load known face encodings from pickle file if it exists"""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_paths = data.get('paths', [])
            except Exception as e:
                print(f"Error loading known faces: {e}")

    def save_known_faces(self):
        """Save known face encodings to pickle file"""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({
                    'encodings': self.known_face_encodings,
                    'paths': self.known_face_paths
                }, f)
        except Exception as e:
            print(f"Error saving known faces: {e}")

    def add_known_face(self, face_image: np.ndarray, face_path: str) -> bool:
        """Add a known face to the database"""
        try:
            # Get face encoding
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image, model="hog")
            if not face_locations:
                logger.warning(f"No face detected in image: {face_path}")
                return False
            
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            
            # Check if face is already known
            if self.known_face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if any(matches):
                    logger.info(f"Face already exists in database: {face_path}")
                    return False
            
            # Add to known faces
            self.known_face_encodings.append(face_encoding)
            self.known_face_paths.append(face_path)
            
            # Save updated encodings
            self.save_known_faces()
            logger.info(f"Successfully added new known face: {face_path}")
            return True
        except Exception as e:
            logger.error(f"Error adding known face: {e}")
            return False

    def is_face_unknown(self, face_image: np.ndarray, notify: bool = True, image_path: Optional[str] = None) -> bool:
        """
        Check if a face is unknown by comparing with known faces
        Args:
            face_image: Image containing the face to check
            notify: Whether to send a notification if face is unknown
            image_path: Path to the image file (required for notifications)
        """
        if not self.known_face_encodings:
            logger.info("No known faces in database, treating face as unknown")
            if notify and image_path:
                self.notifier.notify_unknown_face(image_path, datetime.now().isoformat())
            return True

        try:
            # Get face encoding
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image, model="hog")
            if not face_locations:
                logger.warning("No face detected in image")
                return True
            
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            
            # Compare with known faces using a slightly higher tolerance for better reliability
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            is_unknown = not any(matches)
            
            if is_unknown:
                logger.info("Unknown face detected")
                if notify and image_path:
                    self.notifier.notify_unknown_face(image_path, datetime.now().isoformat())
            else:
                logger.info("Known face detected")
                
            return is_unknown

        except Exception as e:
            logger.error(f"Error checking face: {e}")
            return True
