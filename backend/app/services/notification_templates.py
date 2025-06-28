"""
Notification Template Management

This module handles creation and management of notification templates.
"""

from sqlalchemy.orm import Session
from app.models.notifications import NotificationTemplate, NotificationType


def create_default_templates(db: Session):
    """Create default notification templates"""
    
    templates = [
        # Email templates
        {
            "name": "vehicle_alert_email",
            "notification_type": NotificationType.EMAIL,
            "language": "en",
            "subject_template": "🚗 New {{ listing.make }} {{ listing.model }} matches your alert!",
            "title_template": "New vehicle match found",
            "message_template": """Hi {{ user.username }},

Great news! We found a vehicle that matches your alert "{{ alert.name }}":

{{ listing.make }} {{ listing.model }}{% if listing.year %} ({{ listing.year }}){% endif %}
{% if listing.price %}Price: €{{ "{:,.0f}".format(listing.price) }}{% endif %}
{% if listing.mileage %}Mileage: {{ "{:,}".format(listing.mileage) }} km{% endif %}
{% if listing.fuel_type %}Fuel: {{ listing.fuel_type }}{% endif %}
{% if listing.transmission %}Transmission: {{ listing.transmission }}{% endif %}
{% if listing.city %}Location: {{ listing.city }}{% endif %}

{% if listing.listing_url %}View full details: {{ listing.listing_url }}{% endif %}

This vehicle matches {{ match.matched_criteria|length }} of your criteria with a {{ "{:.0%}".format(match.score) }} match score.

Happy car hunting!
The Auto Scouter Team

---
Manage your alerts: {{ settings.app_url }}/alerts
Unsubscribe: {{ settings.app_url }}/unsubscribe""",
            "html_template": """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ notification.title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; }
        .header { background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 30px 20px; text-align: center; }
        .content { padding: 30px 20px; }
        .vehicle-card { border: 2px solid #e9ecef; border-radius: 12px; padding: 20px; margin: 20px 0; background: #f8f9fa; }
        .vehicle-title { font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px; }
        .price { font-size: 28px; font-weight: bold; color: #28a745; margin: 15px 0; }
        .specs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
        .spec-item { padding: 8px 12px; background: white; border-radius: 6px; border-left: 4px solid #007bff; }
        .spec-label { font-weight: bold; color: #6c757d; font-size: 12px; text-transform: uppercase; }
        .spec-value { color: #212529; font-size: 14px; }
        .match-score { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; }
        .button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #28a745, #20c997); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; text-align: center; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; border-top: 1px solid #e9ecef; }
        .footer a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 {{ settings.app_name }}</h1>
            <h2>{{ notification.title }}</h2>
        </div>
        
        <div class="content">
            <p>Hi {{ user.username }},</p>
            <p>Great news! We found a vehicle that matches your alert <strong>"{{ alert.name }}"</strong>:</p>
            
            <div class="vehicle-card">
                <div class="vehicle-title">{{ listing.make }} {{ listing.model }}{% if listing.year %} ({{ listing.year }}){% endif %}</div>
                
                {% if listing.price %}
                <div class="price">€{{ "{:,.0f}".format(listing.price) }}</div>
                {% endif %}
                
                <div class="specs">
                    {% if listing.mileage %}
                    <div class="spec-item">
                        <div class="spec-label">Mileage</div>
                        <div class="spec-value">{{ "{:,}".format(listing.mileage) }} km</div>
                    </div>
                    {% endif %}
                    {% if listing.fuel_type %}
                    <div class="spec-item">
                        <div class="spec-label">Fuel Type</div>
                        <div class="spec-value">{{ listing.fuel_type }}</div>
                    </div>
                    {% endif %}
                    {% if listing.transmission %}
                    <div class="spec-item">
                        <div class="spec-label">Transmission</div>
                        <div class="spec-value">{{ listing.transmission }}</div>
                    </div>
                    {% endif %}
                    {% if listing.city %}
                    <div class="spec-item">
                        <div class="spec-label">Location</div>
                        <div class="spec-value">{{ listing.city }}</div>
                    </div>
                    {% endif %}
                </div>
                
                {% if listing.listing_url %}
                <a href="{{ listing.listing_url }}" class="button">🔍 View Full Details</a>
                {% endif %}
            </div>
            
            <div class="match-score">
                <strong>Match Score: {{ "{:.0%}".format(match.score) }}</strong><br>
                <small>This vehicle matches {{ match.matched_criteria|length }} of your criteria</small>
            </div>
            
            <p>Happy car hunting!<br><strong>The Auto Scouter Team</strong></p>
        </div>
        
        <div class="footer">
            <p><a href="{{ settings.app_url }}/alerts">Manage your alerts</a> | <a href="{{ settings.app_url }}/unsubscribe">Unsubscribe</a></p>
            <p>© {{ settings.app_name }} - Your trusted vehicle alert service</p>
        </div>
    </div>
</body>
</html>""",
            "variables": ["user", "listing", "alert", "match", "settings"]
        },
        
        # Daily digest email template
        {
            "name": "daily_digest_email",
            "notification_type": NotificationType.EMAIL,
            "language": "en",
            "subject_template": "📊 Daily Digest - {{ notification_count }} new vehicle matches",
            "title_template": "Your daily vehicle matches",
            "message_template": """Hi {{ user.username }},

Here's your daily summary of vehicle matches:

{% for alert_id, count in alert_groups.items() %}
• Alert {{ alert_id }}: {{ count }} new matches
{% endfor %}

Total matches today: {{ notification_count }}

Visit your dashboard to see all the details: {{ settings.app_url }}/dashboard

Best regards,
The Auto Scouter Team""",
            "html_template": """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Daily Digest</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; }
        .header { background-color: #6f42c1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .summary-card { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .alert-item { padding: 10px 0; border-bottom: 1px solid #e9ecef; }
        .count { font-weight: bold; color: #28a745; }
        .button { display: inline-block; padding: 12px 24px; background-color: #6f42c1; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Daily Digest</h1>
            <h2>{{ notification_count }} New Matches</h2>
        </div>
        
        <div class="content">
            <p>Hi {{ user.username }},</p>
            <p>Here's your daily summary of vehicle matches:</p>
            
            <div class="summary-card">
                {% for alert_id, count in alert_groups.items() %}
                <div class="alert-item">
                    Alert {{ alert_id }}: <span class="count">{{ count }} new matches</span>
                </div>
                {% endfor %}
            </div>
            
            <a href="{{ settings.app_url }}/dashboard" class="button">View All Matches</a>
            
            <p>Best regards,<br><strong>The Auto Scouter Team</strong></p>
        </div>
        
        <div class="footer">
            <p><a href="{{ settings.app_url }}/alerts">Manage alerts</a> | <a href="{{ settings.app_url }}/preferences">Email preferences</a></p>
        </div>
    </div>
</body>
</html>""",
            "variables": ["user", "notification_count", "alert_groups", "settings"]
        },
        
        # In-app notification template
        {
            "name": "vehicle_alert_in_app",
            "notification_type": NotificationType.IN_APP,
            "language": "en",
            "title_template": "New {{ listing.make }} {{ listing.model }} match",
            "message_template": "{{ listing.make }} {{ listing.model }}{% if listing.year %} ({{ listing.year }}){% endif %} - {% if listing.price %}€{{ '{:,.0f}'.format(listing.price) }}{% else %}Price on request{% endif %}{% if listing.city %} in {{ listing.city }}{% endif %}",
            "variables": ["listing", "alert", "match"]
        },
        
        # Push notification template
        {
            "name": "vehicle_alert_push",
            "notification_type": NotificationType.PUSH,
            "language": "en",
            "title_template": "🚗 New vehicle match!",
            "message_template": "{{ listing.make }} {{ listing.model }} - {% if listing.price %}€{{ '{:,.0f}'.format(listing.price) }}{% else %}Price on request{% endif %}",
            "variables": ["listing"]
        }
    ]
    
    for template_data in templates:
        # Check if template already exists
        existing = db.query(NotificationTemplate).filter(
            NotificationTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = NotificationTemplate(**template_data)
            db.add(template)
    
    db.commit()


def get_template_variables():
    """Get available template variables for documentation"""
    return {
        "user": {
            "username": "User's username",
            "email": "User's email address"
        },
        "listing": {
            "id": "Listing ID",
            "make": "Vehicle make",
            "model": "Vehicle model", 
            "year": "Vehicle year",
            "price": "Vehicle price",
            "mileage": "Vehicle mileage",
            "fuel_type": "Fuel type",
            "transmission": "Transmission type",
            "body_type": "Body type",
            "city": "Location city",
            "region": "Location region",
            "listing_url": "URL to view listing",
            "primary_image_url": "Main image URL"
        },
        "alert": {
            "id": "Alert ID",
            "name": "Alert name",
            "criteria": "Alert criteria object"
        },
        "match": {
            "score": "Match score (0.0 to 1.0)",
            "matched_criteria": "List of matched criteria",
            "is_perfect_match": "Boolean for perfect matches"
        },
        "notification": {
            "title": "Notification title",
            "message": "Notification message",
            "created_at": "Creation timestamp",
            "priority": "Notification priority"
        },
        "settings": {
            "app_name": "Application name",
            "app_url": "Application URL"
        }
    }
