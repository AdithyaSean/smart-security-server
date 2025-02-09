import logging
from typing import Optional
from firebase_admin import messaging

logger = logging.getLogger(__name__)

class FaceUnknownNotifier:
    def __init__(self, firebase_app=None):
        """Initialize the notifier with Firebase app instance"""
        self.firebase_app = firebase_app

    def notify_unknown_face(self, image_path: str, timestamp: Optional[str] = None) -> bool:
        """Send a notification when an unknown face is detected"""
        try:
            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title='Unknown Person Detected',
                    body=f'An unknown person was detected at {timestamp if timestamp else "the premises"}.'
                ),
                data={
                    'type': 'unknown_face',
                    'image_path': image_path,
                    'timestamp': timestamp or '',
                },
                topic='security_alerts'  # All devices subscribed to this topic will receive the notification
            )
            
            # Send message
            response = messaging.send(message, app=self.firebase_app)
            logger.info(f'Successfully sent unknown face notification: {response}')
            return True
            
        except Exception as e:
            logger.error(f'Error sending unknown face notification: {e}')
            return False
