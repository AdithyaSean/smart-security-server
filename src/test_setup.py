import cv2
import face_recognition
import numpy as np
import sys
from test_notifications import test_notification_system

def test_dependencies():
    """Test if all required dependencies are working"""
    tests = {
        'OpenCV': False,
        'face_recognition': False
    }
    
    try:
        # Test OpenCV
        cv2.__version__
        tests['OpenCV'] = True
        print("✓ OpenCV is working")
    except Exception as e:
        print(f"✗ OpenCV error: {e}")
    
    try:
        # Test face_recognition (which uses dlib internally)
        # Create a small test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        face_recognition.face_locations(test_image)
        tests['face_recognition'] = True
        print("✓ face_recognition is working")
    except Exception as e:
        print(f"✗ face_recognition error: {e}")
    
    # Final result
    all_passed = all(tests.values())
    print(f"\nOverall test {'passed' if all_passed else 'failed'}")
    return all_passed

if __name__ == "__main__":
    print("Testing system dependencies...\n")
    deps_success = test_dependencies()
    
    if not deps_success:
        print("\nDependency tests failed. Skipping notification test.")
        sys.exit(1)
        
    print("\nTesting notification system...")
    notif_success = test_notification_system()
    
    all_passed = deps_success and notif_success
    print(f"\nOverall test status: {'PASSED' if all_passed else 'FAILED'}")
    sys.exit(0 if all_passed else 1)
