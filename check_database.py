#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Script to check all database tables and data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences, Resume
from app.models.job_application import JobApplication
from sqlalchemy import inspect
import json

def check_database():
    """Check all database tables and their data"""
    
    app = create_app()
    with app.app_context():
        print("🔍 Checking AutoHire Database...")
        print("=" * 60)
        
        # Get all table names
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📊 Available Tables: {tables}")
        print()
        
        # Check Users table
        print("👤 USERS TABLE:")
        print("-" * 30)
        users = User.query.all()
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Full Name: {user.full_name}")
            print(f"Phone: {user.phone}")
            print(f"Location: {user.location}")
            print(f"Skills: {user.skills}")
            print(f"Experience Years: {user.experience_years}")
            print(f"Current Salary: {user.current_salary}")
            print(f"Expected Salary: {user.expected_salary}")
            print(f"Education: {user.education}")
            print(f"Achievements: {user.achievements}")
            print(f"Daily Limit: {user.daily_application_limit}")
            print(f"LinkedIn Username: {user.linkedin_username}")
            print(f"LinkedIn Password: {' Set' if user.linkedin_password else ' Not Set'}")
            print(f"Indeed Username: {user.indeed_username}")
            print(f"Indeed Password: {' Set' if user.indeed_password else ' Not Set'}")
            print(f"Platform Priorities: {user.platform_priorities}")
            print(f"Created: {user.created_at}")
            print()
        
        # Check JobPreferences table
        print("⚙️ JOB PREFERENCES TABLE:")
        print("-" * 30)
        try:
            preferences = JobPreferences.query.all()
            if preferences:
                for pref in preferences:
                    print(f"ID: {pref.id}")
                    print(f"User ID: {pref.user_id}")
                    print(f"Preferred Job Titles: {pref.preferred_job_titles}")
                    print(f"Preferred Locations: {pref.preferred_locations}")
                    print(f"Work Type: {pref.work_type}")
                    print(f"Work Mode: {pref.work_mode}")
                    print(f"Experience Level: {pref.experience_level}")
                    print(f"Required Skills: {pref.required_skills}")
                    print(f"Min Salary: {pref.min_salary}")
                    print(f"Max Salary: {pref.max_salary}")
                    print(f"LinkedIn Priority: {pref.linkedin_priority}")
                    print(f"Indeed Priority: {pref.indeed_priority}")
                    print(f"Naukri Priority: {pref.naukri_priority}")
                    print(f"Internshala Priority: {pref.internshala_priority}")
                    print(f"Created: {pref.created_at}")
                    print(f"Updated: {pref.updated_at}")
                    print()
            else:
                print(" No job preferences found in database")
                print()
        except Exception as e:
            print(f" Error accessing JobPreferences table: {str(e)}")
            print()
        
        # Check Resume table
        print("📄 RESUME TABLE:")
        print("-" * 30)
        try:
            resumes = Resume.query.all()
            if resumes:
                for resume in resumes:
                    print(f"ID: {resume.id}")
                    print(f"User ID: {resume.user_id}")
                    print(f"Resume Name: {resume.resume_name}")
                    print(f"Original Filename: {resume.original_filename}")
                    print(f"File Path: {resume.file_path}")
                    print(f"File Size: {resume.file_size}")
                    print(f"File Type: {resume.file_type}")
                    print(f"Is Primary: {resume.is_primary}")
                    print(f"Is Active: {resume.is_active}")
                    print(f"Times Used: {resume.times_used}")
                    print(f"Uploaded: {resume.uploaded_at}")
                    print()
            else:
                print(" No resumes found in database")
                print()
        except Exception as e:
            print(f" Error accessing Resume table: {str(e)}")
            print()
        
        # Check JobApplication table
        print("📋 JOB APPLICATIONS TABLE:")
        print("-" * 30)
        try:
            applications = JobApplication.query.all()
            if applications:
                print(f"Found {len(applications)} job applications:")
                for app in applications[-5:]:  # Show last 5
                    print(f"ID: {app.id}, Job: {app.job_title}, Company: {app.company_name}, Status: {app.status}, Date: {app.application_date}")
                print()
            else:
                print(" No job applications found in database")
                print()
        except Exception as e:
            print(f" Error accessing JobApplication table: {str(e)}")
            print()
        
        # Check if JobPreferences table exists but has different structure
        print("🔧 CHECKING TABLE STRUCTURE:")
        print("-" * 30)
        try:
            # Execute raw SQL to check table structure
            result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            print(f"All tables in database: {tables}")
            
            if 'job_preferences' in tables:
                print("\n📊 JobPreferences table structure:")
                result = db.engine.execute("PRAGMA table_info(job_preferences);")
                for row in result:
                    print(f"  Column: {row[1]}, Type: {row[2]}, NotNull: {row[3]}, Default: {row[4]}")
                
                print("\n📋 Raw JobPreferences data:")
                result = db.engine.execute("SELECT * FROM job_preferences;")
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"  {row}")
                else:
                    print("  No data in job_preferences table")
            else:
                print(" job_preferences table does not exist!")
                
        except Exception as e:
            print(f" Error checking table structure: {str(e)}")

if __name__ == "__main__":
    check_database()
