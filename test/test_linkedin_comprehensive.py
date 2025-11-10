#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Comprehensive LinkedIn Automation Test Script
Tests all aspects of LinkedIn job application process
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from selenium.webdriver.common.by import By
import logging
import time

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('linkedin_test.log')
    ]
)
logger = logging.getLogger(__name__)

class LinkedInTester:
    def __init__(self, username='TestUser3'):
        self.username = username
        self.app = create_app()
        self.user = None
        self.linkedin_bot = None
        
    def setup_user(self):
        """Setup and verify user data"""
        with self.app.app_context():
            self.user = User.query.filter_by(username=self.username).first()
            if not self.user:
                print(f" {self.username} not found!")
                return False
                
            print(f" Found user: {self.user.username} (ID: {self.user.id})")
            print(f"   - Email: {self.user.email}")
            print(f"   - LinkedIn: {self.user.linkedin_username}")
            
            # Check preferences
            user_preferences = JobPreferences.query.filter_by(user_id=self.user.id).first()
            if not user_preferences:
                print(" User preferences not found!")
                return False
                
            print(f" User preferences loaded")
            print(f"   - Job titles: {user_preferences.get_preferred_job_titles()}")
            print(f"   - Locations: {user_preferences.get_preferred_locations()}")
            
            return True
    
    def setup_automation(self):
        """Setup LinkedIn automation"""
        try:
            with self.app.app_context():
                linkedin_password = self.user.get_platform_password('linkedin')
                if not linkedin_password:
                    print(" LinkedIn password could not be decrypted")
                    return False
                    
                print(" LinkedIn credentials verified")
                
                # Create bot
                self.linkedin_bot = LinkedInAutomation(
                    self.user.linkedin_username,
                    linkedin_password,
                    headless=False  # Visible for debugging
                )
                
                print("🚀 Setting up ChromeDriver...")
                self.linkedin_bot.setup_driver()
                print(" ChromeDriver setup successful")
                
                return True
                
        except Exception as e:
            print(f" Error setting up automation: {str(e)}")
            return False
    
    def test_login(self):
        """Test LinkedIn login"""
        print("\n" + "="*50)
        print("🔐 TESTING LINKEDIN LOGIN")
        print("="*50)
        
        try:
            login_success = self.linkedin_bot.login()
            if login_success:
                print(" LinkedIn login successful!")
                return True
            else:
                print(" LinkedIn login failed!")
                return False
        except Exception as e:
            print(f" Login error: {str(e)}")
            return False
    
    def test_job_search(self):
        """Test job search functionality"""
        print("\n" + "="*50)
        print("🔍 TESTING JOB SEARCH")
        print("="*50)
        
        try:
            with self.app.app_context():
                user_preferences = JobPreferences.query.filter_by(user_id=self.user.id).first()
                job_titles = user_preferences.get_preferred_job_titles()
                locations = user_preferences.get_preferred_locations()
                
                search_title = job_titles[0] if job_titles else "Web Developer"
                search_location = locations[0] if locations else "Mumbai"
                
                print(f"🔍 Searching for: '{search_title}' in '{search_location}'")
                
                jobs = self.linkedin_bot.search_jobs(search_title, search_location)
                print(f" Found {len(jobs)} job listings")
                
                if len(jobs) > 0:
                    print(f"📋 Testing job details extraction on first 3 jobs:")
                    for i, job in enumerate(jobs[:3]):
                        print(f"\n--- Job {i+1} ---")
                        try:
                            # Click job to load details
                            self.linkedin_bot.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", job)
                            time.sleep(1)
                            job.click()
                            time.sleep(3)
                            
                            # Extract from panel
                            job_details = self.linkedin_bot.extract_job_details_from_panel()
                            if job_details:
                                print(f"   Title: {job_details.get('job_title', 'N/A')}")
                                print(f"   Company: {job_details.get('company_name', 'N/A')}")
                                print(f"   Location: {job_details.get('location', 'N/A')}")
                                print(f"   Job ID: {job_details.get('platform_job_id', 'N/A')}")
                            else:
                                print("   Could not extract job details from panel")
                                # Try extracting from card
                                job_details = self.linkedin_bot.extract_job_details(job)
                                if job_details:
                                    print(f"  📋 (From card) Title: {job_details.get('job_title', 'N/A')}")
                                    print(f"  📋 (From card) Company: {job_details.get('company_name', 'N/A')}")
                        except Exception as e:
                            print(f"   Error with job {i+1}: {str(e)}")
                
                return len(jobs) > 0
                
        except Exception as e:
            print(f" Search error: {str(e)}")
            return False
    
    def test_job_application(self, max_applications=2):
        """Test job application process"""
        print("\n" + "="*50)
        print("🎯 TESTING JOB APPLICATION")
        print("="*50)
        
        try:
            with self.app.app_context():
                user_preferences = JobPreferences.query.filter_by(user_id=self.user.id).first()
                
                # Prepare user data
                user_data = {
                    'email': self.user.email,
                    'phone': self.user.phone,
                    'full_name': self.user.full_name or 'Test User',
                    'first_name': self.user.full_name.split()[0] if self.user.full_name else 'Test',
                    'last_name': ' '.join(self.user.full_name.split()[1:]) if self.user.full_name and len(self.user.full_name.split()) > 1 else 'User',
                    'city': getattr(self.user, 'city', 'Mumbai'),  # Default to Mumbai if city not set
                    'resume_path': None
                }
                
                print(f"📝 User data prepared:")
                print(f"   - Email: {user_data['email']}")
                print(f"   - Phone: {user_data['phone']}")
                print(f"   - Name: {user_data['full_name']}")
                
                # Test application process
                result = self.linkedin_bot.process_jobs_sequentially(
                    user_preferences=user_preferences,
                    user_skills=[],
                    user_data=user_data,
                    max_applications=max_applications
                )
                
                if result.get('success'):
                    applications_made = result.get('applications_made', 0)
                    print(f" Application test completed!")
                    print(f"📊 Applications made: {applications_made}")
                    return True
                else:
                    print(f" Application test failed: {result.get('error', 'Unknown error')}")
                    return False
                    
        except Exception as e:
            print(f" Application test error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_element_detection(self):
        """Test if key elements can be found"""
        print("\n" + "="*50)
        print("🔍 TESTING ELEMENT DETECTION")
        print("="*50)
        
        try:
            # Test Easy Apply filter detection
            easy_apply_selectors = [
                "//button[contains(@aria-label, 'Easy Apply filter')]",
                "//button[contains(text(), 'Easy Apply')]",
                "//div[contains(@class, 'search-reusables__filter-binary-toggle')]//button[contains(., 'Easy Apply')]"
            ]
            
            print("🔍 Testing Easy Apply filter detection...")
            for selector in easy_apply_selectors:
                try:
                    elements = self.linkedin_bot.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with: {selector}")
                        for i, elem in enumerate(elements):
                            try:
                                print(f"    - Element {i+1}: '{elem.text}' (displayed: {elem.is_displayed()})")
                            except:
                                print(f"    - Element {i+1}: Could not get text")
                    else:
                        print(f"   No elements found with: {selector}")
                except Exception as e:
                    print(f"   Error with selector: {str(e)}")
            
            # Test job card detection
            print("\n🔍 Testing job card detection...")
            job_card_selectors = [
                "//li[contains(@class, 'scaffold-layout__list-item')]",
                "//li[contains(@class, 'jobs-search-results__list-item')]",
                "//main//ul//li[contains(@class, 'ember-view')]"
            ]
            
            for selector in job_card_selectors:
                try:
                    elements = self.linkedin_bot.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} job cards with: {selector}")
                        break
                    else:
                        print(f"   No job cards found with: {selector}")
                except Exception as e:
                    print(f"   Error with selector: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f" Element detection error: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 LINKEDIN AUTOMATION COMPREHENSIVE TEST")
        print("="*60)
        
        # Setup
        if not self.setup_user():
            return False
            
        if not self.setup_automation():
            return False
        
        try:
            # Test 1: Login
            if not self.test_login():
                return False
            
            print("\n⏳ Waiting 3 seconds before proceeding...")
            time.sleep(3)
            
            # Test 2: Element Detection
            self.test_element_detection()
            
            print("\n⏳ Waiting 2 seconds before search...")
            time.sleep(2)
            
            # Test 3: Job Search
            if not self.test_job_search():
                print("⚠️ Search failed, but continuing...")
            
            print("\n⏳ Waiting 3 seconds before application test...")
            time.sleep(3)
            
            # Test 4: Job Application (limited to 2 for testing)
            print("🎯 Starting application test (max 2 applications for testing)...")
            self.test_job_application(max_applications=2)
            
            print("\n COMPREHENSIVE TEST COMPLETED!")
            print("Check the logs above for detailed results.")
            
            input("\nPress Enter to close browser and exit...")
            
        except Exception as e:
            print(f" Test error: {str(e)}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to close browser and exit...")
            return False
        
        finally:
            # Cleanup
            if self.linkedin_bot:
                try:
                    self.linkedin_bot.cleanup()
                    print(" Cleanup completed")
                except:
                    pass

if __name__ == "__main__":
    print("🧪 LinkedIn Automation Comprehensive Tester")
    print("="*50)
    print("This will test all aspects of your LinkedIn automation:")
    print("• User setup and credentials")
    print("• LinkedIn login")
    print("• Element detection")
    print("• Job search functionality")
    print("• Job details extraction")
    print("• Job application process")
    print()
    print("⚠️  Note: This will open a visible browser window.")
    print("⚠️  Make sure you have TestUser3 set up with LinkedIn credentials.")
    print()
    
    response = input("Continue with comprehensive test? (y/n): ")
    if response.lower() == 'y':
        tester = LinkedInTester('TestUser3')
        tester.run_comprehensive_test()
    else:
        print("Test cancelled.")
