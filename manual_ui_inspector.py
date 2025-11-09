#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Manual LinkedIn UI Inspector
Opens LinkedIn jobs page after login and lets you manually inspect elements
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from selenium.webdriver.common.by import By
import time

def manual_inspector():
    """Open LinkedIn and pause for manual inspection"""
    
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username='TestUser3').first()
        if not user:
            print(" TestUser3 not found!")
            return
            
        linkedin_password = user.get_platform_password('linkedin')
        if not linkedin_password:
            print(" LinkedIn password could not be decrypted")
            return
            
        print("✅ User and credentials verified")
        
        # Create bot
        linkedin_bot = LinkedInAutomation(
            user.linkedin_username,
            linkedin_password,
            headless=False  # Visible for inspection
        )
        
        try:
            # Setup and login
            linkedin_bot.setup_driver()
            print("🚀 ChromeDriver setup successful")
            
            if not linkedin_bot.login():
                print(" LinkedIn login failed!")
                return
            print("✅ LinkedIn login successful")
            
            # Navigate to jobs and search
            print("🔍 Performing search to get to results page...")
            jobs = linkedin_bot.search_jobs("Software Engineer", "Mumbai")
            print(f"✅ Search completed, found {len(jobs)} jobs")
            
            # Now we're on the search results page
            current_url = linkedin_bot.driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            print("\n" + "="*80)
            print("🔍 MANUAL INSPECTION MODE")
            print("="*80)
            print("The browser window is now open with LinkedIn search results.")
            print("You can now:")
            print("1. Right-click on the Easy Apply filter button")
            print("2. Select 'Inspect Element' or 'Inspect'")
            print("3. Look at the HTML structure to find the correct selector")
            print("4. Look for job cards in the results list")
            print()
            print("📋 WHAT TO LOOK FOR:")
            print("✅ Easy Apply Filter Button:")
            print("   - Look for a button or toggle with text 'Easy Apply'")
            print("   - Note its HTML path, class names, and attributes")
            print("   - It's usually in a filter panel or sidebar")
            print()
            print("✅ Job Cards:")
            print("   - Look for the list of job results")
            print("   - Each job should be in a <li> or <div> element")
            print("   - Note the class names of these container elements")
            print()
            print("🎯 EXAMPLE SELECTORS TO TRY:")
            print("Easy Apply: //button[contains(text(), 'Easy Apply')]")
            print("Job Cards: //li[contains(@class, 'jobs-search-results__list-item')]")
            print()
            print("⚠️  WHEN YOU'RE DONE:")
            print("Press Ctrl+C to close the browser and exit")
            print("="*80)
            
            # Keep browser open for manual inspection
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Closing browser...")
                
        except Exception as e:
            print(f" Error: {str(e)}")
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
    print("🔍 Manual LinkedIn UI Inspector")
    print("=" * 50)
    print("This will:")
    print("1. Log into LinkedIn")
    print("2. Navigate to jobs and perform a search")
    print("3. Open the results page for manual inspection")
    print("4. Keep the browser open so you can inspect elements")
    print()
    print("You can then right-click on elements and inspect them")
    print("to find the correct selectors for current LinkedIn UI.")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        manual_inspector()
    else:
        print("Cancelled.")
