"""
Firebase Cloud Messaging Service
Handles push notifications for mobile app
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from app.core.cloud_config import get_cloud_settings

logger = logging.getLogger(__name__)
cloud_settings = get_cloud_settings()

class FirebaseNotificationService:
    """Firebase Cloud Messaging service for push notifications"""
    
    def __init__(self):
        self.app = None
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not FIREBASE_AVAILABLE:
            logger.warning("⚠️  Firebase Admin SDK not available - push notifications disabled")
            return
        
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                self.initialized = True
                logger.info("✅ Firebase already initialized")
                return
            
            # Initialize with credentials
            if cloud_settings.firebase_credentials_path:
                cred = credentials.Certificate(cloud_settings.firebase_credentials_path)
                self.app = firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("✅ Firebase initialized with credentials file")
            elif cloud_settings.firebase_project_id:
                # Use default credentials (for cloud deployment)
                cred = credentials.ApplicationDefault()
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': cloud_settings.firebase_project_id
                })
                self.initialized = True
                logger.info("✅ Firebase initialized with default credentials")
            else:
                logger.warning("⚠️  Firebase credentials not configured - push notifications disabled")
                
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            self.initialized = False
    
    def send_vehicle_match_notification(
        self, 
        device_token: str, 
        vehicle_data: Dict[str, Any], 
        match_score: float
    ) -> bool:
        """Send push notification for vehicle match"""
        if not self.initialized:
            logger.warning("⚠️  Firebase not initialized - cannot send push notification")
            return False
        
        try:
            # Create notification payload
            title = f"New {vehicle_data['make']} {vehicle_data['model']} Match!"
            body = f"Found a {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']} for {vehicle_data['price']} EUR in {vehicle_data['city']}"
            
            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=vehicle_data.get('primary_image_url')
                ),
                data={
                    'type': 'vehicle_match',
                    'vehicle_id': str(vehicle_data['id']),
                    'match_score': str(match_score),
                    'listing_url': vehicle_data.get('listing_url', ''),
                    'timestamp': datetime.utcnow().isoformat()
                },
                token=device_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_car',
                        color='#FF6B35',
                        sound='default',
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    ),
                    priority='high'
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"✅ Push notification sent successfully: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send push notification: {e}")
            return False
    
    def send_bulk_notifications(
        self, 
        device_tokens: List[str], 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send bulk push notifications"""
        if not self.initialized:
            logger.warning("⚠️  Firebase not initialized - cannot send bulk notifications")
            return {"success": 0, "failure": len(device_tokens)}
        
        try:
            # Create multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=device_tokens,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_car',
                        color='#FF6B35',
                        sound='default'
                    ),
                    priority='high'
                )
            )
            
            # Send multicast
            response = messaging.send_multicast(message)
            
            logger.info(f"✅ Bulk notifications sent: {response.success_count} success, {response.failure_count} failures")
            
            # Log failures
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        logger.warning(f"⚠️  Failed to send to token {idx}: {resp.exception}")
            
            return {
                "success": response.success_count,
                "failure": response.failure_count,
                "responses": response.responses
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send bulk notifications: {e}")
            return {"success": 0, "failure": len(device_tokens), "error": str(e)}
    
    def send_test_notification(self, device_token: str) -> bool:
        """Send test notification"""
        if not self.initialized:
            logger.warning("⚠️  Firebase not initialized - cannot send test notification")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Vehicle Scout Test",
                    body="Push notifications are working! 🚗"
                ),
                data={
                    'type': 'test',
                    'timestamp': datetime.utcnow().isoformat()
                },
                token=device_token
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Test notification sent: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test notification failed: {e}")
            return False
    
    def validate_device_token(self, device_token: str) -> bool:
        """Validate device token format"""
        if not device_token or len(device_token) < 10:
            return False
        
        # Basic validation - FCM tokens are typically 152+ characters
        if len(device_token) < 100:
            return False
        
        return True
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get Firebase service status"""
        return {
            "firebase_available": FIREBASE_AVAILABLE,
            "initialized": self.initialized,
            "project_id": cloud_settings.firebase_project_id,
            "credentials_configured": bool(cloud_settings.firebase_credentials_path),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global Firebase service instance
firebase_service = FirebaseNotificationService()

def get_firebase_service() -> FirebaseNotificationService:
    """Get Firebase service instance"""
    return firebase_service

# Fallback notification service for when Firebase is not available
class FallbackNotificationService:
    """Fallback notification service using email or webhooks"""
    
    def __init__(self):
        self.email_enabled = bool(cloud_settings.smtp_host)
    
    def send_email_notification(
        self, 
        email: str, 
        subject: str, 
        body: str
    ) -> bool:
        """Send email notification as fallback"""
        if not self.email_enabled:
            logger.warning("⚠️  Email notifications not configured")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = cloud_settings.smtp_user
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(cloud_settings.smtp_host, cloud_settings.smtp_port)
            server.starttls()
            server.login(cloud_settings.smtp_user, cloud_settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email notification sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email notification failed: {e}")
            return False
    
    def send_vehicle_match_email(
        self, 
        email: str, 
        vehicle_data: Dict[str, Any], 
        match_score: float
    ) -> bool:
        """Send vehicle match notification via email"""
        subject = f"Vehicle Scout: New {vehicle_data['make']} {vehicle_data['model']} Match!"
        
        body = f"""
New Vehicle Match Found!

Vehicle Details:
- Make: {vehicle_data['make']}
- Model: {vehicle_data['model']}
- Year: {vehicle_data['year']}
- Price: {vehicle_data['price']} EUR
- Location: {vehicle_data['city']}
- Match Score: {match_score:.0%}

View Listing: {vehicle_data.get('listing_url', 'N/A')}

This is an automated notification from Vehicle Scout.
        """
        
        return self.send_email_notification(email, subject, body)

# Global fallback service
fallback_service = FallbackNotificationService()

def get_fallback_service() -> FallbackNotificationService:
    """Get fallback notification service"""
    return fallback_service
