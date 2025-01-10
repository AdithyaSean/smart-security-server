import os
import cv2
from enhance import enhance_image
from firebase_service import FirebaseService

def apply_night_vision(image):
    # Apply CLAHE for better contrast in dark areas
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    return clahe.apply(image)

def detect_faces(image_path, intensity, camera_id):
    firebase_service = FirebaseService()
    upscale_factor = 2
    intensity_threshold = 50
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if intensity < intensity_threshold:
        image = apply_night_vision(gray)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    if len(faces) > 0:
        for (x, y, w, h) in faces:
            face = image[y:y+h, x:x+w]

            upscaled_face = cv2.resize(face, (w * upscale_factor, h * upscale_factor), interpolation=cv2.INTER_LINEAR)

            # Path for saving the enhanced face image
            face_image_path = os.path.splitext(image_path)[0].replace('original', 'segmented') + '_face.jpg'
            cv2.imwrite(face_image_path, upscaled_face)

            # Enhance the cropped face image and save it
            enhanced_face_path = face_image_path.replace('_face.jpg', '_enhanced_face.jpg')
            enhance_image(face_image_path, enhanced_face_path)

            # Upload original face to Firebase
            firebase_service.upload_image_data(face_image_path, 'segmented', camera_id)
            
            # Upload enhanced face to Firebase
            firebase_service.upload_image_data(enhanced_face_path, 'enhanced', camera_id)

        print("Faces detected and enhanced successfully!")
    else:
        print("No faces detected.")