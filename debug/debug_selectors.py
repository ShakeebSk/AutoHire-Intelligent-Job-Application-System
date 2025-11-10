#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Diagnostic script to identify current LinkedIn selectors
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_linkedin_selectors():
    """Debug LinkedIn selectors by examining page structure"""
    app = create_app()
    with app.app_context():
        # Get TestUser2
        user = User.query.filter_by(username='TestUser2').first()
        if not user:
            print("❌ TestUser2 not found!")
            return
            
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
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
            headless=False  # Keep visible for debugging
        )
        
        try:
            print("\n🚀 Setting up ChromeDriver...")
            linkedin_bot.setup_driver()
            print("✅ ChromeDriver setup successful")
            
            print("\n🔐 Attempting LinkedIn login...")
            login_success = linkedin_bot.login()
            
            if login_success:
                print("✅ LinkedIn login successful!")
                
                # Wait and navigate to jobs
                time.sleep(3)
                print("\n🔍 Navigating to jobs page...")
                linkedin_bot.driver.get("https://www.linkedin.com/jobs")
                time.sleep(5)
                
                # Enter search terms
                print("\n📝 Entering search terms...")
                try:
                    # Try to find keyword input
                    keyword_selectors = [
                        "//input[contains(@id, 'jobs-search-box-keyword-id-ember')]",
                        "//input[contains(@placeholder, 'Search jobs')]",
                        "//input[@aria-label='Search jobs']",
                        "//input[contains(@class, 'jobs-search-box__text-input')]",
                        "//header//input[1]"
                    ]
                    
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.common.keys import Keys
                    
                    keyword_box = None
                    for selector in keyword_selectors:
                        try:
                            keyword_box = linkedin_bot.driver.find_element(By.XPATH, selector)
                            print(f"✅ Found keyword box with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if keyword_box:
                        keyword_box.clear()
                        keyword_box.send_keys("Software Engineer")
                        print("✅ Entered 'Software Engineer'")
                        time.sleep(2)
                        
                        # Try to trigger search
                        keyword_box.send_keys(Keys.RETURN)
                        print("✅ Triggered search")
                        time.sleep(8)  # Wait for results
                        
                        print("\n🔍 Looking for job cards with different selectors...")
                        
                        # Try various selectors to find job cards
                        selectors_to_try = [
                            "//div[contains(@class, 'job-search-card')]",
                            "//div[contains(@class, 'jobs-search-results__list-item')]",
                            "//li[contains(@class, 'jobs-search-results__list-item')]",
                            "//div[contains(@class, 'base-card')]",
                            "//div[contains(@class, 'jobs-search-results__list')]//li",
                            "//div[contains(@class, 'jobs-search-results__list')]//div",
                            "//ul[contains(@class, 'jobs-search__results-list')]//li",
                            "//div[contains(@data-entity-urn, 'job')]",
                            "//article[contains(@class, 'job')]",
                            "//div[contains(@class, 'ember-view') and contains(@class, 'job')]",
                            "//li[contains(@class, 'ember-view')]",
                            "//div[contains(@class, 'scaffold-layout__list-container')]//li",
                            "//main//li",
                            "//div[contains(@class, 'jobs-search-results')]//li"
                        ]
                        
                        for i, selector in enumerate(selectors_to_try):
                            try:
                                elements = linkedin_bot.driver.find_elements(By.XPATH, selector)
                                print(f"{i+1:2d}. Selector: {selector}")
                                print(f"    Found: {len(elements)} elements")
                                
                                if elements and len(elements) > 0:
                                    print(f"    ✅ SUCCESS! Found {len(elements)} job cards")
                                    # Show first element details
                                    first_element = elements[0]
                                    print(f"    First element class: {first_element.get_attribute('class')}")
                                    print(f"    First element tag: {first_element.tag_name}")
                                    print(f"    First element text preview: {first_element.text[:100]}...")
                                    print()
                                else:
                                    print("    ❌ No elements found")
                            except Exception as e:
                                print(f"    ❌ Error: {str(e)}")
                            print()
                        
                        # Try to get page source for manual inspection
                        print("\n📄 Getting page source structure...")
                        try:
                            # Look for main job results container
                            main_containers = linkedin_bot.driver.find_elements(By.XPATH, "//main")
                            if main_containers:
                                print(f"Found {len(main_containers)} main containers")
                                main_html = main_containers[0].get_attribute('outerHTML')
                                
                                # Save to file for inspection
                                with open('linkedin_page_structure.html', 'w', encoding='utf-8') as f:
                                    f.write(main_html)
                                print("✅ Saved page structure to 'linkedin_page_structure.html'")
                        except Exception as e:
                            print(f"❌ Error saving page structure: {e}")
                        
                        # Keep browser open for manual inspection
                        print("\n⏳ Keeping browser open for 60 seconds for manual inspection...")
                        print("💡 You can manually inspect the page to identify correct selectors")
                        time.sleep(60)
                        
                    else:
                        print("❌ Could not find keyword search box")
                        
                except Exception as e:
                    print(f"❌ Error during search: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ LinkedIn login failed")
                
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
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
    print("🔍 LinkedIn Selectors Debug Script")
    print("=" * 50)
    print("This will help identify the correct selectors for LinkedIn job cards.")
    print("Watch the browser and check the console output.")
    print()
    
    debug_linkedin_selectors()
    print("\n✅ Debug completed!")
