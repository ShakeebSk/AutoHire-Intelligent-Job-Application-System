#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Debug script to test the automation flow and identify issues
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.automation_manager import AutomationManager
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_automation_setup():
    """Test automation setup for TestUser2"""
    app = create_app()
    with app.app_context():
        # Get TestUser2
        user = User.query.filter_by(username='TestUser2').first()
        if not user:
            print(" TestUser2 not found!")
            return
            
        print(f" Found user: {user.username} (ID: {user.id})")
        
        # Test automation manager initialization
        try:
            automation_manager = AutomationManager(user.id)
            print(" AutomationManager created successfully")
            
            # Check daily limit
            today_apps, daily_limit = automation_manager.check_daily_limit()
            print(f" Daily limit check: {today_apps}/{daily_limit} applications today")
            
            # Get search criteria
            search_criteria = automation_manager.get_user_search_criteria()
            if search_criteria:
                print(" Search criteria found:")
                print(f"   Job titles: {search_criteria['job_titles']}")
                print(f"   Locations: {search_criteria['locations']}")
                print(f"   Required skills: {search_criteria['required_skills']}")
            else:
                print(" No search criteria found")
                return
            
            # Get platform priorities
            priorities = automation_manager.get_platform_priorities()
            print(f" Platform priorities: {priorities}")
            
            # Test bot initialization
            print("\n🤖 Testing bot initialization...")
            try:
                automation_manager.initialize_bots()
                print(" Bots initialized successfully!")
                
                # Check which bots were created
                if automation_manager.linkedin_bot:
                    print(" LinkedIn bot created")
                else:
                    print(" LinkedIn bot not created")
                    
                if automation_manager.indeed_bot:
                    print(" Indeed bot created")
                else:
                    print(" Indeed bot not created")
                    
            except Exception as e:
                print(f" Bot initialization failed: {str(e)}")
                
            finally:
                # Cleanup
                try:
                    automation_manager.cleanup_bots()
                    print(" Cleanup completed")
                except:
                    pass
            
        except Exception as e:
            print(f" AutomationManager creation failed: {str(e)}")
            import traceback
            traceback.print_exc()

def test_user_credentials():
    """Test user credential decryption"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username='TestUser2').first()
        if not user:
            print(" TestUser2 not found!")
            return
            
        print(f"Testing credentials for {user.username}:")
        
        # Test LinkedIn credentials
        if user.linkedin_username and user.linkedin_password:
            try:
                decrypted_password = user.get_platform_password('linkedin')
                if decrypted_password:
                    print(f" LinkedIn credentials: {user.linkedin_username} / [password decrypted successfully]")
                else:
                    print(f" LinkedIn password decryption failed")
            except Exception as e:
                print(f" LinkedIn credential error: {str(e)}")
        else:
            print(" LinkedIn credentials not set")
            
        # Test Indeed credentials
        if user.indeed_username and user.indeed_password:
            try:
                decrypted_password = user.get_platform_password('indeed')
                if decrypted_password:
                    print(f" Indeed credentials: {user.indeed_username} / [password decrypted successfully]")
                else:
                    print(f" Indeed password decryption failed")
            except Exception as e:
                print(f" Indeed credential error: {str(e)}")
        else:
            print(" Indeed credentials not set")

if __name__ == "__main__":
    print("🔍 Debugging AutoHire Automation")
    print("=" * 50)
    
    print("\n1. Testing user credentials...")
    test_user_credentials()
    
    print("\n2. Testing automation setup...")
    test_automation_setup()
    
    print("\n Debug completed!")
