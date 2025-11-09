#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

LinkedIn UI Diagnostic Script
Inspects the current LinkedIn jobs page to find actual selectors
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from selenium.webdriver.common.by import By
import time

def diagnose_linkedin_ui():
    """Diagnose current LinkedIn UI structure"""
    
    # Setup
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
            
        print(" User and credentials verified")
        
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
            print(" LinkedIn login successful")
            
            # Navigate to jobs page and do a search
            linkedin_bot.driver.get("https://www.linkedin.com/jobs/")
            time.sleep(3)
            
            # Simple search
            keyword_selectors = [
                "//input[contains(@placeholder, 'Search jobs')]",
                "//input[@aria-label='Search jobs']",
                "//input[contains(@class, 'jobs-search-box__text-input')]",
                "//input[@id='jobs-search-box-keyword-id-ember*']",
                "//input[starts-with(@id, 'jobs-search-box-keyword')]"
            ]
            
            search_input = None
            for selector in keyword_selectors:
                try:
                    search_input = linkedin_bot.driver.find_element(By.XPATH, selector)
                    print(f" Found keyword input with: {selector}")
                    break
                except:
                    continue
                    
            if search_input:
                search_input.clear()
                search_input.send_keys("Software Engineer")
                search_input.send_keys('\n')  # Enter key
                time.sleep(5)
                print(" Search executed")
            else:
                print("⚠️ Could not find search input")
            
            print("\n" + "="*60)
            print("🔍 DIAGNOSTIC INSPECTION OF CURRENT LINKEDIN UI")
            print("="*60)
            
            # 1. Find all buttons on the page
            print("\n1. 🔲 ALL BUTTONS ON PAGE:")
            try:
                all_buttons = linkedin_bot.driver.find_elements(By.TAG_NAME, "button")
                print(f"   Found {len(all_buttons)} total buttons")
                
                for i, button in enumerate(all_buttons[:20]):  # First 20 buttons
                    try:
                        text = button.text.strip()[:50]  # First 50 chars
                        aria_label = button.get_attribute('aria-label') or ''
                        class_attr = button.get_attribute('class') or ''
                        if text or 'apply' in aria_label.lower() or 'filter' in aria_label.lower():
                            print(f"   Button {i+1}: '{text}' | Label: '{aria_label[:30]}' | Class: '{class_attr[:30]}'")
                    except:
                        continue
            except Exception as e:
                print(f"   Error finding buttons: {e}")
            
            # 2. Look for anything with "Easy Apply" text
            print("\n2. 🎯 ELEMENTS CONTAINING 'Easy Apply' TEXT:")
            easy_apply_elements = linkedin_bot.driver.find_elements(By.XPATH, "//*[contains(text(), 'Easy Apply')]")
            if easy_apply_elements:
                for i, elem in enumerate(easy_apply_elements):
                    try:
                        tag = elem.tag_name
                        text = elem.text.strip()[:50]
                        print(f"   Element {i+1}: <{tag}> '{text}'")
                    except:
                        continue
            else:
                print("   No elements found with 'Easy Apply' text")
            
            # 3. Look for filter-related elements
            print("\n3. 🔧 FILTER-RELATED ELEMENTS:")
            filter_selectors = [
                "//div[contains(@class, 'filter')]",
                "//div[contains(@class, 'search')]//ul",
                "//section//ul[contains(@class, 'list')]",
                "//div[contains(@class, 'jobs-search')]//ul"
            ]
            
            for selector in filter_selectors:
                try:
                    elements = linkedin_bot.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with: {selector}")
                        # Get details of first element
                        elem = elements[0]
                        print(f"     First element: {elem.get_attribute('outerHTML')[:100]}...")
                except:
                    continue
            
            # 4. Look for job cards
            print("\n4. 📋 JOB CARD ELEMENTS:")
            job_card_selectors = [
                "//li[contains(@class, 'jobs-')]",
                "//li[contains(@class, 'scaffold-')]",
                "//div[contains(@class, 'job-')]",
                "//div[contains(@class, 'card')]"
            ]
            
            for selector in job_card_selectors:
                try:
                    elements = linkedin_bot.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with: {selector}")
                except:
                    continue
            
            # 5. Get page source snippet for manual inspection
            print("\n5. 📄 PAGE SOURCE SNIPPET (around filter area):")
            try:
                page_source = linkedin_bot.driver.page_source
                # Look for filter-related section
                if 'filter' in page_source.lower():
                    import re
                    # Find section around filters
                    filter_matches = list(re.finditer(r'filter', page_source, re.IGNORECASE))
                    if filter_matches:
                        match = filter_matches[0]
                        start = max(0, match.start() - 200)
                        end = min(len(page_source), match.start() + 400)
                        snippet = page_source[start:end]
                        print(f"   {snippet}")
                else:
                    print("   No 'filter' text found in page source")
            except Exception as e:
                print(f"   Error getting page source: {e}")
            
            print("\n" + "="*60)
            print(" DIAGNOSTIC COMPLETED!")
            print("Check the output above to identify current LinkedIn UI patterns.")
            print("Press Ctrl+C to exit and close browser...")
            
            # Keep browser open for manual inspection
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Closing browser...")
                
        except Exception as e:
            print(f" Diagnostic error: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            try:
                linkedin_bot.cleanup()
                print(" Cleanup completed")
            except:
                pass

if __name__ == "__main__":
    print("🔍 LinkedIn UI Diagnostic Tool")
    print("=" * 40)
    print("This will inspect the current LinkedIn jobs page to identify")
    print("the actual UI elements and selectors we need to use.")
    print("\n⚠️  This will open a visible browser window.")
    print("⚠️  Press Ctrl+C when you're done inspecting.")
    print()
    
    response = input("Continue with diagnostic? (y/n): ")
    if response.lower() == 'y':
        diagnose_linkedin_ui()
    else:
        print("Diagnostic cancelled.")
