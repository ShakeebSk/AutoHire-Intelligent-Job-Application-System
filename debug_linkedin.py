#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Debug script specifically for LinkedIn automation issues
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_linkedin_search():
    """Test LinkedIn search specifically"""
    app = create_app()
    with app.app_context():
        # Get TestUser2
        user = User.query.filter_by(username='TestUser2').first()
        if not user:
            print("❌ TestUser2 not found!")
            return
            
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # Get credentials
        linkedin_password = user.get_platform_password('linkedin')
        if not linkedin_password:
            print("❌ LinkedIn password could not be decrypted")
            return
            
        print("✅ LinkedIn credentials verified")
        
        # Get Gemini API key for AI functionality
        gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if gemini_api_key:
            print("🤖 AI Question Answering: ENABLED")
        else:
            print("⚠️ AI Question Answering: DISABLED (no API key)")
        
        # Create LinkedIn bot with AI capabilities
        linkedin_bot = LinkedInAutomation(
            user.linkedin_username,
            linkedin_password,
            headless=False,  # Make it visible for debugging
            gemini_api_key=gemini_api_key  # Enable AI if API key available
        )
        
        try:
            print("\n🚀 Setting up ChromeDriver...")
            linkedin_bot.setup_driver()
            print("✅ ChromeDriver setup successful")
            
            print("\n🔐 Attempting LinkedIn login...")
            login_success = linkedin_bot.login()
            
            if login_success:
                print("✅ LinkedIn login successful!")
                print("🔍 Continuing with automated job search...")
                import time
                time.sleep(2)  # Brief pause instead of user input
                
                print("\n🔍 Searching for jobs...")
                jobs = linkedin_bot.search_jobs("Software Engineer", "Mumbai")
                
                print(f"✅ Found {len(jobs)} job listings")
                
                # Get user preferences for job matching
                user_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
                if not user_preferences:
                    print("⚠️ No job preferences found - will use default matching")
                
                # Prepare user data for applications
                user_data = {
                    'first_name': (user.full_name or 'Test').split()[0],
                    'last_name': ' '.join((user.full_name or 'User').split()[1:]),
                    'full_name': user.full_name or 'Test User',
                    'email': user.email,
                    'phone': user.phone,
                    'location': user.location or 'Mumbai',
                    'resume_path': None,  # Add resume path if available
                    'experience_years': user.experience_years or 3,
                    'current_salary': user.current_salary,
                    'expected_salary': user.expected_salary,
                    'skills': ['Python', 'JavaScript', 'React', 'SQL', 'Flask'],
                    'education': user.education or 'Bachelor\'s in Computer Science',
                    'achievements': user.achievements or 'AutoHire project development'
                }
                
                user_skills = user_data['skills']
                
                if jobs:
                    print("\n🎯 TESTING COMPLETE AUTOMATION WORKFLOW")
                    print("=" * 50)
                    print("This will test the FULL process:")
                    print("1. Job search ✅")
                    print("2. Job matching against preferences")
                    print("3. Easy Apply detection and clicking")
                    print("4. Form filling with AI assistance")
                    print("5. Application submission")
                    print("6. Moving to next job automatically")
                    print()
                    
                    choice = input("Test complete automation workflow? (y/n): ")
                    if choice.lower() == 'y':
                        print("\n🚀 STARTING COMPLETE AUTOMATION TEST...")
                        print("This will process jobs sequentially and apply automatically!")
                        print()
                        
                        # This is the MAIN TEST - testing our fixed workflow
                        result = linkedin_bot.process_jobs_sequentially(
                            user_preferences=user_preferences,
                            user_skills=user_skills,
                            user_data=user_data,
                            max_applications=2  # Test with 2 applications for safety
                        )
                        
                        print("\n📊 AUTOMATION TEST RESULTS:")
                        print("=" * 30)
                        if result['success']:
                            print(f"✅ SUCCESS: {result['applications_made']} applications completed")
                            print("The complete workflow is working!")
                        else:
                            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                    else:
                        print("\n📄 Testing basic job details extraction...")
                        for i, job in enumerate(jobs[:3]):  # Test first 3 jobs
                            print(f"\nJob {i+1}:")
                            job_details = linkedin_bot.extract_job_details(job)
                            if job_details:
                                print(f"  Title: {job_details.get('job_title', 'N/A')}")
                                print(f"  Company: {job_details.get('company_name', 'N/A')}")
                                print(f"  Location: {job_details.get('location', 'N/A')}")
                                print(f"  Job ID: {job_details.get('platform_job_id', 'N/A')}")
                            else:
                                print("  ❌ Could not extract job details")
                
                # Test AI form filling if enabled
                if linkedin_bot.ai_answerer:
                    print("\n🤖 AI FORM FILLING TEST")
                    print("-" * 30)
                    print("Instructions:")
                    print("1. Navigate to a LinkedIn job and click 'Easy Apply'")
                    print("2. When you see a form with questions, come back here")
                    print("3. Press Enter to test AI form filling")
                    print()
                    
                    input("Press Enter when you're ready to test AI form filling...")
                    
                    # Prepare user data for AI
                    user_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
                    
                    user_data = {
                        'full_name': user.full_name or 'Test User',
                        'email': user.email,
                        'phone': user.phone,
                        'city': user.location or 'Mumbai',  # Use location instead of city
                        'experience_years': user.experience_years or 3,
                        'current_role': 'Software Developer',
                        'education': user.education or 'Bachelor\'s in Computer Science',
                        'skills': ['Python', 'JavaScript', 'React', 'SQL'],
                        'work_authorization': 'Yes',
                        'willing_to_relocate': 'Yes',
                        'availability': 'Immediately'
                    }
                    
                    print("🚀 Testing AI form filling on current page...")
                    success = linkedin_bot._ai_fill_application_form(user_data)
                    
                    if success:
                        print("✅ AI form filling test completed!")
                        print("Check the browser to see the filled form.")
                    else:
                        print("⚠️ AI form filling test encountered issues.")
                        print("This might be normal if there are no forms on the current page.")
                else:
                    print("\n⚠️ AI form filling not available (no API key provided)")
                
                # Wait before closing
                input("\nPress Enter to close browser...")
                
            else:
                print("❌ LinkedIn login failed")
                input("Press Enter to close browser...")
                
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()
            input("Press Enter to close browser...")
            
        finally:
            # Cleanup
            try:
                linkedin_bot.cleanup()
                print("✅ Cleanup completed")
            except:
                pass

if __name__ == "__main__":
    print("🔍 Debug LinkedIn COMPLETE Automation Workflow")
    print("=" * 50)
    print("This debug script will:")
    print("• Open a visible Chrome browser window")
    print("• Test LinkedIn login and job search")
    print("• Test COMPLETE automation workflow:")
    print("  - Sequential job processing")
    print("  - Job preference matching")
    print("  - Easy Apply detection and clicking")
    print("  - AI-powered form filling")
    print("  - Application submission")
    print("  - Automatic progression to next job")
    print("• Show detailed progress logs")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        test_linkedin_search()
    else:
        print("Debug cancelled.")
