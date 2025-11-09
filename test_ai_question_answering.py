#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Comprehensive Test Script for AI-Powered Question Answering
Tests the complete AI integration with LinkedIn job applications
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from app.utils.ai_question_answerer import AIQuestionAnswerer
from app.utils.form_question_parser import FormQuestionParser
import logging
import time

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_test.log')
    ]
)
logger = logging.getLogger(__name__)

class AIQuestionAnsweringTester:
    def __init__(self, username='TestUser3'):
        self.username = username
        self.app = create_app()
        self.user = None
        self.linkedin_bot = None
        self.ai_answerer = None
        self.gemini_api_key = None
        
    def setup_user_and_api_key(self):
        """Setup user data and get API key"""
        print("🔧 Setting up user data and API configuration...")
        
        with self.app.app_context():
            self.user = User.query.filter_by(username=self.username).first()
            if not self.user:
                print(f" {self.username} not found!")
                return False
                
            print(f"✅ Found user: {self.user.username}")
            print(f"   - Email: {self.user.email}")
            print(f"   - LinkedIn: {self.user.linkedin_username}")
            
            # Check preferences
            user_preferences = JobPreferences.query.filter_by(user_id=self.user.id).first()
            if not user_preferences:
                print(" User preferences not found!")
                return False
                
            print(f"✅ User preferences loaded")
            print(f"   - Job titles: {user_preferences.get_preferred_job_titles()}")
            
            return True
    
    def get_api_key(self):
        """Get Gemini API key from user"""
        print("\n🔑 API Key Setup")
        print("=" * 50)
        print("You need a Google Gemini API key to test AI question answering.")
        print("Get your free API key at: https://makersuite.google.com/app/apikey")
        print()
        
        self.gemini_api_key = input("Enter your Google Gemini API key (or press Enter to skip AI testing): ").strip()
        
        if not self.gemini_api_key:
            print("⚠️ No API key provided - will test basic functionality only")
            return False
        
        print("✅ API key provided - will test full AI functionality")
        return True
    
    def test_ai_service_standalone(self):
        """Test AI service independently"""
        print("\n" + "="*60)
        print(" TESTING AI QUESTION ANSWERING SERVICE")
        print("="*60)
        
        if not self.gemini_api_key:
            print("⏭️ Skipping AI service test - no API key provided")
            return True
        
        try:
            # Initialize AI service
            self.ai_answerer = AIQuestionAnswerer(api_key=self.gemini_api_key)
            print("✅ AI Question Answerer initialized successfully")
            
            # Prepare test user data
            with self.app.app_context():
                user_data = {
                    'full_name': self.user.full_name or 'Test User',
                    'email': self.user.email,
                    'phone': self.user.phone,
                    'city': self.user.city,
                    'experience_years': 3,
                    'current_role': 'Software Developer',
                    'education': 'Bachelor\'s in Computer Science',
                    'skills': ['Python', 'JavaScript', 'React', 'SQL'],
                    'previous_companies': ['Tech Corp', 'StartupXYZ'],
                    'work_authorization': 'Yes',
                    'willing_to_relocate': 'Yes',
                    'availability': 'Immediately'
                }
                
                print("✅ Test user data prepared")
                
                # Test various question types
                test_questions = [
                    {
                        'question': 'Are you authorized to work in this country?',
                        'type': 'radio',
                        'options': ['Yes', 'No'],
                        'expected_category': 'yes_no'
                    },
                    {
                        'question': 'How many years of experience do you have with Python?',
                        'type': 'text',
                        'options': [],
                        'expected_category': 'experience'
                    },
                    {
                        'question': 'What is your expected salary range?',
                        'type': 'text',
                        'options': [],
                        'expected_category': 'salary'
                    },
                    {
                        'question': 'When can you start working?',
                        'type': 'select',
                        'options': ['Immediately', '2 weeks notice', '1 month notice'],
                        'expected_category': 'availability'
                    },
                    {
                        'question': 'Why are you interested in this position?',
                        'type': 'textarea',
                        'options': [],
                        'expected_category': 'cover_letter'
                    }
                ]
                
                user_context = self.ai_answerer.prepare_user_context(user_data)
                print(f"✅ User context prepared (length: {len(user_context)} chars)")
                
                # Test each question
                successful_tests = 0
                for i, test_q in enumerate(test_questions):
                    try:
                        print(f"\n--- Test Question {i+1}/{len(test_questions)} ---")
                        print(f"Question: {test_q['question']}")
                        print(f"Type: {test_q['type']}")
                        if test_q['options']:
                            print(f"Options: {test_q['options']}")
                        
                        # Analyze question
                        analysis = self.ai_answerer.analyze_question_type(
                            test_q['question'], 
                            test_q['type']
                        )
                        
                        print(f"AI Analysis:")
                        print(f"  - Category: {analysis['category']}")
                        print(f"  - Expected: {test_q['expected_category']}")
                        print(f"  - Required: {analysis['is_required']}")
                        
                        # Generate answer
                        answer = self.ai_answerer.generate_answer(
                            question_text=test_q['question'],
                            user_context=user_context,
                            question_analysis=analysis,
                            options=test_q['options']
                        )
                        
                        if answer:
                            print(f" AI Answer: '{answer}'")
                            
                            # Validate answer quality
                            if test_q['options'] and answer not in test_q['options']:
                                # Check if answer matches any option partially
                                matches = [opt for opt in test_q['options'] if answer.lower() in opt.lower() or opt.lower() in answer.lower()]
                                if matches:
                                    print(f"✅ Answer matches option: {matches[0]}")
                                    successful_tests += 1
                                else:
                                    print(f"⚠️ Answer doesn't match available options")
                            else:
                                print("✅ Answer generated successfully")
                                successful_tests += 1
                        else:
                            print(" AI failed to generate answer")
                            
                    except Exception as e:
                        print(f" Error testing question {i+1}: {str(e)}")
                
                print(f"\n📊 AI Service Test Summary:")
                print(f"   Total questions tested: {len(test_questions)}")
                print(f"   Successful answers: {successful_tests}")
                print(f"   Success rate: {(successful_tests/len(test_questions)*100):.1f}%")
                
                return successful_tests >= len(test_questions) * 0.8  # 80% success rate
                
        except Exception as e:
            print(f" AI service test failed: {str(e)}")
            return False
    
    def test_linkedin_integration(self):
        """Test AI integration with LinkedIn automation"""
        print("\n" + "="*60)
        print("🔗 TESTING LINKEDIN AI INTEGRATION")
        print("="*60)
        
        try:
            with self.app.app_context():
                # Get credentials
                linkedin_password = self.user.get_platform_password('linkedin')
                if not linkedin_password:
                    print(" LinkedIn password could not be decrypted")
                    return False
                    
                print("✅ LinkedIn credentials verified")
                
                # Create LinkedIn bot with AI integration
                self.linkedin_bot = LinkedInAutomation(
                    self.user.linkedin_username,
                    linkedin_password,
                    headless=False,  # Visible for testing
                    gemini_api_key=self.gemini_api_key
                )
                
                print("🚀 Setting up LinkedIn automation with AI...")
                
                if not self.linkedin_bot.driver:
                    print(" Failed to setup Chrome driver")
                    return False
                    
                print("✅ LinkedIn automation with AI initialized successfully")
                
                # Test login
                print("\n🔐 Testing LinkedIn login...")
                login_success = self.linkedin_bot.login()
                
                if not login_success:
                    print(" LinkedIn login failed")
                    return False
                    
                print("✅ LinkedIn login successful")
                
                # Wait for manual navigation to a job application
                print("\n📋 Manual Job Application Test")
                print("-" * 40)
                print("1. Navigate to a LinkedIn job and click 'Easy Apply'")
                print("2. When you reach a form with questions, press Enter here")
                print("3. The AI will automatically detect and fill the form")
                print()
                
                input("Press Enter when you're ready to test AI form filling...")
                
                # Test AI form filling on current page
                if self.linkedin_bot.ai_answerer and self.linkedin_bot.form_parser:
                    print("\n🤖 Testing AI form filling on current page...")
                    
                    # Prepare test user data
                    user_data = {
                        'full_name': self.user.full_name or 'Test User',
                        'email': self.user.email,
                        'phone': self.user.phone,
                        'city': self.user.city,
                        'experience_years': 3,
                        'current_role': 'Software Developer',
                        'education': 'Bachelor\'s in Computer Science',
                        'skills': ['Python', 'JavaScript', 'React', 'SQL'],
                        'work_authorization': 'Yes',
                        'willing_to_relocate': 'Yes',
                        'availability': 'Immediately'
                    }
                    
                    # Test AI form filling
                    success = self.linkedin_bot._ai_fill_application_form(user_data)
                    
                    if success:
                        print("✅ AI form filling test completed successfully")
                        print("Check the browser to see the filled form")
                        
                        input("\nPress Enter to continue or Ctrl+C to exit...")
                        return True
                    else:
                        print(" AI form filling test failed")
                        return False
                else:
                    print(" AI components not properly initialized")
                    return False
                    
        except Exception as e:
            print(f" LinkedIn integration test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            if self.linkedin_bot:
                input("\nPress Enter to close browser and exit...")
                try:
                    self.linkedin_bot.cleanup()
                    print("✅ Cleanup completed")
                except:
                    pass
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 AI-POWERED QUESTION ANSWERING TEST SUITE")
        print("="*70)
        print("This test suite will verify:")
        print("• AI question answering service")
        print("• Form question detection and parsing")
        print("• LinkedIn integration with AI")
        print()
        
        # Setup
        if not self.setup_user_and_api_key():
            return False
        
        # Get API key
        has_api_key = self.get_api_key()
        
        try:
            # Test 1: AI Service (if API key provided)
            if has_api_key:
                ai_success = self.test_ai_service_standalone()
                if not ai_success:
                    print("⚠️ AI service test failed, but continuing...")
            
            # Test 2: LinkedIn Integration
            linkedin_success = self.test_linkedin_integration()
            
            # Summary
            print("\n" + "="*70)
            print("🏁 TEST SUITE COMPLETED")
            print("="*70)
            
            if has_api_key:
                print(f"AI Service Test: {'✅ PASSED' if ai_success else ' FAILED'}")
            else:
                print("AI Service Test: ⏭️ SKIPPED (No API key)")
                
            print(f"LinkedIn Integration: {'✅ PASSED' if linkedin_success else ' FAILED'}")
            
            if has_api_key and ai_success and linkedin_success:
                print("\n🎉 ALL TESTS PASSED! Your AI question answering is working perfectly!")
            elif linkedin_success:
                print("\n✅ Basic integration working. Add API key for full AI functionality.")
            else:
                print("\n Some tests failed. Check the logs for details.")
                
        except KeyboardInterrupt:
            print("\n\n⛔ Test cancelled by user")
        except Exception as e:
            print(f"\n Test suite error: {str(e)}")

if __name__ == "__main__":
    print("🧪 AI Question Answering Comprehensive Tester")
    print("="*50)
    print("⚠️  IMPORTANT SETUP REQUIRED:")
    print("1. Make sure TestUser3 is set up with LinkedIn credentials")
    print("2. Have your Google Gemini API key ready")
    print("3. Ensure you have a stable internet connection")
    print()
    
    response = input("Ready to start testing? (y/n): ")
    if response.lower() == 'y':
        tester = AIQuestionAnsweringTester('TestUser3')
        tester.run_comprehensive_test()
    else:
        print("Test cancelled.")
