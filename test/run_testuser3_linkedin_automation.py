#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Real LinkedIn automation script for TestUser3
This script performs actual LinkedIn job applications using Selenium automation
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.job_preferences import JobPreferences
from app.automation.automation_manager import AutomationManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main function to run real LinkedIn automation for TestUser3"""
    
    # Create Flask application
    app = create_app()
    
    with app.app_context():
        print("🚀 AutoHire TestUser3 REAL LinkedIn Automation")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Fetch information for TestUser3
        print("🔍 Fetching TestUser3 information from database...")
        user = User.query.filter_by(username='TestUser3').first()
        
        if not user:
            print(" User 'TestUser3' not found in the database.")
            return
        
        print(f"✅ Found user: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🏢 LinkedIn: {user.linkedin_username}")
        
        # Check job preferences
        job_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
        if not job_preferences:
            print(" No job preferences configured for TestUser3")
            return
        
        print(f"   🎯 Job Titles: {job_preferences.get_preferred_job_titles()[:3]}...")  # Show first 3
        print(f"   📍 Locations: {job_preferences.get_preferred_locations()[:3]}...")   # Show first 3
        
        # Check if LinkedIn credentials are available
        if not user.linkedin_username:
            print(" LinkedIn credentials not configured for TestUser3")
            return
        
        print("\n🚨 WARNING: This will open a browser and perform REAL job applications!")
        print("🚨 Make sure TestUser3's LinkedIn credentials are correct.")
        print("⏳ Starting automation in 5 seconds...\n")
        
        # Countdown
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
        
        print("\n🤖 Initializing Automation Manager...")
        print("=" * 60)
        
        try:
            # Initialize automation manager
            automation_manager = AutomationManager(user.id)
            
            print("🔧 Setting up LinkedIn bot...")
            automation_manager.initialize_bots()
            
            if not automation_manager.linkedin_bot:
                print(" Failed to initialize LinkedIn bot")
                return
            
            print("✅ LinkedIn bot initialized successfully")
            
            # Get search criteria
            search_criteria = automation_manager.get_user_search_criteria()
            print(f"\n📋 Search Criteria:")
            print(f"   🎯 Job Titles: {search_criteria['job_titles'][:2]}")  # First 2 for demo
            print(f"   📍 Locations: {search_criteria['locations'][:2]}")    # First 2 for demo
            
            # Start the real automation process
            print(f"\n🔥 Starting REAL LinkedIn Job Application Process...")
            print("=" * 60)
            
            # Login to LinkedIn
            print("🔐 Logging into LinkedIn...")
            linkedin_bot = automation_manager.linkedin_bot
            
            if linkedin_bot.login():
                print("✅ Successfully logged into LinkedIn!")
                
                applications_made = 0
                max_applications = min(3, user.daily_application_limit)  # Limit to 3 for demo
                
                print(f"\n🎯 Target: Apply to up to {max_applications} jobs")
                print("=" * 40)
                
                # Search and apply for jobs
                for i, job_title in enumerate(search_criteria['job_titles'][:2]):  # First 2 titles
                    if applications_made >= max_applications:
                        break
                        
                    for j, location in enumerate(search_criteria['locations'][:2]):  # First 2 locations
                        if applications_made >= max_applications:
                            break
                        
                        print(f"\n🔍 Searching: '{job_title}' in '{location}'")
                        print("⏳ Please wait while we search for jobs...")
                        
                        try:
                            # Search for jobs
                            jobs = linkedin_bot.search_jobs(job_title, location)
                            print(f"📋 Found {len(jobs)} job listings")
                            
                            # Apply to jobs
                            for k, job_element in enumerate(jobs[:5]):  # Limit to first 5 jobs per search
                                if applications_made >= max_applications:
                                    break
                                
                                print(f"\n📝 Processing Job {k+1}/{min(5, len(jobs))}...")
                                
                                try:
                                    # Extract job details first
                                    job_details = linkedin_bot.extract_job_details(job_element)
                                    
                                    if not job_details or not job_details.get('job_title'):
                                        print("⚠️  Could not extract job details, skipping...")
                                        continue
                                    
                                    print(f"   🏢 Job: {job_details['job_title']}")
                                    print(f"   🏛️  Company: {job_details['company_name']}")
                                    print(f"   📍 Location: {job_details['location']}")
                                    
                                    # Check if already applied
                                    existing_app = JobApplication.query.filter_by(
                                        user_id=user.id,
                                        platform_job_id=job_details.get('platform_job_id'),
                                        platform='linkedin'
                                    ).first()
                                    
                                    if existing_app:
                                        print("   ⚠️  Already applied to this job, skipping...")
                                        continue
                                    
                                    # Check if job matches preferences
                                    if not automation_manager.job_matches_preferences(job_details):
                                        print("   ⚠️  Job doesn't match preferences, skipping...")
                                        continue
                                    
                                    print("   ✅ Job matches preferences!")
                                    print("   🤖 Attempting to apply...")
                                    
                                    # Apply to the job
                                    application_result = linkedin_bot.apply_to_job(
                                        job_element,
                                        job_preferences,
                                        user.skills.split(', ') if user.skills else []
                                    )
                                    
                                    if application_result['success']:
                                        print("   🎉 APPLICATION SUCCESSFUL!")
                                        applications_made += 1
                                        
                                        # Save to database
                                        try:
                                            automation_manager.save_job_application(
                                                job_details, 
                                                application_result
                                            )
                                            print("   💾 Application saved to database")
                                        except Exception as save_error:
                                            print(f"   ⚠️  Database save error: {str(save_error)}")
                                        
                                    else:
                                        print(f"    Application failed: {application_result.get('error', 'Unknown error')}")
                                    
                                    # Add delay between applications
                                    print("   ⏳ Waiting before next application...")
                                    time.sleep(3)
                                    
                                except Exception as job_error:
                                    print(f"    Error processing job: {str(job_error)}")
                                    continue
                            
                            # Add delay between searches
                            if applications_made < max_applications:
                                print("⏳ Waiting before next search...")
                                time.sleep(2)
                                
                        except Exception as search_error:
                            print(f" Error searching jobs: {str(search_error)}")
                            continue
                
                print(f"\n🏁 Automation Process Complete!")
                print("=" * 60)
                print(f"📊 Results Summary:")
                print(f"   ✅ Applications Made: {applications_made}")
                print(f"   🎯 Target Reached: {'Yes' if applications_made >= max_applications else 'No'}")
                
            else:
                print(" Failed to login to LinkedIn")
                
        except Exception as e:
            print(f"\n Critical Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up
            print("\n🧹 Cleaning up automation resources...")
            try:
                automation_manager.cleanup_bots()
                print("✅ Cleanup completed")
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup error: {str(cleanup_error)}")
        
        print(f"\n" + "=" * 60)
        print(f"⏰ Automation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 TestUser3 LinkedIn automation finished!")


if __name__ == "__main__":
    main()
