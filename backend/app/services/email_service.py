"""
Enhanced Email Service for Auto Scouter

This module provides comprehensive email functionality including:
- SMTP configuration and connection management
- Email template rendering with Jinja2
- HTML and text email support
- Email delivery tracking
- Retry logic and error handling
- Email testing and validation
"""

import logging
import smtplib
import ssl
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formataddr
from jinja2 import Template, Environment, BaseLoader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notifications import (
    Notification, NotificationTemplate, NotificationType, NotificationStatus
)
from app.models.scout import User

logger = logging.getLogger(__name__)


class EmailService:
    """Enhanced email service with comprehensive functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.smtp_config = {
            'host': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'user': settings.SMTP_USER,
            'password': settings.SMTP_PASSWORD,
            'use_tls': settings.SMTP_TLS,
            'use_ssl': settings.SMTP_SSL,
            'from_email': settings.EMAIL_FROM,
            'from_name': settings.EMAIL_FROM_NAME
        }
        self.enabled = settings.EMAIL_ENABLED
        self.test_mode = settings.EMAIL_TEST_MODE
        
    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and configuration"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'message': 'Email service is disabled',
                    'details': 'Set EMAIL_ENABLED=true to enable email service'
                }
            
            if not self.smtp_config['user'] or not self.smtp_config['password']:
                return {
                    'success': False,
                    'message': 'SMTP credentials not configured',
                    'details': 'Set SMTP_USER and SMTP_PASSWORD environment variables'
                }
            
            # Test SMTP connection
            server = self._create_smtp_connection()
            server.quit()
            
            return {
                'success': True,
                'message': 'SMTP connection successful',
                'details': f"Connected to {self.smtp_config['host']}:{self.smtp_config['port']}"
            }
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return {
                'success': False,
                'message': 'SMTP connection failed',
                'details': str(e)
            }
    
    def _create_smtp_connection(self):
        """Create and configure SMTP connection"""
        if self.smtp_config['use_ssl']:
            # Use SSL connection
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                self.smtp_config['host'], 
                self.smtp_config['port'], 
                context=context
            )
        else:
            # Use regular connection with optional TLS
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            if self.smtp_config['use_tls']:
                server.starttls()
        
        # Login if credentials provided
        if self.smtp_config['user'] and self.smtp_config['password']:
            server.login(self.smtp_config['user'], self.smtp_config['password'])
        
        return server
    
    def send_email(self, 
                   to_email: str,
                   subject: str,
                   text_content: Optional[str] = None,
                   html_content: Optional[str] = None,
                   from_email: Optional[str] = None,
                   from_name: Optional[str] = None,
                   reply_to: Optional[str] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send email with comprehensive options"""
        
        if not self.enabled:
            logger.warning("Email service is disabled")
            return {
                'success': False,
                'message': 'Email service is disabled',
                'sent_at': None
            }
        
        if self.test_mode:
            logger.info(f"TEST MODE: Would send email to {to_email} with subject: {subject}")
            return {
                'success': True,
                'message': 'Email sent (test mode)',
                'sent_at': datetime.utcnow(),
                'test_mode': True
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((
                from_name or self.smtp_config['from_name'],
                from_email or self.smtp_config['from_email']
            ))
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            server = self._create_smtp_connection()
            server.send_message(msg)
            server.quit()
            
            sent_at = datetime.utcnow()
            logger.info(f"Email sent successfully to {to_email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'sent_at': sent_at
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'sent_at': None
            }
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            if attachment.get('type') == 'image':
                with open(attachment['path'], 'rb') as f:
                    img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-Disposition', 
                               f'attachment; filename="{attachment["filename"]}"')
                msg.attach(image)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {str(e)}")
    
    def render_template(self, 
                       template: NotificationTemplate,
                       context: Dict[str, Any]) -> Dict[str, str]:
        """Render email template with context data"""
        try:
            jinja_env = Environment(loader=BaseLoader())
            
            # Render subject
            subject = ""
            if template.subject_template:
                subject_tmpl = jinja_env.from_string(template.subject_template)
                subject = subject_tmpl.render(**context)
            
            # Render text content
            text_content = ""
            if template.message_template:
                text_tmpl = jinja_env.from_string(template.message_template)
                text_content = text_tmpl.render(**context)
            
            # Render HTML content
            html_content = ""
            if template.html_template:
                html_tmpl = jinja_env.from_string(template.html_template)
                html_content = html_tmpl.render(**context)
            
            return {
                'subject': subject,
                'text_content': text_content,
                'html_content': html_content
            }
            
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            raise
    
    def send_notification_email(self, notification: Notification) -> bool:
        """Send email notification using template"""
        try:
            # Get user
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user or not user.email:
                logger.error(f"User {notification.user_id} not found or has no email")
                return False
            
            # Get email template
            template = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.notification_type == NotificationType.EMAIL,
                NotificationTemplate.name.like('%alert%'),
                NotificationTemplate.is_active == True
            ).first()
            
            if not template:
                logger.error("No active email template found")
                return False
            
            # Prepare context
            context = {
                'user': user,
                'notification': notification,
                'settings': {
                    'app_name': settings.PROJECT_NAME,
                    'app_url': 'https://autoscouter.com'  # TODO: Make configurable
                }
            }
            
            # Add notification content data if available
            if notification.content_data:
                context.update(notification.content_data)
            
            # Render template
            rendered = self.render_template(template, context)
            
            # Send email
            result = self.send_email(
                to_email=user.email,
                subject=rendered['subject'],
                text_content=rendered['text_content'],
                html_content=rendered['html_content']
            )
            
            # Update notification status
            if result['success']:
                notification.status = NotificationStatus.SENT
                notification.sent_at = result['sent_at']
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = result['message']
            
            self.db.commit()
            return result['success']
            
        except Exception as e:
            logger.error(f"Failed to send notification email {notification.id}: {str(e)}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            self.db.commit()
            return False
    
    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """Send test email to verify configuration"""
        subject = f"Test Email from {settings.PROJECT_NAME}"
        text_content = f"""
        Hello!
        
        This is a test email from {settings.PROJECT_NAME}.
        
        If you received this email, your email configuration is working correctly.
        
        Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        
        Best regards,
        The Auto Scouter Team
        """
        
        html_content = f"""
        <html>
        <body>
            <h2>Test Email from {settings.PROJECT_NAME}</h2>
            <p>Hello!</p>
            <p>This is a test email from <strong>{settings.PROJECT_NAME}</strong>.</p>
            <p>If you received this email, your email configuration is working correctly.</p>
            <p><small>Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</small></p>
            <hr>
            <p>Best regards,<br><strong>The Auto Scouter Team</strong></p>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )
