#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Debug script for LinkedIn automation with job matching functionality
"""

import sys
import os
import time
import signal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences


class MockUserPreferences:
    """Mock user preferences for testing job matching"""
    
    def __init__(self):
        self.preferred_job_titles = ['Software Engineer', 'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 'Web Developer']
        self.preferred_locations = ['Mumbai', 'India', 'Remote', 'Maharashtra']
        self.required_skills = ['Python', 'JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'SQL', 'Java']
        self.preferred_skills = ['Django', 'Flask', 'MongoDB', 'PostgreSQL', 'AWS', 'Docker']
    
    def get_preferred_job_titles(self):
        return self.preferred_job_titles
    
    def get_preferred_locations(self):
        return self.preferred_locations
    
    def get_required_skills(self):
        return self.required_skills
    
    def get_preferred_skills(self):
        return self.preferred_skills


def cleanup_handler(signum, frame):
    """Handle cleanup on interrupt"""
    print("\n🛑 Interrupt received, cleaning up...")
    sys.exit(0)


def main():
    print("🔍 LinkedIn Automation with Job Matching Test")
    print("=" * 50)
    print("This will test the job matching functionality.")
    print("Watch the browser window to see what happens.\n")

    # Set up signal handler for graceful cleanup
    signal.signal(signal.SIGINT, cleanup_handler)

    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get test user from database
            test_user = User.query.filter_by(username='TestUser2').first()
            if not test_user:
                print("❌ Test user 'TestUser2' not found in database!")
                print("Please create a test user first.")
                return

            print(f"✅ Found user: {test_user.username} (ID: {test_user.id})")

            # Get LinkedIn credentials
            linkedin_username = test_user.linkedin_username
            linkedin_password = test_user.get_platform_password('linkedin')

            if not linkedin_username or not linkedin_password:
                print("❌ LinkedIn credentials not found!")
                return

            print("✅ LinkedIn credentials verified\n")

            # Get user's primary resume
            from app.models.job_preferences import Resume
            primary_resume = Resume.query.filter_by(user_id=test_user.id, is_primary=True, is_active=True).first()
            resume_path = None
            if primary_resume and primary_resume.file_path:
                import os
                resume_path = os.path.abspath(primary_resume.file_path)
                if os.path.exists(resume_path):
                    print(f"✅ Found primary resume: {primary_resume.original_filename}")
                else:
                    print(f"⚠️ Resume file not found at: {resume_path}")
                    resume_path = None
            else:
                print("⚠️ No primary resume found in database")

            # Prepare user data for auto-fill
            user_data = {
                'phone': test_user.phone,
                'email': test_user.email,
                'first_name': test_user.full_name.split()[0] if test_user.full_name else '',
                'last_name': ' '.join(test_user.full_name.split()[1:]) if test_user.full_name and len(test_user.full_name.split()) > 1 else '',
                'resume_path': resume_path
            }

            print(f"📋 User Data for Auto-fill:")
            print(f"   Phone: {user_data['phone'] or 'Not set'}")
            print(f"   Email: {user_data['email'] or 'Not set'}")
            print(f"   Name: {user_data['first_name']} {user_data['last_name']}")
            print(f"   Resume: {'Available' if user_data['resume_path'] else 'Not available'}")
            print()

            # Create mock user preferences
            user_preferences = MockUserPreferences()
            user_skills = user_preferences  # Same object for simplicity

            print("📋 User Preferences:")
            print(f"   Job Titles: {', '.join(user_preferences.get_preferred_job_titles())}")
            print(f"   Locations: {', '.join(user_preferences.get_preferred_locations())}")
            print(f"   Required Skills: {', '.join(user_preferences.get_required_skills())}")
            print()

            # Initialize LinkedIn automation
            print("🚀 Setting up ChromeDriver...")
            linkedin_bot = LinkedInAutomation(
                username=linkedin_username,
                password=linkedin_password,
                headless=False  # Keep browser visible for debugging
            )

            if not linkedin_bot.driver:
                print("❌ Failed to initialize ChromeDriver")
                return

            print("✅ ChromeDriver setup successful\n")

            # Login to LinkedIn
            print("🔐 Attempting LinkedIn login...")
            if not linkedin_bot.login():
                print("❌ LinkedIn login failed")
                linkedin_bot.quit()
                return

            print("✅ LinkedIn login successful!")
            print("⏳ Proceeding with job search in 3 seconds...\n")
            time.sleep(3)

            # Search for jobs
            print("🔍 Searching for jobs: 'Software Engineer' in 'Mumbai'...")
            job_cards = linkedin_bot.search_jobs(
                keywords="Software Engineer",
                location="Mumbai",
                filters={'easy_apply': True}
            )

            if not job_cards:
                print("❌ No jobs found")
                linkedin_bot.quit()
                return

            print(f"✅ Found {len(job_cards)} job listings\n")

            # Test job details extraction on first 3 jobs
            print("📄 Testing job matching on first 5 jobs...\n")

            for i, job_card in enumerate(job_cards[:5], 1):
                print(f"--- Job {i} ---")
                try:
                    # Extract job details
                    job_details = linkedin_bot.extract_job_details(job_card)
                    if job_details:
                        print(f"  ✅ Title: {job_details['job_title']}")
                        print(f"  ✅ Company: {job_details['company_name']}")
                        print(f"  ✅ Location: {job_details['location']}")
                        
                        # Test job matching
                        match_result = linkedin_bot._match_job_to_preferences(
                            job_details, user_preferences, user_skills
                        )
                        
                        if match_result:
                            print(f"  ✅ Job MATCHES user preferences!")
                        else:
                            print(f"  ❌ Job does NOT match user preferences")
                    else:
                        print(f"  ❌ Could not extract job details")

                except Exception as e:
                    print(f"  ❌ Error processing job: {str(e)}")

                print()
                time.sleep(2)  # Brief pause between jobs

            # Test application process on matching jobs
            print("🎯 Testing application process on matching jobs (up to 3)...\n")
            
            applications_attempted = 0
            successful_applications = 0
            max_applications = 3

            for i, job_card in enumerate(job_cards):
                if applications_attempted >= max_applications:
                    break
                
                print(f"=== Attempting Job {applications_attempted + 1}/{max_applications} ===")
                
                try:
                    # Try to apply to the job with user data for auto-fill
                    result = linkedin_bot.apply_to_job(job_card, user_preferences, user_skills, user_data)
                    applications_attempted += 1
                    
                    if result['success']:
                        successful_applications += 1
                        job_details = result['job_details']
                        print(f"✅ Successfully applied to: {job_details['job_title']}")
                        print(f"   Company: {job_details['company_name']}")
                        print(f"   Location: {job_details['location']}")
                    else:
                        print(f"❌ Application failed: {result['error']}")
                        
                        # If job doesn't match preferences, continue to next job
                        if "does not match" in result['error']:
                            print("🔄 Job doesn't match preferences, trying next job...")
                            continue
                        
                        # For other errors, we might want to continue or stop
                        print("🔄 Moving to next job...")
                
                except Exception as e:
                    print(f"❌ Unexpected error: {str(e)}")
                    applications_attempted += 1
                
                print()
                time.sleep(5)  # Pause between applications

            # Summary
            print("📊 Application Summary:")
            print(f"   Jobs attempted: {applications_attempted}")
            print(f"   Successful applications: {successful_applications}")
            if applications_attempted > 0:
                success_rate = (successful_applications / applications_attempted) * 100
                print(f"   Success rate: {success_rate:.1f}%")
            print()

            # Keep browser open for observation
            print("⏳ Keeping browser open for 30 seconds for observation...")
            time.sleep(30)

            # Cleanup
            linkedin_bot.quit()
            print("✅ Cleanup completed")

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
