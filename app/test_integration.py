#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Test script to verify AutoHire automation integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences, Resume
from app.automation.automation_manager import AutomationManager
import json

def test_integration():
    """Test the integration between user profile, job preferences, and automation"""
    
    app = create_app()
    with app.app_context():
        print("🔧 Testing AutoHire Integration...")
        print("=" * 50)
        
        # Find an existing user (should be the test user we have)
        # Use specific user ID if necessary
        user_id = 5  # Adjust this based on database checking results
        user = User.query.get(user_id)
        if not user:
            print(" No user found in database")
            return False
            
        print(f" Found user: {user.username} (ID: {user.id})")
        
        # Check user profile
        print(f"📋 User Profile:")
        print(f"   - Full Name: {user.full_name}")
        print(f"   - Email: {user.email}")
        print(f"   - Phone: {user.phone}")
        print(f"   - Location: {user.location}")
        print(f"   - Skills: {user.skills}")
        print(f"   - Daily Limit: {user.daily_application_limit}")
        
        # Check platform credentials
        print(f"🔑 Platform Credentials:")
        print(f"   - LinkedIn: {user.linkedin_username} ({'' if user.linkedin_password else ''})")
        print(f"   - Indeed: {user.indeed_username} ({'' if user.indeed_password else ''})")
        
        # Check job preferences
        preferences = JobPreferences.query.filter_by(user_id=user.id).first()
        if preferences:
            print(f"⚙️ Job Preferences:")
            print(f"   - Job Titles: {preferences.get_preferred_job_titles()}")
            print(f"   - Locations: {preferences.get_preferred_locations()}")
            print(f"   - Work Type: {preferences.work_type}")
            print(f"   - Min Salary: {preferences.min_salary}")
            print(f"   - Max Salary: {preferences.max_salary}")
            print(f"   - Platform Priorities: LinkedIn={preferences.linkedin_priority}, Indeed={preferences.indeed_priority}")
        else:
            print(" No job preferences found")
            
        # Check resumes
        resumes = Resume.query.filter_by(user_id=user.id).all()
        print(f"📄 Resumes: {len(resumes)} found")
        for resume in resumes:
            print(f"   - {resume.resume_name} ({'Primary' if resume.is_primary else 'Secondary'})")
        
        # Test automation manager
        print("\n Testing Automation Manager...")
        try:
            automation_manager = AutomationManager(user.id)
            
            # Test search criteria
            search_criteria = automation_manager.get_user_search_criteria()
            print(f"   - Search Criteria: {'' if search_criteria else ''}")
            if search_criteria:
                print(f"     Job Titles: {search_criteria.get('job_titles', [])}")
                print(f"     Locations: {search_criteria.get('locations', [])}")
            
            # Test platform priorities
            priorities = automation_manager.get_platform_priorities()
            print(f"   - Platform Priorities: {priorities}")
            
            # Test daily limit check
            today_apps, daily_limit = automation_manager.check_daily_limit()
            print(f"   - Daily Limit: {today_apps}/{daily_limit}")
            
            # Test user skills
            user_skills = automation_manager._get_user_skills()
            print(f"   - User Skills: {user_skills}")
            
            # Test user application data
            user_data = automation_manager._get_user_application_data()
            print(f"   - Application Data:")
            print(f"     Name: {user_data.get('first_name')} {user_data.get('last_name')}")
            print(f"     Email: {user_data.get('email')}")
            print(f"     Phone: {user_data.get('phone')}")
            print(f"     Resume: {'' if user_data.get('resume_path') else ''}")
            
            print(" Automation Manager integration successful!")
            return True
            
        except Exception as e:
            print(f" Automation Manager error: {str(e)}")
            return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("The AutoHire system is properly integrated and ready to use.")
    else:
        print("\n Integration test failed!")
        print("Please check the setup and configuration.")
