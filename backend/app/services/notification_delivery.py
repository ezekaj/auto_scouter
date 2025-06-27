"""
Notification Delivery System

This module handles the delivery of notifications through various channels.
"""

import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from jinja2 import Template
from sqlalchemy.orm import Session

from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate, 
    NotificationQueue, NotificationStatus, NotificationType
)
from app.models.scout import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationDeliveryService:
    """Service for delivering notifications through various channels"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_config = self._get_email_config()
        
    def _get_email_config(self) -> Dict[str, Any]:
        """Get email configuration from settings"""
        return {
            "smtp_server": getattr(settings, "SMTP_SERVER", "localhost"),
            "smtp_port": getattr(settings, "SMTP_PORT", 587),
            "smtp_username": getattr(settings, "SMTP_USERNAME", ""),
            "smtp_password": getattr(settings, "SMTP_PASSWORD", ""),
            "smtp_use_tls": getattr(settings, "SMTP_USE_TLS", True),
            "from_email": getattr(settings, "FROM_EMAIL", "noreply@autoscouter.com"),
            "from_name": getattr(settings, "FROM_NAME", "Auto Scouter")
        }
    
    def process_notification_queue(self, max_notifications: int = 100) -> Dict[str, int]:
        """
        Process pending notifications from the queue
        
        Returns:
            Dict with processing statistics
        """
        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Get pending notifications from queue
        pending_notifications = self.db.query(NotificationQueue).filter(
            NotificationQueue.status == "queued"
        ).order_by(
            NotificationQueue.priority.desc(),
            NotificationQueue.created_at.asc()
        ).limit(max_notifications).all()
        
        for queue_item in pending_notifications:
            stats["processed"] += 1
            
            try:
                # Mark as processing
                queue_item.status = "processing"
                queue_item.processing_started_at = datetime.utcnow()
                self.db.commit()
                
                # Get the notification
                notification = self.db.query(Notification).filter(
                    Notification.id == queue_item.notification_id
                ).first()
                
                if not notification:
                    queue_item.status = "failed"
                    queue_item.error_message = "Notification not found"
                    stats["failed"] += 1
                    continue
                
                # Check if notification should be sent
                if not self._should_send_notification(notification):
                    queue_item.status = "completed"
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = "Notification delivery conditions not met"
                    stats["skipped"] += 1
                    continue
                
                # Deliver the notification
                success = self._deliver_notification(notification)
                
                if success:
                    queue_item.status = "completed"
                    queue_item.processing_completed_at = datetime.utcnow()
                    stats["sent"] += 1
                else:
                    # Handle retry logic
                    if queue_item.retry_count < 3:
                        queue_item.retry_count += 1
                        queue_item.status = "queued"
                        # Schedule retry with exponential backoff
                        retry_delay = timedelta(minutes=5 * (2 ** queue_item.retry_count))
                        queue_item.scheduled_for = datetime.utcnow() + retry_delay
                    else:
                        queue_item.status = "failed"
                        notification.status = NotificationStatus.FAILED
                        stats["failed"] += 1
                
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Error processing notification queue item {queue_item.id}: {str(e)}")
                queue_item.status = "failed"
                queue_item.error_message = str(e)
                stats["failed"] += 1
                self.db.commit()
        
        return stats
    
    def _should_send_notification(self, notification: Notification) -> bool:
        """Check if notification should be sent based on user preferences and quiet hours"""
        # Get user preferences
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == notification.user_id
        ).first()
        
        if not prefs:
            return True  # Send if no preferences set
        
        # Check if notification type is enabled
        if notification.notification_type == NotificationType.EMAIL and not prefs.email_enabled:
            return False
        elif notification.notification_type == NotificationType.IN_APP and not prefs.in_app_enabled:
            return False
        elif notification.notification_type == NotificationType.PUSH and not prefs.push_enabled:
            return False
        elif notification.notification_type == NotificationType.SMS and not prefs.sms_enabled:
            return False
        
        # Check quiet hours
        if prefs.quiet_hours_enabled:
            current_time = datetime.utcnow().time()
            quiet_start = datetime.strptime(prefs.quiet_hours_start, "%H:%M").time()
            quiet_end = datetime.strptime(prefs.quiet_hours_end, "%H:%M").time()
            
            if quiet_start <= quiet_end:
                # Same day quiet hours
                if quiet_start <= current_time <= quiet_end:
                    return False
            else:
                # Overnight quiet hours
                if current_time >= quiet_start or current_time <= quiet_end:
                    return False
        
        return True
    
    def _deliver_notification(self, notification: Notification) -> bool:
        """Deliver a notification through the appropriate channel"""
        try:
            if notification.notification_type == NotificationType.EMAIL:
                return self._send_email_notification(notification)
            elif notification.notification_type == NotificationType.IN_APP:
                return self._send_in_app_notification(notification)
            elif notification.notification_type == NotificationType.PUSH:
                return self._send_push_notification(notification)
            elif notification.notification_type == NotificationType.SMS:
                return self._send_sms_notification(notification)
            else:
                logger.error(f"Unknown notification type: {notification.notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error delivering notification {notification.id}: {str(e)}")
            notification.error_message = str(e)
            return False
    
    def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification"""
        try:
            # Get user details
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return False
            
            # Get email template
            template = self._get_notification_template(
                NotificationType.EMAIL, 
                "alert_match"
            )
            
            # Render email content
            subject, html_content, text_content = self._render_email_content(
                template, notification, user
            )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_config['from_name']} <{self.email_config['from_email']}>"
            msg['To'] = user.email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['smtp_use_tls']:
                    server.starttls()
                
                if self.email_config['smtp_username']:
                    server.login(
                        self.email_config['smtp_username'], 
                        self.email_config['smtp_password']
                    )
                
                server.send_message(msg)
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"Email notification {notification.id} sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification {notification.id}: {str(e)}")
            notification.error_message = str(e)
            return False
    
    def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send in-app notification (just mark as sent since it's stored in DB)"""
        try:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"In-app notification {notification.id} marked as sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send in-app notification {notification.id}: {str(e)}")
            return False
    
    def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification (placeholder for future implementation)"""
        try:
            # TODO: Implement push notification delivery
            # This would integrate with services like Firebase Cloud Messaging,
            # Apple Push Notification Service, etc.
            
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"Push notification {notification.id} sent (placeholder)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification {notification.id}: {str(e)}")
            return False
    
    def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification (placeholder for future implementation)"""
        try:
            # TODO: Implement SMS delivery using services like Twilio, AWS SNS, etc.
            
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"SMS notification {notification.id} sent (placeholder)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification {notification.id}: {str(e)}")
            return False
    
    def _get_notification_template(self, 
                                 notification_type: NotificationType, 
                                 template_name: str) -> Optional[NotificationTemplate]:
        """Get notification template by type and name"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.notification_type == notification_type,
            NotificationTemplate.name == template_name,
            NotificationTemplate.is_active == True
        ).first()
    
    def _render_email_content(self, 
                            template: Optional[NotificationTemplate],
                            notification: Notification,
                            user: User) -> tuple[str, str, str]:
        """Render email content using template"""
        # Prepare template variables
        template_vars = {
            "user": {
                "username": user.username,
                "email": user.email
            },
            "notification": {
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at
            }
        }
        
        # Add content data if available
        if notification.content_data:
            template_vars.update(notification.content_data)
        
        if template:
            # Use custom template
            subject_template = Template(template.subject_template or notification.title)
            html_template = Template(template.html_template or "")
            text_template = Template(template.message_template)
            
            subject = subject_template.render(**template_vars)
            html_content = html_template.render(**template_vars) if template.html_template else ""
            text_content = text_template.render(**template_vars)
        else:
            # Use default content
            subject = notification.title
            text_content = notification.message
            html_content = self._generate_default_html_content(notification, user)
        
        return subject, html_content, text_content
    
    def _generate_default_html_content(self, notification: Notification, user: User) -> str:
        """Generate default HTML email content"""
        content_data = notification.content_data or {}
        listing = content_data.get("listing", {})
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">🚗 {notification.title}</h2>
            
            <p>Hello {user.username},</p>
            
            <p>{notification.message}</p>
        """
        
        if listing:
            html += f"""
            <div style="border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3 style="margin-top: 0;">{listing.get('make', '')} {listing.get('model', '')}</h3>
                
                <table style="width: 100%;">
                    <tr>
                        <td><strong>Year:</strong></td>
                        <td>{listing.get('year', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td><strong>Price:</strong></td>
                        <td>€{listing.get('price', 0):,.0f}</td>
                    </tr>
                    <tr>
                        <td><strong>Mileage:</strong></td>
                        <td>{listing.get('mileage', 'N/A'):,} km</td>
                    </tr>
                    <tr>
                        <td><strong>Fuel Type:</strong></td>
                        <td>{listing.get('fuel_type', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td><strong>Location:</strong></td>
                        <td>{listing.get('city', 'N/A')}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px;">
                    <a href="{listing.get('listing_url', '#')}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Listing
                    </a>
                </p>
            </div>
            """
        
        html += f"""
            <hr style="margin: 30px 0;">
            
            <p style="font-size: 12px; color: #666;">
                You received this notification because you have an active alert that matches this listing.
                <br>
                <a href="http://localhost:3000/alerts">Manage your alerts</a> | 
                <a href="http://localhost:3000/notifications/preferences">Notification preferences</a>
            </p>
        </body>
        </html>
        """
        
        return html
    
    def queue_notification(self, notification: Notification, priority: int = 1) -> bool:
        """Add notification to delivery queue"""
        try:
            queue_item = NotificationQueue(
                notification_id=notification.id,
                priority=priority,
                status="queued"
            )
            
            self.db.add(queue_item)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue notification {notification.id}: {str(e)}")
            return False
    
    def create_and_queue_notification(self,
                                    user_id: int,
                                    notification_type: NotificationType,
                                    title: str,
                                    message: str,
                                    content_data: Optional[Dict[str, Any]] = None,
                                    alert_id: Optional[int] = None,
                                    listing_id: Optional[int] = None,
                                    priority: int = 1) -> Optional[Notification]:
        """Create and queue a notification for delivery"""
        try:
            notification = Notification(
                user_id=user_id,
                alert_id=alert_id,
                listing_id=listing_id,
                notification_type=notification_type,
                title=title,
                message=message,
                content_data=content_data,
                priority=priority
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # Queue for delivery
            if self.queue_notification(notification, priority):
                return notification
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to create and queue notification: {str(e)}")
            return None
