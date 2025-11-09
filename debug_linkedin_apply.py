#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Debug script for LinkedIn automation that tests the full application process
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences, Resume
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_linkedin_application():
    """Test LinkedIn job application with auto-fill"""
    app = create_app()
    with app.app_context():
        # Get TestUser2
        user = User.query.filter_by(username='TestUser3').first()
        if not user:
            print("❌ TestUser3 not found!")
            return
            
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # Get user preferences
        user_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
        user_skills = []  # For now, we'll use an empty list for skills
        
        if not user_preferences:
            print("❌ User preferences not found!")
            return
        
        print(f"✅ User preferences loaded")
        print(f"   - Preferred job titles: {user_preferences.get_preferred_job_titles()}")
        print(f"   - Preferred locations: {user_preferences.get_preferred_locations()}")
        print(f"   - Required skills: {user_preferences.get_required_skills()}")
        
        # Prepare user data for auto-fill
        user_data = {
            'email': user.email,
            'phone': user.phone,
            'full_name': user.full_name or 'Test User',
            'first_name': user.full_name.split()[0] if user.full_name else 'Test',
            'last_name': ' '.join(user.full_name.split()[1:]) if user.full_name and len(user.full_name.split()) > 1 else 'User',
            'city':user.city,
            'resume_path': None  # We'll set this if user has a primary resume
        }
        
        # Check if user has a primary resume
        if hasattr(user, 'resumes') and user.resumes:
            primary_resume = next((r for r in user.resumes if r.is_primary), None)
            if primary_resume and os.path.exists(primary_resume.file_path):
                user_data['resume_path'] = primary_resume.file_path
                print(f"✅ Primary resume found: {primary_resume.file_path}")
            else:
                print("⚠️ No primary resume found or file doesn't exist")
        else:
            print("⚠️ No resumes found for user")
        
        print(f"✅ User data prepared for auto-fill:")
        print(f"   - Email: {user_data['email']}")
        print(f"   - Phone: {user_data['phone']}")
        print(f"   - Full name: {user_data['full_name']}")
        print(f"   - Resume available: {'Yes' if user_data['resume_path'] else 'No'}")
        
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
            headless=False  # Make it visible for debugging
        )
        
        try:
            print("\n🚀 Setting up ChromeDriver...")
            linkedin_bot.setup_driver()
            print("✅ ChromeDriver setup successful")
            
            print("\n🔐 Attempting LinkedIn login...")
            login_success = linkedin_bot.login()
            
            if login_success:
                print("✅ LinkedIn login successful!")
                print("🔍 Continuing with automated job search and application...")
                time.sleep(2)
                
                print("\n🔍 Searching for jobs...")
                # Use user preferences for search
                job_titles = user_preferences.get_preferred_job_titles()
                locations = user_preferences.get_preferred_locations()
                
                search_title = job_titles[0] if job_titles else "Web Developer"
                search_location = locations[0] if locations else "Mumbai"
                
                print(f"   - Searching for: {search_title}")
                print(f"   - Location: {search_location}")
                
                jobs = linkedin_bot.search_jobs(search_title, search_location)
                print(f"✅ Found {len(jobs)} job listings")
                
                if jobs:
                    print(f"\n🎯 Attempting to apply to up to 3 matching jobs...")
                    applications_attempted = 0
                    successful_applications = 0
                    
                    for i, job in enumerate(jobs[:10]):  # Try first 10 jobs to find matches
                        if applications_attempted >= 3:
                            break
                            
                        print(f"\n--- Job {i+1}/{min(len(jobs), 10)} ---")
                        
                        try:
                            # Apply to job with user data for auto-fill
                            result = linkedin_bot.apply_to_job(
                                job, 
                                user_preferences, 
                                user_skills,
                                user_data=user_data
                            )
                            
                            if result['success']:
                                applications_attempted += 1
                                successful_applications += 1
                                job_details = result.get('job_details', {})
                                print(f"✅ SUCCESSFULLY APPLIED!")
                                print(f"   - Job: {job_details.get('job_title', 'N/A')}")
                                print(f"   - Company: {job_details.get('company_name', 'N/A')}")
                                print(f"   - Location: {job_details.get('location', 'N/A')}")
                                print(f"   - Method: {result.get('application_method', 'N/A')}")
                                
                                # Add delay between successful applications
                                time.sleep(5)
                                
                            else:
                                error = result.get('error', 'Unknown error')
                                job_details = result.get('job_details', {})
                                
                                if 'does not match user preferences' in error:
                                    print(f"⏭️ SKIPPED (doesn't match preferences)")
                                    print(f"   - Job: {job_details.get('job_title', 'N/A')}")
                                    print(f"   - Company: {job_details.get('company_name', 'N/A')}")
                                    print(f"   - Reason: {error}")
                                elif 'Already applied' in error:
                                    print(f"⏭️ SKIPPED (already applied)")
                                    print(f"   - Job: {job_details.get('job_title', 'N/A')}")
                                else:
                                    applications_attempted += 1
                                    print(f"❌ APPLICATION FAILED")
                                    print(f"   - Job: {job_details.get('job_title', 'N/A')}")
                                    print(f"   - Company: {job_details.get('company_name', 'N/A')}")
                                    print(f"   - Error: {error}")
                                    
                                    # Add delay between failed attempts
                                    time.sleep(3)
                                    
                        except Exception as e:
                            applications_attempted += 1
                            print(f"❌ EXCEPTION during application: {str(e)}")
                            time.sleep(3)
                    
                    print(f"\n📊 SUMMARY:")
                    print(f"   - Jobs found: {len(jobs)}")
                    print(f"   - Applications attempted: {applications_attempted}")
                    print(f"   - Successful applications: {successful_applications}")
                    print(f"   - Success rate: {(successful_applications/applications_attempted*100):.1f}%" if applications_attempted > 0 else "   - Success rate: N/A")
                    
                else:
                    print("❌ No jobs found to apply to")
                
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
                applied_count = linkedin_bot.get_applied_jobs_count()
                print(f"✅ Total jobs applied to in this session: {applied_count}")
                linkedin_bot.cleanup()
                print("✅ Cleanup completed")
            except:
                pass

if __name__ == "__main__":
    print("🔍 LinkedIn Application Debug Tool")
    print("=" * 50)
    print("This will test the complete job application process:")
    print("• Login to LinkedIn")
    print("• Search for jobs based on user preferences")
    print("• Match jobs to user preferences")
    print("• Apply to matching jobs with auto-fill")
    print("• Show detailed success/failure information")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        test_linkedin_application()
    else:
        print("Debug cancelled.")
