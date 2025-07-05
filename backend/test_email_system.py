#!/usr/bin/env python3
"""
Email System Test Script

This script tests the email notification system functionality including:
- SMTP configuration validation
- Email template rendering
- Email sending capabilities
- Notification delivery
"""

import os
import sys
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal, engine, get_db
from app.models.base import Base
from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationTemplate, NotificationPreferences,
    NotificationType, NotificationStatus, NotificationFrequency
)
from app.services.email_service import EmailService
from app.services.notification_templates import create_default_templates
from app.core.config import settings


def test_email_configuration():
    """Test email configuration and SMTP connection"""
    print("\n🔧 Testing Email Configuration")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        email_service = EmailService(db)
        
        print(f"Email Enabled: {email_service.enabled}")
        print(f"Test Mode: {email_service.test_mode}")
        print(f"SMTP Host: {email_service.smtp_config['host']}")
        print(f"SMTP Port: {email_service.smtp_config['port']}")
        print(f"From Email: {email_service.smtp_config['from_email']}")
        print(f"From Name: {email_service.smtp_config['from_name']}")
        
        # Test SMTP connection
        connection_test = email_service.test_connection()
        print(f"\nConnection Test: {'✅ PASSED' if connection_test['success'] else '❌ FAILED'}")
        print(f"Message: {connection_test['message']}")
        if connection_test.get('details'):
            print(f"Details: {connection_test['details']}")
        
        return connection_test['success']
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_email_templates():
    """Test email template creation and rendering"""
    print("\n📧 Testing Email Templates")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create default templates
        create_default_templates(db)
        
        # Get email templates
        templates = db.query(NotificationTemplate).filter(
            NotificationTemplate.notification_type == NotificationType.EMAIL
        ).all()
        
        print(f"Found {len(templates)} email templates:")
        for template in templates:
            print(f"  - {template.name} ({template.language})")
        
        if templates:
            # Test template rendering
            email_service = EmailService(db)
            test_template = templates[0]
            
            # Sample context
            context = {
                'user': {'username': 'Test User', 'email': 'test@example.com'},
                'notification': {'title': 'Test Notification', 'message': 'This is a test'},
                'listing': {
                    'make': 'BMW',
                    'model': '3 Series',
                    'year': 2020,
                    'price': 25000,
                    'city': 'Munich',
                    'listing_url': 'https://example.com/listing/123'
                },
                'alert': {'name': 'Test Alert'},
                'match': {
                    'score': 0.95,
                    'matched_criteria': ['make', 'model', 'price']
                },
                'settings': {
                    'app_name': settings.PROJECT_NAME,
                    'app_url': 'https://autoscouter.com'
                }
            }
            
            rendered = email_service.render_template(test_template, context)
            print(f"\n✅ Template rendering successful:")
            print(f"Subject: {rendered['subject'][:50]}...")
            print(f"Text content length: {len(rendered['text_content'])} chars")
            print(f"HTML content length: {len(rendered['html_content'])} chars")
            
            return True
        else:
            print("❌ No email templates found")
            return False
            
    except Exception as e:
        print(f"❌ Template test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_send_email():
    """Test sending a basic email"""
    print("\n📤 Testing Email Sending")
    print("=" * 50)
    
    # Get test email from environment or use default
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    print(f"Test email address: {test_email}")
    
    if test_email == "test@example.com":
        print("⚠️ Using default test email. Set TEST_EMAIL environment variable for actual testing.")
    
    db = SessionLocal()
    try:
        email_service = EmailService(db)
        
        # Send test email
        result = email_service.send_test_email(test_email)
        
        if result['success']:
            print("✅ Test email sent successfully")
            print(f"Sent at: {result.get('sent_at', 'N/A')}")
            if result.get('test_mode'):
                print("ℹ️ Email was sent in test mode (not actually delivered)")
        else:
            print(f"❌ Test email failed: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Email sending test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_notification_email():
    """Test sending notification email with template"""
    print("\n🔔 Testing Notification Email")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create or get test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash="dummy_hash",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create test notification
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Vehicle Alert",
            message="A new BMW 3 Series matching your criteria has been found!",
            content_data={
                'listing': {
                    'make': 'BMW',
                    'model': '3 Series',
                    'year': 2020,
                    'price': 25000,
                    'city': 'Munich',
                    'listing_url': 'https://example.com/listing/123'
                },
                'alert': {'name': 'BMW 3 Series Alert'},
                'match': {'score': 0.95, 'matched_criteria': ['make', 'model', 'price']}
            }
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send notification email
        email_service = EmailService(db)
        success = email_service.send_notification_email(notification)
        
        if success:
            print("✅ Notification email sent successfully")
            print(f"Notification ID: {notification.id}")
            print(f"Status: {notification.status}")
            print(f"Sent at: {notification.sent_at}")
        else:
            print(f"❌ Notification email failed")
            print(f"Status: {notification.status}")
            print(f"Error: {notification.error_message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Notification email test failed: {str(e)}")
        return False
    finally:
        db.close()


def setup_test_environment():
    """Setup test environment and database"""
    print("\n⚙️ Setting up Test Environment")
    print("=" * 50)

    try:
        # Import all models to ensure they're registered
        from app.models import automotive, scout, notifications

        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")

        # Create default templates
        db = SessionLocal()
        try:
            create_default_templates(db)
            print("✅ Default email templates created")
        finally:
            db.close()

        return True

    except Exception as e:
        print(f"❌ Test environment setup failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Auto Scouter Email System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Test environment setup failed")
        return False
    
    # Run tests
    tests = [
        ("Email Configuration", test_email_configuration),
        ("Email Templates", test_email_templates),
        ("Email Sending", test_send_email),
        ("Notification Email", test_notification_email)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check configuration and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
