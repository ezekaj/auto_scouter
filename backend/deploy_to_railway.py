#!/usr/bin/env python3
"""
Railway Cloud Deployment Script
Deploys Vehicle Scout to Railway for 24/7 operation
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RailwayDeployer:
    """Railway deployment manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_files = [
            "requirements.txt",
            "railway.json",
            "Procfile",
            "app/main_cloud.py"
        ]
    
    def check_prerequisites(self):
        """Check if all required files exist"""
        logger.info("🔍 Checking deployment prerequisites...")
        
        missing_files = []
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ Missing required files: {missing_files}")
            return False
        
        logger.info("✅ All required files present")
        return True
    
    def check_railway_cli(self):
        """Check if Railway CLI is installed"""
        try:
            result = subprocess.run(["railway", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Railway CLI found: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ Railway CLI not working properly")
                return False
        except FileNotFoundError:
            logger.error("❌ Railway CLI not found. Install it first:")
            logger.error("   npm install -g @railway/cli")
            logger.error("   or visit: https://railway.app/cli")
            return False
    
    def setup_environment_variables(self):
        """Setup environment variables for Railway deployment"""
        logger.info("🔧 Setting up environment variables...")
        
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "SCRAPING_INTERVAL_MINUTES": "5",
            "MAX_VEHICLES_PER_SCRAPE": "50",
            "LOG_LEVEL": "INFO",
            "SECRET_KEY": "your-production-secret-key-change-this",
            "ALLOWED_HOSTS": "*"
        }
        
        for key, value in env_vars.items():
            try:
                cmd = ["railway", "variables", "set", f"{key}={value}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✅ Set {key}")
                else:
                    logger.warning(f"⚠️  Failed to set {key}: {result.stderr}")
            except Exception as e:
                logger.error(f"❌ Error setting {key}: {e}")
        
        logger.info("🎯 Environment variables configured")
    
    def create_railway_project(self):
        """Create or connect to Railway project"""
        logger.info("🚀 Setting up Railway project...")
        
        try:
            # Check if already connected to a project
            result = subprocess.run(["railway", "status"], capture_output=True, text=True)
            if result.returncode == 0 and "Project:" in result.stdout:
                logger.info("✅ Already connected to Railway project")
                return True
            
            # Create new project
            logger.info("Creating new Railway project...")
            result = subprocess.run(["railway", "login"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Railway login failed")
                return False
            
            result = subprocess.run(["railway", "init"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Railway project created")
                return True
            else:
                logger.error(f"❌ Failed to create Railway project: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting up Railway project: {e}")
            return False
    
    def add_postgresql_service(self):
        """Add PostgreSQL database service"""
        logger.info("🗄️  Adding PostgreSQL database...")
        
        try:
            # Add PostgreSQL plugin
            result = subprocess.run(["railway", "add", "--database", "postgresql"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ PostgreSQL database added")
                return True
            else:
                logger.warning(f"⚠️  PostgreSQL add result: {result.stderr}")
                # Database might already exist
                return True
                
        except Exception as e:
            logger.error(f"❌ Error adding PostgreSQL: {e}")
            return False
    
    def add_redis_service(self):
        """Add Redis service for Celery"""
        logger.info("🔴 Adding Redis service...")
        
        try:
            # Add Redis plugin
            result = subprocess.run(["railway", "add", "--database", "redis"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Redis service added")
                return True
            else:
                logger.warning(f"⚠️  Redis add result: {result.stderr}")
                # Redis might already exist
                return True
                
        except Exception as e:
            logger.error(f"❌ Error adding Redis: {e}")
            return False
    
    def deploy_application(self):
        """Deploy the application to Railway"""
        logger.info("🚀 Deploying application to Railway...")
        
        try:
            # Deploy the application
            result = subprocess.run(["railway", "up"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Application deployed successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"❌ Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during deployment: {e}")
            return False
    
    def get_deployment_info(self):
        """Get deployment information"""
        logger.info("📋 Getting deployment information...")
        
        try:
            # Get project status
            result = subprocess.run(["railway", "status"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("📊 Deployment Status:")
                logger.info(result.stdout)
            
            # Get domain
            result = subprocess.run(["railway", "domain"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("🌐 Domain Information:")
                logger.info(result.stdout)
                
        except Exception as e:
            logger.error(f"❌ Error getting deployment info: {e}")
    
    def run_deployment(self):
        """Run the complete deployment process"""
        logger.info("🚀 Starting Railway deployment process...")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Railway CLI", self.check_railway_cli),
            ("Railway Project", self.create_railway_project),
            ("PostgreSQL Database", self.add_postgresql_service),
            ("Redis Service", self.add_redis_service),
            ("Environment Variables", self.setup_environment_variables),
            ("Application Deployment", self.deploy_application),
            ("Deployment Info", self.get_deployment_info)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"🔄 Step: {step_name}")
            logger.info(f"{'='*50}")
            
            if not step_func():
                logger.error(f"❌ Step '{step_name}' failed. Stopping deployment.")
                return False
        
        logger.info("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        logger.info("🌐 Your Vehicle Scout application is now running 24/7 in the cloud!")
        logger.info("📱 Update your mobile app to use the Railway domain instead of localhost")
        
        return True

def main():
    """Main deployment function"""
    print("🚀 Vehicle Scout - Railway Cloud Deployment")
    print("=" * 50)
    
    deployer = RailwayDeployer()
    
    if deployer.run_deployment():
        print("\n✅ SUCCESS: Vehicle Scout is now running 24/7 in the cloud!")
        print("🔗 Next steps:")
        print("   1. Update mobile app to use Railway domain")
        print("   2. Test the cloud deployment")
        print("   3. Monitor scraping and notifications")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Deployment encountered errors")
        print("🔧 Check the logs above and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
