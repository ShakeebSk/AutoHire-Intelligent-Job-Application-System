#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Test Script for Fixed AutoHire LinkedIn Automation

This script demonstrates the complete workflow:
1. Login to LinkedIn
2. Search for jobs with Easy Apply filter
3. Process jobs sequentially with AI assistance
4. Apply to matching jobs automatically
5. Track and save application results
"""

import os
import sys
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.append('app')

from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.automation_manager import AutomationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('automation_test.log')
    ]
)

def test_linkedin_automation():
    """
    Test the complete LinkedIn automation workflow
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("🚀 TESTING FIXED LINKEDIN AUTOMATION")
    print("="*80)
    
    # Example credentials (replace with your actual credentials)
    LINKEDIN_USERNAME = "your_linkedin_username@email.com"
    LINKEDIN_PASSWORD = "your_linkedin_password"
    GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')  # Set this in your environment
    
    # Example user data (replace with actual user data)
    user_data = {
        'first_name': 'Sayyed',
        'last_name': 'Affan',
        'full_name': 'Sayyed Affan',
        'email': 'sayyed.affan@email.com',
        'phone': '+1234567890',
        'location': 'Mumbai, India',
        'resume_path': 'C:\\path\\to\\your\\resume.pdf',  # Update with actual resume path
        'experience_years': 2,
        'current_salary': '500000',
        'expected_salary': '800000',
        'skills': ['Python', 'Flask', 'JavaScript', 'React', 'SQL'],
        'education': 'Bachelor of Computer Science',
        'achievements': 'Final year project on AutoHire system'
    }
    
    # Mock job preferences (in real app, this comes from database)
    class MockJobPreferences:
        def get_preferred_job_titles(self):
            return ['Software Developer', 'Full Stack Developer', 'Python Developer']
        
        def get_preferred_locations(self):
            return ['Mumbai', 'Remote', 'Hybrid']
        
        def get_required_skills(self):
            return ['Python', 'Flask', 'JavaScript']
    
    try:
        # Step 1: Initialize LinkedIn automation
        print("\n📱 Step 1: Initializing LinkedIn automation...")
        linkedin_bot = LinkedInAutomation(
            username=LINKEDIN_USERNAME,
            password=LINKEDIN_PASSWORD,
            headless=False,  # Set to False to see the browser in action
            gemini_api_key=GEMINI_API_KEY
        )
        
        # Step 2: Login to LinkedIn
        print("\n🔐 Step 2: Logging into LinkedIn...")
        login_success = linkedin_bot.login()
        if not login_success:
            print(" Login failed. Please check credentials.")
            return
        
        print(" Login successful!")
        
        # Step 3: Search for jobs
        print("\n🔍 Step 3: Searching for jobs...")
        job_cards = linkedin_bot.search_jobs(
            keywords="Python Developer",
            location="Mumbai",
            filters={'easy_apply': True}
        )
        
        if not job_cards:
            print(" No jobs found")
            return
        
        print(f" Found {len(job_cards)} jobs with Easy Apply")
        
        # Step 4: Process jobs sequentially with AI assistance
        print("\n Step 4: Processing jobs with AI assistance...")
        
        mock_preferences = MockJobPreferences()
        user_skills = user_data['skills']
        
        # This is the MAIN METHOD that handles the complete workflow
        result = linkedin_bot.process_jobs_sequentially(
            user_preferences=mock_preferences,
            user_skills=user_skills,
            user_data=user_data,
            max_applications=3  # Start with 3 applications for testing
        )
        
        # Step 5: Display results
        print("\n📊 AUTOMATION RESULTS:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Applications Made: {result['applications_made']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\n Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f" Test failed: {str(e)}")
    
    finally:
        # Cleanup
        try:
            linkedin_bot.quit()
            print("\n🧹 Browser closed and cleanup completed")
        except:
            pass

def test_automation_manager():
    """
    Test the AutomationManager with database integration
    """
    print("\n" + "="*80)
    print("🚀 TESTING AUTOMATION MANAGER (WITH DATABASE)")
    print("="*80)
    
    try:
        # This would work if you have a user in the database
        # For testing purposes, you'd need to:
        # 1. Create a user account through the web interface
        # 2. Set up job preferences
        # 3. Upload a resume
        # 4. Get the user ID and use it here
        
        # Example:
        # user_id = 1  # Replace with actual user ID
        # automation_manager = AutomationManager(user_id)
        # result = automation_manager.run_full_automation()
        
        print("📝 To test AutomationManager:")
        print("1. Register a user through the web interface")
        print("2. Set up job preferences and upload resume")
        print("3. Update this script with the user ID")
        print("4. Run automation_manager.run_full_automation()")
        
    except Exception as e:
        print(f" AutomationManager test setup: {str(e)}")

if __name__ == "__main__":
    print("🎯 AutoHire LinkedIn Automation Test")
    print("Choose test option:")
    print("1. Test LinkedIn automation directly")
    print("2. Test Automation Manager (requires database setup)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        print("\n⚠️ IMPORTANT: Update the credentials in the script before running!")
        print("- LinkedIn username and password")
        print("- Google Gemini API key (set GOOGLE_GEMINI_API_KEY environment variable)")
        print("- Resume file path")
        print("- User details")
        
        confirm = input("\nHave you updated the credentials? (y/n): ")
        if confirm.lower() == 'y':
            test_linkedin_automation()
        else:
            print("Please update credentials and run again.")
    
    elif choice == "2":
        test_automation_manager()
    
    else:
        print("Invalid choice")
