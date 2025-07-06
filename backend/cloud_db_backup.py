#!/usr/bin/env python3
"""
Cloud Database Backup and Restore Utility
Handles backup and restore operations for PostgreSQL cloud database
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudDatabaseBackup:
    """Cloud database backup and restore manager"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> str:
        """Create a backup of the cloud database"""
        logger.info("💾 Creating cloud database backup...")
        
        try:
            from app.models.cloud_base import SessionLocal
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"cloud_backup_{timestamp}.json"
            
            cloud_db = SessionLocal()
            backup_data = {}
            
            try:
                # Backup users
                logger.info("👥 Backing up users...")
                users = cloud_db.query(User).all()
                backup_data['users'] = [self._serialize_model(user) for user in users]
                logger.info(f"✅ Backed up {len(backup_data['users'])} users")
                
                # Backup vehicles
                logger.info("🚗 Backing up vehicles...")
                vehicles = cloud_db.query(VehicleListing).all()
                backup_data['vehicles'] = [self._serialize_model(vehicle) for vehicle in vehicles]
                logger.info(f"✅ Backed up {len(backup_data['vehicles'])} vehicles")
                
                # Backup alerts
                logger.info("🔔 Backing up alerts...")
                alerts = cloud_db.query(Alert).all()
                backup_data['alerts'] = [self._serialize_model(alert) for alert in alerts]
                logger.info(f"✅ Backed up {len(backup_data['alerts'])} alerts")
                
                # Backup notifications
                logger.info("📧 Backing up notifications...")
                notifications = cloud_db.query(Notification).all()
                backup_data['notifications'] = [self._serialize_model(notification) for notification in notifications]
                logger.info(f"✅ Backed up {len(backup_data['notifications'])} notifications")
                
                # Add metadata
                backup_data['metadata'] = {
                    'backup_date': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'total_records': sum(len(backup_data[key]) for key in backup_data if key != 'metadata')
                }
                
                # Save backup file
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                
                file_size = backup_file.stat().st_size / 1024 / 1024  # MB
                logger.info(f"✅ Backup saved: {backup_file} ({file_size:.2f} MB)")
                
                return str(backup_file)
                
            finally:
                cloud_db.close()
                
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return None
    
    def _serialize_model(self, model) -> Dict[str, Any]:
        """Convert SQLAlchemy model to JSON-serializable dictionary"""
        data = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # Handle datetime objects
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data
    
    def list_backups(self) -> List[str]:
        """List available backup files"""
        backup_files = list(self.backup_dir.glob("cloud_backup_*.json"))
        backup_files.sort(reverse=True)  # Most recent first
        return [str(f) for f in backup_files]
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore database from backup file"""
        logger.info(f"🔄 Restoring from backup: {backup_file}")
        
        try:
            # Load backup data
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Verify backup format
            if 'metadata' not in backup_data:
                logger.error("❌ Invalid backup format - missing metadata")
                return False
            
            metadata = backup_data['metadata']
            logger.info(f"📋 Backup info: {metadata['backup_date']}, {metadata['total_records']} records")
            
            from app.models.cloud_base import SessionLocal
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            cloud_db = SessionLocal()
            
            try:
                # Clear existing data (optional - comment out for append mode)
                logger.info("🗑️  Clearing existing data...")
                cloud_db.query(Notification).delete()
                cloud_db.query(Alert).delete()
                cloud_db.query(VehicleListing).delete()
                cloud_db.query(User).delete()
                cloud_db.commit()
                
                # Restore users
                logger.info("👥 Restoring users...")
                for user_data in backup_data.get('users', []):
                    # Convert datetime strings back to datetime objects
                    if 'created_at' in user_data and isinstance(user_data['created_at'], str):
                        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                    if 'updated_at' in user_data and isinstance(user_data['updated_at'], str):
                        user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
                    
                    user = User(**user_data)
                    cloud_db.add(user)
                
                cloud_db.commit()
                logger.info(f"✅ Restored {len(backup_data.get('users', []))} users")
                
                # Restore vehicles
                logger.info("🚗 Restoring vehicles...")
                for vehicle_data in backup_data.get('vehicles', []):
                    # Convert datetime strings
                    if 'scraped_at' in vehicle_data and isinstance(vehicle_data['scraped_at'], str):
                        vehicle_data['scraped_at'] = datetime.fromisoformat(vehicle_data['scraped_at'])
                    if 'updated_at' in vehicle_data and isinstance(vehicle_data['updated_at'], str):
                        vehicle_data['updated_at'] = datetime.fromisoformat(vehicle_data['updated_at'])
                    
                    vehicle = VehicleListing(**vehicle_data)
                    cloud_db.add(vehicle)
                
                cloud_db.commit()
                logger.info(f"✅ Restored {len(backup_data.get('vehicles', []))} vehicles")
                
                # Restore alerts
                logger.info("🔔 Restoring alerts...")
                for alert_data in backup_data.get('alerts', []):
                    # Convert datetime strings
                    if 'created_at' in alert_data and isinstance(alert_data['created_at'], str):
                        alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
                    if 'updated_at' in alert_data and isinstance(alert_data['updated_at'], str):
                        alert_data['updated_at'] = datetime.fromisoformat(alert_data['updated_at'])
                    if 'last_triggered' in alert_data and isinstance(alert_data['last_triggered'], str):
                        alert_data['last_triggered'] = datetime.fromisoformat(alert_data['last_triggered'])
                    
                    alert = Alert(**alert_data)
                    cloud_db.add(alert)
                
                cloud_db.commit()
                logger.info(f"✅ Restored {len(backup_data.get('alerts', []))} alerts")
                
                # Restore notifications
                logger.info("📧 Restoring notifications...")
                for notification_data in backup_data.get('notifications', []):
                    # Convert datetime strings
                    if 'created_at' in notification_data and isinstance(notification_data['created_at'], str):
                        notification_data['created_at'] = datetime.fromisoformat(notification_data['created_at'])
                    if 'sent_at' in notification_data and isinstance(notification_data['sent_at'], str):
                        notification_data['sent_at'] = datetime.fromisoformat(notification_data['sent_at'])
                    
                    notification = Notification(**notification_data)
                    cloud_db.add(notification)
                
                cloud_db.commit()
                logger.info(f"✅ Restored {len(backup_data.get('notifications', []))} notifications")
                
                logger.info("✅ Database restore completed successfully")
                return True
                
            finally:
                cloud_db.close()
                
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        try:
            from app.models.cloud_base import SessionLocal
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            cloud_db = SessionLocal()
            
            try:
                stats = {
                    'users': cloud_db.query(User).count(),
                    'vehicles': cloud_db.query(VehicleListing).count(),
                    'alerts': cloud_db.query(Alert).count(),
                    'notifications': cloud_db.query(Notification).count(),
                    'timestamp': datetime.now().isoformat()
                }
                
                return stats
                
            finally:
                cloud_db.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}

def main():
    """Main backup utility function"""
    if len(sys.argv) < 2:
        print("🌐 Vehicle Scout - Cloud Database Backup Utility")
        print("=" * 50)
        print("Usage:")
        print("  python cloud_db_backup.py backup          # Create backup")
        print("  python cloud_db_backup.py list            # List backups")
        print("  python cloud_db_backup.py restore <file>  # Restore backup")
        print("  python cloud_db_backup.py stats           # Show database stats")
        sys.exit(1)
    
    backup_manager = CloudDatabaseBackup()
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_file = backup_manager.create_backup()
        if backup_file:
            print(f"✅ Backup created: {backup_file}")
        else:
            print("❌ Backup failed")
            sys.exit(1)
    
    elif command == "list":
        backups = backup_manager.list_backups()
        if backups:
            print("📋 Available backups:")
            for backup in backups:
                print(f"  - {backup}")
        else:
            print("📋 No backups found")
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Please specify backup file to restore")
            sys.exit(1)
        
        backup_file = sys.argv[2]
        if backup_manager.restore_backup(backup_file):
            print(f"✅ Restore completed: {backup_file}")
        else:
            print("❌ Restore failed")
            sys.exit(1)
    
    elif command == "stats":
        stats = backup_manager.get_database_stats()
        if stats:
            print("📊 Database Statistics:")
            for key, value in stats.items():
                if key != 'timestamp':
                    print(f"  {key.capitalize()}: {value}")
            print(f"  Last updated: {stats.get('timestamp', 'unknown')}")
        else:
            print("❌ Failed to get database stats")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
