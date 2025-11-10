#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Complete LinkedIn Automation Test Script

This script tests the complete end-to-end LinkedIn job application automation:
1. Login to LinkedIn
2. Search for jobs
3. For each job: click → check eligibility → apply with Easy Apply
4. Fill forms → upload resume → answer questions with AI → review → submit
5. Move to next job and repeat

Usage:
    python test_complete_automation.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('automation_test.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main test function for complete LinkedIn automation"""
    
    print("🚀 COMPLETE LINKEDIN AUTOMATION TEST")
    print("="*60)
    print("This will test the complete end-to-end automation:")
    print("• Login to LinkedIn")
    print("• Search for jobs")
    print("• Click job cards")
    print("• Check eligibility")
    print("• Apply with Easy Apply")
    print("• Fill forms with AI")
    print("• Upload resume")
    print("• Review and submit applications")
    print("• Repeat for multiple jobs")
    print("="*60)
    
    # Get user confirmation
    response = input("\nDo you want to proceed with LIVE automation test? (y/n): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    # Get test parameters
    print("\n📝 CONFIGURE TEST PARAMETERS")
    print("-" * 30)
    
    keywords = input("Enter job search keywords (default: Software Engineer): ").strip()
    if not keywords:
        keywords = "Software Engineer"
    
    location = input("Enter location (default: Mumbai): ").strip()
    if not location:
        location = "Mumbai"
    
    max_applications = input("Enter max applications to submit (default: 3): ").strip()
    try:
        max_applications = int(max_applications) if max_applications else 3
    except ValueError:
        max_applications = 3
    
    # Check for resume file
    resume_path = input("Enter resume file path (optional): ").strip()
    if resume_path and not os.path.exists(resume_path):
        print(f"⚠️ Resume file not found at {resume_path}")
        resume_path = None
    
    # Initialize Flask app and database
    app = create_app()
    with app.app_context():
        try:
            # Get user from database
            user = User.query.filter_by(username='TestUser2').first()
            if not user:
                print(" TestUser2 not found in database!")
                print("Please make sure you have a test user set up.")
                return
            
            # Get user preferences
            user_preferences = JobPreferences.query.filter_by(user_id=user.id).first()
            
            # Get credentials
            linkedin_password = user.get_platform_password('linkedin')
            if not linkedin_password:
                print(" LinkedIn password not found for TestUser2")
                return
            
            # Get Gemini API key
            gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            if not gemini_api_key:
                print("⚠️ No Gemini API key found - AI features will be disabled")
            
            print(f"\n User: {user.username} ({user.email})")
            print(f" LinkedIn credentials: Available")
            print(f" AI features: {'Enabled' if gemini_api_key else 'Disabled'}")
            if resume_path:
                print(f" Resume: {resume_path}")
            
            # Create automation instance
            print(f"\n INITIALIZING LINKEDIN AUTOMATION")
            print("-" * 40)
            
            linkedin_bot = LinkedInAutomation(
                username=user.linkedin_username,
                password=linkedin_password,
                headless=False,  # Visible for testing
                gemini_api_key=gemini_api_key
            )
            
            if not linkedin_bot.driver:
                print(" Failed to initialize automation (ChromeDriver issue)")
                return
            
            print(" LinkedIn automation initialized")
            
            # Start complete automation
            print(f"\n🎯 STARTING COMPLETE AUTOMATION")
            print(f"🔍 Search: '{keywords}' in '{location}'")
            print(f"📊 Target: {max_applications} applications")
            print("="*60)
            
            # Run the complete automation
            result = linkedin_bot.run_automated_job_applications(
                keywords=keywords,
                location=location,
                user_preferences=user_preferences,
                user_skills=None,  # Will be extracted from user data
                max_applications=max_applications,
                resume_path=resume_path
            )
            
            # Display results
            print("\n" + "="*60)
            print("🏁 AUTOMATION COMPLETED")
            print("="*60)
            
            if result['success']:
                print(" Automation completed successfully!")
                
                stats = result['stats']
                print(f"\n📊 FINAL STATISTICS:")
                print(f"   Duration: {stats.get('total_duration', 0):.1f} seconds")
                print(f"   Jobs Viewed: {stats.get('total_jobs_viewed', 0)}")
                print(f"   Jobs Matched Criteria: {stats.get('jobs_matched_criteria', 0)}")
                print(f"   Applications Attempted: {stats.get('applications_attempted', 0)}")
                print(f"   Applications Successful: {stats.get('applications_successful', 0)}")
                print(f"   Applications Failed: {stats.get('applications_failed', 0)}")
                print(f"   Jobs Skipped (No Easy Apply): {stats.get('jobs_skipped_no_easy_apply', 0)}")
                print(f"   Jobs Skipped (Criteria): {stats.get('jobs_skipped_criteria', 0)}")
                print(f"   Errors: {stats.get('errors_encountered', 0)}")
                
                success_rate = 0
                if stats.get('applications_attempted', 0) > 0:
                    success_rate = (stats.get('applications_successful', 0) / stats.get('applications_attempted', 0)) * 100
                print(f"   Success Rate: {success_rate:.1f}%")
                
            else:
                print(" Automation failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
                
                if 'stats' in result:
                    stats = result['stats']
                    print(f"\n📊 PARTIAL STATISTICS:")
                    print(f"   Jobs Viewed: {stats.get('total_jobs_viewed', 0)}")
                    print(f"   Applications Attempted: {stats.get('applications_attempted', 0)}")
                    print(f"   Applications Successful: {stats.get('applications_successful', 0)}")
                    print(f"   Errors: {stats.get('errors_encountered', 0)}")
            
            # Keep browser open for inspection
            input("\n👁️ Browser will remain open for inspection. Press Enter to close...")
            
        except Exception as e:
            logger.error(f"Fatal error during automation test: {str(e)}")
            print(f" Fatal error: {str(e)}")
            
        finally:
            # Cleanup
            try:
                if 'linkedin_bot' in locals():
                    linkedin_bot.cleanup()
                    print(" Cleanup completed")
            except:
                pass

def test_ai_only():
    """Test AI components only without full automation"""
    print("\n AI COMPONENTS TEST")
    print("="*30)
    
    app = create_app()
    with app.app_context():
        try:
            # Get user
            user = User.query.filter_by(username='TestUser2').first()
            if not user:
                print(" TestUser2 not found")
                return
            
            # Get API key
            gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            if not gemini_api_key:
                print(" No Gemini API key found")
                return
            
            from app.utils.ai_question_answerer import AIQuestionAnswerer
            
            # Test AI initialization
            ai_answerer = AIQuestionAnswerer(api_key=gemini_api_key)
            print(" AI Question Answerer initialized")
            
            # Test user context preparation
            user_data = {
                'full_name': user.full_name or 'Test User',
                'email': user.email,
                'experience_years': user.experience_years or 3,
                'skills': ['Python', 'JavaScript', 'React'],
                'education': user.education or "Bachelor's in Computer Science"
            }
            
            user_context = ai_answerer.prepare_user_context(user_data)
            print(" User context prepared")
            
            # Test question analysis
            test_questions = [
                "How many years of experience do you have with Python?",
                "Are you authorized to work in India?",
                "What is your expected salary?",
                "Are you willing to relocate?",
                "Do you have experience with React?"
            ]
            
            print(f"\n🧪 Testing AI with sample questions:")
            for i, question in enumerate(test_questions, 1):
                print(f"\n{i}. {question}")
                
                analysis = ai_answerer.analyze_question_type(question, 'text')
                print(f"   Category: {analysis['category']}")
                
                answer = ai_answerer.generate_answer(
                    question_text=question,
                    user_context=user_context,
                    question_analysis=analysis
                )
                print(f"   AI Answer: {answer}")
            
            print("\n✅ AI test completed successfully!")
            
        except Exception as e:
            print(f" AI test failed: {str(e)}")

if __name__ == "__main__":
    print("LinkedIn Automation Test Options:")
    print("1. Complete end-to-end automation test (recommended)")
    print("2. AI components test only")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "2":
        test_ai_only()
    else:
        main()
