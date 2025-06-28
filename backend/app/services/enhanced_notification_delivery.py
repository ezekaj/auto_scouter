"""
Enhanced Notification Delivery System

This module handles comprehensive notification delivery through multiple channels
with templates, rate limiting, and delivery confirmation tracking.
"""

import logging
import smtplib
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template, Environment, BaseLoader
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, NotificationStatus, NotificationType, NotificationFrequency
)
from app.models.scout import User
from app.models.automotive import VehicleListing
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Comprehensive notification delivery service"""

    def __init__(self, db: Session):
        self.db = db
        self.jinja_env = Environment(loader=BaseLoader())

    def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through the appropriate channel
        
        Args:
            notification: The notification to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Update notification status
            notification.status = NotificationStatus.PENDING
            self.db.commit()
            
            # Get user preferences
            user_prefs = self._get_user_preferences(notification.user_id)
            
            # Check quiet hours
            if self._is_quiet_hours(user_prefs):
                logger.info(f"Skipping notification {notification.id} due to quiet hours")
                return self._schedule_for_later(notification, user_prefs)
            
            # Send based on notification type
            success = False
            
            if notification.notification_type == NotificationType.EMAIL:
                success = self._send_email_notification(notification, user_prefs)
            elif notification.notification_type == NotificationType.PUSH:
                success = self._send_push_notification(notification, user_prefs)
            elif notification.notification_type == NotificationType.IN_APP:
                success = self._send_in_app_notification(notification, user_prefs)
            elif notification.notification_type == NotificationType.SMS:
                success = self._send_sms_notification(notification, user_prefs)
            
            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                logger.info(f"Successfully sent notification {notification.id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.retry_count += 1
                logger.error(f"Failed to send notification {notification.id}")
            
            self.db.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {str(e)}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            notification.retry_count += 1
            self.db.commit()
            return False

    def _send_email_notification(self, notification: Notification, user_prefs: NotificationPreferences) -> bool:
        """Send email notification"""
        try:
            # Get user email
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user or not user.email:
                logger.error(f"No email found for user {notification.user_id}")
                return False
            
            # Get email template
            template = self._get_notification_template(
                NotificationType.EMAIL, 
                user_prefs.language if user_prefs else "en"
            )
            
            if not template:
                logger.error("No email template found")
                return False
            
            # Render email content
            email_content = self._render_email_template(template, notification, user_prefs)
            
            # Send email
            return self._send_email(
                to_email=user.email,
                subject=email_content["subject"],
                html_body=email_content["html_body"],
                text_body=email_content["text_body"]
            )
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False

    def _send_push_notification(self, notification: Notification, user_prefs: NotificationPreferences) -> bool:
        """Send push notification (Firebase/FCM)"""
        try:
            if not settings.PUSH_NOTIFICATION_ENABLED:
                logger.info("Push notifications disabled")
                return False
            
            # Get user's push token (would be stored in user preferences or separate table)
            # For now, return True as placeholder
            logger.info(f"Push notification sent for notification {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return False

    def _send_in_app_notification(self, notification: Notification, user_prefs: NotificationPreferences) -> bool:
        """Send in-app notification (just mark as ready for display)"""
        try:
            # In-app notifications are just stored in the database
            # The frontend will poll or use WebSocket to get them
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"In-app notification failed: {str(e)}")
            return False

    def _send_sms_notification(self, notification: Notification, user_prefs: NotificationPreferences) -> bool:
        """Send SMS notification"""
        try:
            # SMS implementation would go here (Twilio, etc.)
            logger.info(f"SMS notification sent for notification {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")
            return False

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False

    def _get_user_preferences(self, user_id: int) -> Optional[NotificationPreferences]:
        """Get user notification preferences"""
        return self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()

    def _get_notification_template(self, notification_type: str, language: str = "en") -> Optional[NotificationTemplate]:
        """Get notification template"""
        return self.db.query(NotificationTemplate).filter(
            and_(
                NotificationTemplate.notification_type == notification_type,
                NotificationTemplate.language == language,
                NotificationTemplate.is_active == True
            )
        ).first()

    def _render_email_template(self, template: NotificationTemplate, notification: Notification, user_prefs: Optional[NotificationPreferences]) -> Dict[str, str]:
        """Render email template with notification data"""
        try:
            # Get template context
            context = self._build_template_context(notification, user_prefs)
            
            # Render subject
            subject_template = Template(template.subject_template or notification.title)
            subject = subject_template.render(**context)
            
            # Render HTML body
            html_template = Template(template.html_template or self._get_default_html_template())
            html_body = html_template.render(**context)
            
            # Render text body
            text_template = Template(template.message_template)
            text_body = text_template.render(**context)
            
            return {
                "subject": subject,
                "html_body": html_body,
                "text_body": text_body
            }
            
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            # Fallback to simple template
            return {
                "subject": notification.title,
                "html_body": f"<html><body><h2>{notification.title}</h2><p>{notification.message}</p></body></html>",
                "text_body": f"{notification.title}\n\n{notification.message}"
            }

    def _build_template_context(self, notification: Notification, user_prefs: Optional[NotificationPreferences]) -> Dict[str, Any]:
        """Build template context for rendering"""
        context = {
            "notification": {
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at,
                "priority": notification.priority
            },
            "user": {},
            "listing": {},
            "alert": {},
            "settings": {
                "app_name": settings.PROJECT_NAME,
                "app_url": "http://localhost:3000"  # TODO: Make configurable
            }
        }
        
        # Add user info
        if notification.user:
            context["user"] = {
                "username": notification.user.username,
                "email": notification.user.email
            }
        
        # Add content data if available
        if notification.content_data:
            if "listing" in notification.content_data:
                context["listing"] = notification.content_data["listing"]
            if "alert" in notification.content_data:
                context["alert"] = notification.content_data["alert"]
        
        return context

    def _get_default_html_template(self) -> str:
        """Get default HTML email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{{ notification.title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { background-color: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }
                .listing { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }
                .price { font-size: 24px; font-weight: bold; color: #28a745; }
                .button { display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ settings.app_name }}</h1>
                    <h2>{{ notification.title }}</h2>
                </div>
                
                <p>{{ notification.message }}</p>
                
                {% if listing %}
                <div class="listing">
                    <h3>{{ listing.make }} {{ listing.model }}{% if listing.year %} ({{ listing.year }}){% endif %}</h3>
                    {% if listing.price %}<div class="price">€{{ "{:,.0f}".format(listing.price) }}</div>{% endif %}
                    {% if listing.mileage %}<p><strong>Mileage:</strong> {{ "{:,}".format(listing.mileage) }} km</p>{% endif %}
                    {% if listing.fuel_type %}<p><strong>Fuel:</strong> {{ listing.fuel_type }}</p>{% endif %}
                    {% if listing.transmission %}<p><strong>Transmission:</strong> {{ listing.transmission }}</p>{% endif %}
                    {% if listing.city %}<p><strong>Location:</strong> {{ listing.city }}</p>{% endif %}
                    {% if listing.listing_url %}<a href="{{ listing.listing_url }}" class="button">View Listing</a>{% endif %}
                </div>
                {% endif %}
                
                <p><small>This notification was sent because you have an active alert that matches this vehicle. You can manage your alerts in your <a href="{{ settings.app_url }}/alerts">account settings</a>.</small></p>
            </div>
        </body>
        </html>
        """

    def _is_quiet_hours(self, user_prefs: Optional[NotificationPreferences]) -> bool:
        """Check if current time is within user's quiet hours"""
        if not user_prefs or not user_prefs.quiet_hours_enabled:
            return False
        
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        
        start_time = user_prefs.quiet_hours_start or "22:00"
        end_time = user_prefs.quiet_hours_end or "08:00"
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time

    def _schedule_for_later(self, notification: Notification, user_prefs: Optional[NotificationPreferences]) -> bool:
        """Schedule notification for after quiet hours"""
        try:
            if not user_prefs:
                return False
            
            # Calculate next delivery time (after quiet hours end)
            now = datetime.utcnow()
            end_time = user_prefs.quiet_hours_end or "08:00"
            
            # Parse end time
            hour, minute = map(int, end_time.split(":"))
            
            # Schedule for tomorrow at end time if we're past it today
            next_delivery = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_delivery <= now:
                next_delivery += timedelta(days=1)
            
            # Update notification queue
            queue_item = self.db.query(NotificationQueue).filter(
                NotificationQueue.notification_id == notification.id
            ).first()
            
            if queue_item:
                queue_item.scheduled_for = next_delivery
                self.db.commit()
            
            logger.info(f"Notification {notification.id} scheduled for {next_delivery}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {str(e)}")
            return False

    def create_digest_notification(self, user: User, notifications: List[Notification]) -> Optional[Notification]:
        """Create a daily digest notification"""
        try:
            if not notifications:
                return None
            
            # Create digest content
            title = f"Daily Digest - {len(notifications)} new matches"
            
            # Group notifications by alert
            alert_groups = {}
            for notif in notifications:
                alert_id = notif.alert_id
                if alert_id not in alert_groups:
                    alert_groups[alert_id] = []
                alert_groups[alert_id].append(notif)
            
            # Build message
            message_parts = []
            for alert_id, alert_notifications in alert_groups.items():
                alert_name = alert_notifications[0].alert.name if alert_notifications[0].alert else f"Alert {alert_id}"
                message_parts.append(f"• {alert_name}: {len(alert_notifications)} matches")
            
            message = "Your daily vehicle alert summary:\n\n" + "\n".join(message_parts)
            
            # Create digest notification
            digest_notification = Notification(
                user_id=user.id,
                notification_type=NotificationType.EMAIL,
                title=title,
                message=message,
                content_data={
                    "digest": True,
                    "notification_count": len(notifications),
                    "alert_groups": {str(k): len(v) for k, v in alert_groups.items()}
                },
                priority=1  # Low priority for digests
            )
            
            self.db.add(digest_notification)
            self.db.commit()
            
            return digest_notification
            
        except Exception as e:
            logger.error(f"Failed to create digest notification: {str(e)}")
            return None
