#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Auto-running debug script for LinkedIn automation
"""

import sys
import os

from app.automation import automation_manager
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_linkedin_automation():
    """Test full LinkedIn automation flow"""
    app = create_app()
    with app.app_context():
        # Get TestUser3
        user = User.query.filter_by(username='TestUser3').first()
        if not user:
            print("❌ TestUser3 not found!")
            return
        print(f"🧑‍💼 Testing with user: {user.username}")
            
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # Get job preferences
        job_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
        if not job_preferences:
            print("⚠️ No job preferences found for user")
            return
        
        print(f"📋 Job Preferences:")
        print(f"   Preferred Titles: {job_preferences.get_preferred_job_titles()[:3]}...")
        print(f"   Preferred Locations: {job_preferences.get_preferred_locations()[:3]}...")
        print(f"   Required Skills: {job_preferences.get_required_skills()[:5]}...")
        
        # Get credentials
        linkedin_password = user.get_platform_password('linkedin')
        if not linkedin_password:
            print("❌ LinkedIn password could not be decrypted")
            return
            
        print("✅ LinkedIn credentials verified")
        
        # Create LinkedIn bot with visible browser
        linkedin_bot = LinkedInAutomation(
            user.linkedin_username,
            linkedin_password,
            headless=False  # Keep visible for debugging
        )
        
        try:
            print("\n🚀 Setting up ChromeDriver...")
            linkedin_bot.setup_driver()
            print("✅ ChromeDriver setup successful")
            
            print("\n🔐 Attempting LinkedIn login...")
            login_success = linkedin_bot.login()
            
            if login_success:
                print("✅ LinkedIn login successful!")
                
                # Auto-proceed after 3 seconds
                print("⏳ Proceeding with job search in 3 seconds...")
                time.sleep(3)
                
                print("\n🔍 Searching for jobs: 'Software Engineer' in 'Mumbai'...")
                jobs = linkedin_bot.search_jobs("Software Engineer")
                
                print(f"✅ Found {len(jobs)} job listings")
                
                if jobs:
                    print("\n📄 Testing job details extraction on first 3 jobs...")
                    for i, job in enumerate(jobs[:3]):
                        print(f"\n--- Job {i+1} ---")
                        try:
                            job_details = linkedin_bot.extract_job_details(job)
                            if job_details:
                                print(f"  ✅ Title: {job_details.get('job_title', 'N/A')}")
                                print(f"  ✅ Company: {job_details.get('company_name', 'N/A')}")
                                print(f"  ✅ Location: {job_details.get('location', 'N/A')}")
                                print(f"  ✅ Job ID: {job_details.get('platform_job_id', 'N/A')}")
                                print(f"  ✅ URL: {job_details.get('job_url', 'N/A')}")
                            else:
                                print("  ❌ Could not extract job details")
                        except Exception as e:
                            print(f"  ❌ Error extracting job details: {str(e)}")
                    
                    # Test application to multiple jobs (move to next if current fails)
                    max_application_attempts = min(5, len(jobs))  # Try up to 5 jobs
                    applications_attempted = 0
                    successful_applications = 0
                    
                    print(f"\n🎯 Testing application process on up to {max_application_attempts} jobs...")
                    print("Will move to next job if current application fails.\n")
                    
                    # Use sequential processing instead of manual iteration
                    print(f"🔄 Starting sequential job processing...")
                    user_skills = job_preferences.get_required_skills() if job_preferences else []
                    user_data = {
                        'first_name': user.full_name.split()[0] if user.full_name else '',
                        'last_name': ' '.join(user.full_name.split()[1:]) if user.full_name and len(user.full_name.split()) > 1 else '',
                        'email': user.email,
                        'phone': user.phone,
                        'skills': user_skills,
                        'resume_path': os.path.join(os.getcwd(), 'data', 'resumes', 'test_resume.pdf')
                    }
                    
                    # Reset job index for sequential processing
                    linkedin_bot.current_job_index = 0
                    
                    # Process jobs sequentially
                    result = linkedin_bot.process_jobs_sequentially(
                        user_preferences=job_preferences,
                        user_skills=user_skills,
                        user_data=user_data,
                        max_applications=max_application_attempts
                    )
                    
                    applications_attempted = max_application_attempts
                    successful_applications = result.get('applications_made', 0)
                    
                    print(f"\n📊 Application Summary:")
                    print(f"   Jobs attempted: {applications_attempted}")
                    print(f"   Successful applications: {successful_applications}")
                    print(f"   Success rate: {(successful_applications/applications_attempted)*100:.1f}%")
                else:
                    print("❌ No jobs found to test application process")
                
                # Keep browser open for 30 seconds to observe
                print(f"\n⏳ Keeping browser open for 30 seconds for observation...")
                time.sleep(30)
                
            else:
                print("❌ LinkedIn login failed")
                
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            try:
                linkedin_bot.cleanup()
                print("✅ Cleanup completed")
            except:
                pass

if __name__ == "__main__":
    print("🔍 Auto LinkedIn Automation Test")
    print("=" * 50)
    print("This will automatically run through the entire process.")
    print("Watch the browser window to see what happens.")
    print()
    
    test_linkedin_automation()
    print("\n✅ Test completed!")
