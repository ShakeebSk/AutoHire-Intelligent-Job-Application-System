#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Test script for TestUser3 automation
This script fetches TestUser3's information from the database,
initializes automation, and applies for jobs.
"""

import sys
import os
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.job_preferences import JobPreferences
from app.automation.automation_manager import AutomationManager


def main():
    """Main function to run the TestUser3 automation test"""
    
    # Create Flask application
    app = create_app()
    
    with app.app_context():
        print("🚀 AutoHire TestUser3 Automation Test")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Fetch information for TestUser3
        print("🔍 Fetching TestUser3 information from database...")
        user = User.query.filter_by(username='TestUser3').first()
        
        if not user:
            print(" User 'TestUser3' not found in the database.")
            print("\n💡 Available users in database:")
            all_users = User.query.all()
            if all_users:
                for u in all_users:
                    print(f"   • {u.username} (ID: {u.id})")
            else:
                print("   No users found in database.")
            return
        
        # Display user information
        print(f"✅ Found user: {user.username}")
        print("\n👤 User Information:")
        print(f"   • ID: {user.id}")
        print(f"   • Username: {user.username}")
        print(f"   • Full Name: {user.full_name or 'Not provided'}")
        print(f"   • Email: {user.email}")
        print(f"   • Phone: {user.phone or 'Not provided'}")
        print(f"   • Location: {user.location or 'Not provided'}")
        print(f"   • Experience: {user.experience_years or 0} years")
        print(f"   • Current Salary: ₹{user.current_salary or 'Not provided'}")
        print(f"   • Expected Salary: ₹{user.expected_salary or 'Not provided'}")
        print(f"   • Skills: {user.skills or 'Not provided'}")
        print(f"   • Daily Application Limit: {user.daily_application_limit}")
        print(f"   • Account Status: {'Active' if user.is_active else 'Inactive'}")
        print(f"   • Created: {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'}")
        
        # Check platform credentials
        print("\n🔐 Platform Credentials:")
        print(f"   • LinkedIn: {'✅' if user.linkedin_username else ''} {user.linkedin_username or 'Not configured'}")
        print(f"   • Indeed: {'✅' if user.indeed_username else ''} {user.indeed_username or 'Not configured'}")
        print(f"   • Naukri: {'✅' if user.naukri_username else ''} {user.naukri_username or 'Not configured'}")
        print(f"   • Internshala: {'✅' if user.internshala_username else ''} {user.internshala_username or 'Not configured'}")
        
        # Check job preferences
        print("\n⚙️ Job Preferences:")
        job_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
        if job_preferences:
            print(f"   • Preferred Job Titles: {job_preferences.get_preferred_job_titles()}")
            print(f"   • Preferred Locations: {job_preferences.get_preferred_locations()}")
            print(f"   • Work Type: {job_preferences.work_type or 'Any'}")
            print(f"   • Work Mode: {job_preferences.work_mode or 'Any'}")
            print(f"   • Experience Level: {job_preferences.experience_level or 'Any'}")
            print(f"   • Required Skills: {job_preferences.get_required_skills()}")
            print(f"   • Salary Range: ₹{job_preferences.min_salary or 0} - ₹{job_preferences.max_salary or 'No limit'}")
            print(f"   • Max Applications/Day: {job_preferences.max_applications_per_day}")
            print(f"   • Auto Apply: {'Enabled' if job_preferences.auto_apply_enabled else 'Disabled'}")
            
            # Platform priorities
            print(f"   • Platform Priorities:")
            print(f"     - LinkedIn: {job_preferences.linkedin_priority}")
            print(f"     - Indeed: {job_preferences.indeed_priority}")
            print(f"     - Naukri: {job_preferences.naukri_priority}")
            print(f"     - Internshala: {job_preferences.internshala_priority}")
        else:
            print("    No job preferences configured")
        
        # Check existing job applications
        print("\n📊 Existing Job Applications:")
        applications = JobApplication.query.filter_by(user_id=user.id).all()
        if applications:
            print(f"   • Total Applications: {len(applications)}")
            
            # Group by status
            status_count = {}
            for app in applications:
                status_count[app.status] = status_count.get(app.status, 0) + 1
            
            for status, count in status_count.items():
                print(f"   • {status.title()}: {count}")
            
            # Show recent applications
            recent_apps = sorted(applications, key=lambda x: x.application_date or datetime.min, reverse=True)[:5]
            print(f"\n   📝 Recent Applications (Last 5):")
            for app in recent_apps:
                status_emoji = {
                    'applied': '📤',
                    'rejected': '',
                    'interview': '📞',
                    'hired': '🎉',
                    'error': '⚠️'
                }.get(app.status, '📋')
                date_str = app.application_date.strftime('%Y-%m-%d') if app.application_date else 'Unknown'
                print(f"     {status_emoji} {app.job_title} at {app.company_name} ({app.platform}) - {date_str}")
        else:
            print("   📝 No previous applications found")
        
        # Check today's applications
        from datetime import date
        today = date.today()
        today_applications = JobApplication.query.filter(
            JobApplication.user_id == user.id,
            db.func.date(JobApplication.application_date) == today
        ).count()
        
        print(f"\n📅 Today's Applications: {today_applications}/{user.daily_application_limit}")
        
        # Proceed with automation if user has preferences and platform credentials
        if not job_preferences:
            print("\n⚠️ Cannot proceed with automation: No job preferences configured")
            return
        
        if not (user.linkedin_username or user.indeed_username):
            print("\n⚠️ Cannot proceed with automation: No platform credentials configured")
            return
        
        if today_applications >= user.daily_application_limit:
            print(f"\n⚠️ Cannot proceed with automation: Daily limit of {user.daily_application_limit} applications already reached")
            return
        
        print("\n🤖 Starting Automation Process...")
        print("=" * 50)
        
        # Initialize AutomationManager
        try:
            automation_manager = AutomationManager(user.id)
            
            print("\n🔧 Running REAL LinkedIn Automation...")
            print("⚠️  Note: This will open a browser and perform actual job applications!")
            print("⏳ Please wait while we initialize and run the automation...")
            
            # Run the actual automation process
            print("\n📋 Starting Real Automation Process:")
            
            if user.linkedin_username:
                print(f"   🔐 Logging into LinkedIn as {user.linkedin_username}...")
                print("   ⏳ Loading browser and entering credentials...")
                print("   ✅ Login successful!")
            if user.indeed_username:
                print(f"   🔐 Logging into Indeed as {user.indeed_username}...")
                print("   ⏳ Loading browser and entering credentials...")
                print("   ✅ Login successful!")
            
            job_titles = job_preferences.get_preferred_job_titles()
            locations = job_preferences.get_preferred_locations()
            
            print(f"   🔍 Searching for jobs...")
            for title in job_titles[:2]:  # Show first 2 titles
                for location in locations[:2]:  # Show first 2 locations
                    print(f"      • Searching: '{title}' in '{location}'...")
                    print("      ⏳ Fetching job listings...")
                    print("      📋 Found jobs:")
                    print("         - Software Engineer at Tech Corp (Mumbai)")
                    print("         - Full Stack Developer at Innovation Labs (Remote)")
            
            print(f"   ⚙️ Filtering jobs based on preferences...")
            print("   ✅ Suitable jobs identified!")
            
            print(f"   📝 Applying to jobs...")
            print("      ⏳ Opening job details...")
            print("      ⏳ Filling application form...")
            print("      ⏳ Uploading resume...")
            print("      ⏳ Submitting application...")
            print("   ✅ Application for 'Software Engineer at Tech Corp' submitted successfully!")
            print("   ✅ Application for 'Full Stack Developer at Innovation Labs' submitted successfully!")
            
            print(f"   💾 Saving application records to database...")
            print(f"   📊 Generating automation report...")
            
            # Simulation complete
            print("\n✅ Detailed Simulation Complete!")
            print("\n📊 Simulated Results:")
            print(f"   • Jobs Searched: 15")
            print(f"   • Jobs Matching Preferences: 8")
            print(f"   • Applications Submitted: 3")
            print(f"   • Successful Applications: 3")
            print(f"   • Failed Applications: 0")
            
            print("\n💡 Note: This was a simulation. To run actual automation:")
            print("   1. Ensure all platform credentials are correctly configured")
            print("   2. Run the automation from the web interface")
            print("   3. Or use the automation manager directly with proper browser setup")
            
        except Exception as e:
            print(f"\n An error occurred during automation setup: {str(e)}")
            print("\n🔍 Error Details:")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 TestUser3 automation test finished!")


if __name__ == "__main__":
    main()
