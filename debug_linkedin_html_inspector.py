#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

LinkedIn HTML Structure Inspector
This script helps us understand the actual HTML structure of LinkedIn job cards
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

def inspect_linkedin_structure():
    """Inspect LinkedIn job card HTML structure"""
    app = create_app()
    with app.app_context():
        # Get TestUser3
        user = User.query.filter_by(username='TestUser3').first()
        if not user:
            print("❌ TestUser3 not found!")
            return
            
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
                
                print("\n🔍 Navigating to jobs and searching...")
                jobs = linkedin_bot.search_jobs("Software Engineer")
                
                print(f"✅ Found {len(jobs)} job listings")
                
                if jobs:
                    print("\n🔍 INSPECTING HTML STRUCTURE OF FIRST JOB CARD...")
                    
                    # Get the first job card
                    first_job = jobs[0]
                    
                    # Print the outer HTML of the job card
                    print("\n" + "="*80)
                    print("JOB CARD HTML STRUCTURE:")
                    print("="*80)
                    
                    try:
                        job_html = first_job.get_attribute('outerHTML')
                        # Clean up the HTML for better readability
                        import re
                        job_html = re.sub(r'>\s+<', '><', job_html)  # Remove whitespace between tags
                        job_html = job_html.replace('><', '>\n<')  # Add line breaks
                        
                        # Print first 50 lines to avoid overwhelming output
                        lines = job_html.split('\n')
                        for i, line in enumerate(lines[:100]):  # Show first 100 lines
                            print(f"{i+1:3d}: {line}")
                            
                        if len(lines) > 100:
                            print(f"... (truncated, total {len(lines)} lines)")
                            
                    except Exception as e:
                        print(f"Error getting HTML: {str(e)}")
                    
                    print("\n" + "="*80)
                    print("LOOKING FOR SPECIFIC ELEMENTS...")
                    print("="*80)
                    
                    # Try to find any clickable links in the job card
                    try:
                        links = first_job.find_elements("xpath", ".//a")
                        print(f"\n📎 Found {len(links)} links in job card:")
                        for i, link in enumerate(links[:10]):  # Show first 10 links
                            try:
                                href = link.get_attribute('href')
                                text = link.text.strip()
                                classes = link.get_attribute('class')
                                print(f"  Link {i+1}:")
                                print(f"    Text: '{text}'")
                                print(f"    Href: {href}")
                                print(f"    Classes: {classes}")
                                print()
                            except Exception as e:
                                print(f"    Error getting link {i+1}: {str(e)}")
                    except Exception as e:
                        print(f"Error finding links: {str(e)}")
                    
                    # Try to find any text elements that might be titles
                    try:
                        text_elements = first_job.find_elements("xpath", ".//*[text()]")
                        print(f"\n📝 Found {len(text_elements)} text elements:")
                        for i, elem in enumerate(text_elements[:20]):  # Show first 20
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 5:  # Only show meaningful text
                                    tag_name = elem.tag_name
                                    classes = elem.get_attribute('class')
                                    print(f"  {i+1}: [{tag_name}] '{text}' (class: {classes})")
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"Error finding text elements: {str(e)}")
                    
                    # Try to find elements with specific patterns
                    print(f"\n🎯 SEARCHING FOR COMMON PATTERNS:")
                    
                    # Search for elements containing job-related keywords
                    patterns = [
                        "job-card",
                        "title", 
                        "company",
                        "location",
                        "ember-view"
                    ]
                    
                    for pattern in patterns:
                        try:
                            elements = first_job.find_elements("xpath", f".//*[contains(@class, '{pattern}')]")
                            print(f"  Elements with '{pattern}' in class: {len(elements)}")
                            for i, elem in enumerate(elements[:5]):  # Show first 5
                                try:
                                    text = elem.text.strip()
                                    classes = elem.get_attribute('class')
                                    tag = elem.tag_name
                                    print(f"    [{tag}] '{text[:50]}...' (class: {classes})")
                                except:
                                    continue
                        except Exception as e:
                            print(f"  Error searching for '{pattern}': {str(e)}")
                    
                    print(f"\n⏳ Keeping browser open for 60 seconds for manual inspection...")
                    print("You can now manually inspect the page in the browser!")
                    time.sleep(60)
                    
                else:
                    print("❌ No jobs found to inspect")
                    
            else:
                print("❌ LinkedIn login failed")
                
        except Exception as e:
            print(f"❌ Error during inspection: {str(e)}")
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
    print("🔍 LinkedIn HTML Structure Inspector")
    print("=" * 50)
    print("This will help us understand the current LinkedIn job card structure.")
    print("Watch the browser window and check the console output.")
    print()
    
    inspect_linkedin_structure()
    print("\n✅ Inspection completed!")
