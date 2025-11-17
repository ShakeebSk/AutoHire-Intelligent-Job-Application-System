'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from app.automation.base_automation import BaseJobAutomation
from app.utils.ai_question_answerer import AIQuestionAnswerer
from app.utils.form_question_parser import FormQuestionParser
import time
import logging
import re
import os


class LinkedInAutomation(BaseJobAutomation):
    # Enhanced LinkedIn Automation including AI scoring and PDF generation
    """LinkedIn Job Automation"""
    
    def __init__(self, username, password, headless=True, gemini_api_key=None):
        super().__init__(username, password, headless)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs"
        self.applied_jobs = set()
        self.search_completed = False
        self.current_job_index = 0
        self.easy_apply_filter_applied = False
        self.successful_applications = 0
        self.daily_application_limit = 10
        
        # Initialize AI question answerer
        self.ai_answerer = None
        self.form_parser = None
        
        if gemini_api_key:
            try:
                self.ai_answerer = AIQuestionAnswerer(api_key=gemini_api_key)
                self.logger.info(" AI Question Answerer initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize AI Question Answerer: {str(e)}")
                self.logger.info("Will proceed without AI question answering")
        else:
            self.logger.info("No Gemini API key provided - AI question answering disabled")
        
        # Set up the Chrome driver
        try:
            self.setup_driver()
            if self.driver:
                self.form_parser = FormQuestionParser(self.driver)
        except Exception as e:
            self.logger.error(f"Failed to initialize LinkedIn automation: {str(e)}")
            self.driver = None
    
    def login(self):
        """Login to LinkedIn"""
        try:
            self.logger.info("Navigating to LinkedIn login page")
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            username_field = self.wait_for_element((By.ID, "username"))
            password_field = self.wait_for_element((By.ID, "password"))
            
            # Enter credentials
            self.safe_send_keys(username_field, self.username)
            self.safe_send_keys(password_field, self.password)
            self.random_delay(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.safe_click(login_button)
            
            # Wait for login to complete
            self.random_delay(3, 5)
            
            # Handle save password popup
            self._dismiss_save_password_popup()
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.logger.info("Successfully logged into LinkedIn")
                return True
            else:
                self.logger.error("LinkedIn login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during LinkedIn login: {str(e)}")
            return False
    
    def search_jobs(self, keywords, location=None, filters=None):
        """Search for jobs on LinkedIn - only perform search if not already completed"""
        try:
            # Check if we already have a search loaded and should not reload
            if self.search_completed and "jobs/search" in self.driver.current_url:
                self.logger.info("Search already completed and loaded, skipping new search")
                # Get existing job cards from current search
                job_cards = self._get_job_cards()
                self.logger.info(f"Found {len(job_cards)} existing job listings")
                return job_cards
            
            self.logger.info(f"Performing new LinkedIn job search: {keywords} in {location or 'Any location'}")
            
            
            self.driver.get(self.jobs_url)
            self.random_delay(3, 5)  # Increased delay for page load
            self.logger.info("Navigated to jobs page successfully")
            
            keyword_box = None
            keyword_selectors = [
                "//input[contains(@id, 'jobs-search-box-keyword-id-ember')]",  # Dynamic ID pattern
                "/html/body/div[6]/header/div/div/div/div[2]/div[2]/div/div/input[1]",  # Full XPath
                "//input[contains(@placeholder, 'Search jobs')]",
                "//input[@aria-label='Search jobs']",
                "//input[contains(@class, 'jobs-search-box__text-input')]",
                "//header//input[1]",  # First input in header
                "div[6] header input[1]"  # CSS selector
            ]
            
            self.logger.info("Attempting to locate keyword search input")
            
            for selector in keyword_selectors:
                try:
                    keyword_box = self.wait_for_element((By.XPATH, selector), timeout=5)
                    break
                except:
                    continue
            
            if not keyword_box:
                raise Exception("Could not find keyword search box")
            

            try:
                keyword_box.clear()
                
               
                search_query = keywords
                
                
                # if location:
                    
                #     self.logger.info(f"LinkedIn UI updated: Location '{location}' will be ignored - using only job keywords for broader results")
                #     self.logger.info("Note: You can filter by location using LinkedIn's location filters after search if needed")
                
                
                if location:
                    search_query = f"{keywords} in {location}"
                    self.logger.info(f"Combined search query: '{search_query}'")
                
                self.safe_send_keys(keyword_box, search_query)
                self.logger.info(f"Search query '{search_query}' entered successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to enter search query: {str(e)}")
                return []
            
            self.random_delay(1, 2)
            
            
            
            search_triggered = False
            
            
            try:
                if keyword_box.is_displayed() and keyword_box.is_enabled():
                    keyword_box.send_keys(Keys.RETURN)
                    search_triggered = True
                    self.logger.info("Search triggered via Enter key")
                else:
                    self.logger.error("Failed to trigger search using Enter key")
            except Exception as e:
                self.logger.warning(f"Could not trigger search via Enter: {str(e)}")
            
            
            if not search_triggered:
                search_button_selectors = [
                    "//button[contains(@class, 'jobs-search-box__submit-button')]",
                    "//button[@type='submit']",
                    "//button[contains(., 'Search')]",
                    "//button[@aria-label='Search']"
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_button = self.driver.find_element(By.XPATH, selector)
                        if search_button.is_displayed() and search_button.is_enabled():
                            self.safe_click(search_button)
                            search_triggered = True
                            self.logger.info("Search triggered via button click")
                            break
                    except NoSuchElementException:
                        self.logger.error(f"Search button '{selector}' not found")
                    except Exception as e:
                        self.logger.error(f"Error interacting with search button {selector}: {str(e)}")
                        return []
            
            if not search_triggered:
                raise Exception("Could not trigger job search")
                
            self.logger.info("Waiting for search results to load...")
            self.random_delay(5, 8)  # Wait longer for results to load
            if not self.easy_apply_filter_applied:
                self.logger.info("Search completed, now applying Easy Apply filter...")
                # Create a base filter dict if none provided
                if not filters:
                    filters = {}
                filters['easy_apply'] = True
                self._apply_search_filters(filters)
            else:
                self.logger.info("[SUCCESS] Easy Apply filter already applied in this session - skipping reapplication")
            job_cards = self._get_job_cards()
            self.logger.info(f"Found {len(job_cards)} job listings with Easy Apply filter")
            self.search_completed = True
            self.current_job_index = 0  # Reset job index for new search
            
            return job_cards
            
        except Exception as e:
            self.logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
    
    def _apply_search_filters(self, filters):
        """Apply search filters - should only be called AFTER search results have loaded"""
        try:
            # Verify we're on a search results page
            current_url = self.driver.current_url
            if "jobs/search" not in current_url and "jobs?keywords" not in current_url:
                self.logger.warning(f"Not on search results page (URL: {current_url}), may not find filter elements")
            else:
                self.logger.info("Confirmed: On search results page, proceeding with filter application")
            # Always apply Easy Apply filter regardless of parameter (making this the default behavior)
            if True:  # This ensures it always executes
                self.logger.info("[FILTER] Applying Easy Apply filter - this is now mandatory in our workflow")
                easy_apply_button_selectors = [
                    # CURRENT LinkedIn UI (2025) - EXACT PATHS PROVIDED BY USER
                    '//*[@id="searchFilter_applyWithLinkedin"]'
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/div",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[3]/div/button"
                    
                    # Try button, input, and clickable elements within these containers
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/div/button",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/button",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/div/input",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/input",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/div/label",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/label",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]//button",
                    "/html/body/div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]//*[contains(text(), 'Easy Apply')]",
                    
                    # Relative variations of the exact paths
                    "//div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]/div",
                    "//div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]",
                    "//div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]//button",
                    "//div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]//input",
                    "//div[6]/div[3]/div[4]/section/div/section/div/div/div/ul/li[7]//*[contains(text(), 'Easy Apply')]",
                    
                    # More flexible variations focusing on li[7] structure
                    "//section//div//section//div//div//div//ul//li[7]",
                    "//section//div//section//div//div//div//ul//li[7]//button",
                    "//section//div//section//div//div//div//ul//li[7]//input",
                    "//section//div//section//div//div//div//ul//li[7]//*[contains(text(), 'Easy Apply')]",
                    
                    # Generic Easy Apply detection (fallback)
                    "//button[contains(@aria-label, 'Easy Apply')]",
                    "//button[contains(text(), 'Easy Apply')]",
                    "//input[contains(@aria-label, 'Easy Apply')]",
                    "//label[contains(text(), 'Easy Apply')]",
                    "//span[contains(text(), 'Easy Apply')]/parent::*",
                    "//div[contains(text(), 'Easy Apply')]",
                    
                    # Legacy paths for backward compatibility
                    "/html/body/div[6]/div[3]/div[3]/section/div/div/div[1]/div/ul/li[5]/div/button",
                    "/html/body/div[6]/div[3]/div[3]/section/div/div/div[1]/div/ul/li[6]/div/button",
                    "/html/body/div[6]/div[3]/div[3]/section/div/div/div[1]/div/ul/li[8]/div/button"
                ]
            
            filter_applied = False
            for i, selector in enumerate(easy_apply_button_selectors):
                try:
                    self.logger.info(f"[SEARCH] [{i+1}/{len(easy_apply_button_selectors)}] Trying: {selector[:80]}{'...' if len(selector) > 80 else ''}")
                    easy_apply_buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    if len(easy_apply_buttons) > 0:
                        self.logger.info(f"   [FOUND] Found {len(easy_apply_buttons)} element(s) with this selector")
                    else:
                        self.logger.debug(f"   [NONE] No elements found")
                        continue
                    
                    for j, element in enumerate(easy_apply_buttons):
                        try:
                            if element.is_displayed():
                                element_text = element.text.strip()
                                element_tag = element.tag_name.lower()
                                aria_label = element.get_attribute('aria-label') or ''
                                class_attr = element.get_attribute('class') or ''
                                is_pressed = element.get_attribute('aria-pressed') == 'true'
                                is_checked = element.get_attribute('checked') is not None
                                
                                self.logger.info(f"   Element {j+1}: <{element_tag}> Text='{element_text}', Label='{aria_label[:30]}', Class='{class_attr[:30]}', Pressed={is_pressed}, Checked={is_checked}")
                                
                                # Check if this looks like an Easy Apply filter element
                                is_easy_apply = (
                                    'easy apply' in element_text.lower() or
                                    'easy apply' in aria_label.lower() or
                                    'easy apply' in class_attr.lower() or
                                    # If no text but it's in the right position (li[7])
                                    ('li[7]' in selector and not element_text) or
                                    # Check for filter-related classes
                                    'filter' in class_attr.lower()
                                )
                                
                                if is_easy_apply:
                                    # Check if already active/pressed/checked
                                    already_active = is_pressed or is_checked
                                    
                                    if not already_active:
                                        self.logger.info(f"   [ACTIVATE] ACTIVATING Easy Apply filter on <{element_tag}> element...")
                                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                                        self.random_delay(1, 2)
                                        
                                        # Try different interaction methods based on element type
                                        try:
                                            if element_tag in ['button', 'div', 'span', 'label']:
                                                self.safe_click(element)
                                            elif element_tag == 'input':
                                                # For input elements, try clicking or setting checked
                                                input_type = element.get_attribute('type') or 'text'
                                                if input_type in ['checkbox', 'radio']:
                                                    if not element.is_selected():
                                                        element.click()
                                                else:
                                                    element.click()
                                            else:
                                                # For any other element, try clicking
                                                self.safe_click(element)
                                                
                                            self.logger.info("[SUCCESS] Easy Apply filter element clicked successfully!")
                                            filter_applied = True
                                            self.random_delay(3, 5)  # Wait for filter to apply
                                            
                                            # Verify the filter stayed active
                                            try:
                                                final_is_pressed = element.get_attribute('aria-pressed') == 'true'
                                                final_is_checked = element.get_attribute('checked') is not None
                                                if final_is_pressed or final_is_checked:
                                                    self.logger.info("[VERIFIED] Easy Apply filter confirmed ACTIVE")
                                                else:
                                                    self.logger.info("[UNCLEAR] Filter clicked but status unclear (may still be working)")
                                            except:
                                                self.logger.info("[APPLIED] Filter applied but cannot verify status")
                                            break
                                        except Exception as click_error:
                                            self.logger.warning(f"Failed to interact with element: {str(click_error)}")
                                            continue
                                    else:
                                        self.logger.info("[ACTIVE] Easy Apply filter is already ACTIVE")
                                        filter_applied = True
                                        break
                                else:
                                    self.logger.debug(f"   [SKIP] Element doesn't appear to be Easy Apply filter")
                                    
                        except Exception as e:
                            self.logger.debug(f"   Error checking button {j+1}: {str(e)}")
                            continue
                    
                    if filter_applied:
                        self.logger.info(f"[SUCCESS] Easy Apply filter successfully applied using selector {i+1}")
                        break
                        
                except NoSuchElementException:
                    self.logger.debug(f"   No elements found with selector {i+1}")
                    continue
                except Exception as e:
                    self.logger.debug(f"   Error with selector {i+1}: {str(e)}")
                    continue
            
            # Additional verification - check if any non-Easy Apply jobs are visible
            if filter_applied:
                try:
                    self.random_delay(2, 3)
                    # Look for any "Apply" buttons that are NOT "Easy Apply"
                    non_easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Apply') and not(contains(., 'Easy Apply'))]")
                    if non_easy_apply_buttons:
                        self.logger.warning(f"⚠️ Found {len(non_easy_apply_buttons)} non-Easy Apply buttons - filter may not be working properly")
                        # Try to reapply the filter
                        self.logger.info("🔄 Reapplying Easy Apply filter...")
                        self.random_delay(2, 3)
                    else:
                        self.logger.info(" Confirmed: No non-Easy Apply buttons visible - filter working correctly")
                except Exception as e:
                    self.logger.debug(f"Error verifying filter: {str(e)}")
            
            if not filter_applied:
                self.logger.warning("[WARNING] Could not find or activate Easy Apply filter - continuing anyway")
                self.logger.info("Job search will proceed but may include non-Easy Apply jobs")
            else:
                # Log page state after successful filter application
                current_url = self.driver.current_url
                self.logger.info(f"[URL] Page URL after filter: {current_url}")
                
                # Check if Easy Apply is in the URL (common indicator)
                if 'easy%20apply' in current_url.lower() or 'easyapply' in current_url.lower():
                    self.logger.info("[CONFIRMED] URL confirms Easy Apply filter is active")
                
                # Wait a bit more for the page to fully update
                self.random_delay(2, 3)
                self.logger.info("[SUCCESS] Easy Apply filter is now active - all jobs should be Easy Apply only")
                self.easy_apply_filter_applied = True  # Mark filter as applied
            
            # Apply date filter (e.g., past week, past month)
            if filters.get('date_posted'):
                date_filter = filters['date_posted']
                date_button_selectors = [
                    f"//button[contains(text(), '{date_filter}')]",
                    f"//button[contains(@aria-label, '{date_filter}')]",
                    f"//div[contains(@class, 'search-reusables__filter')]//button[contains(text(), '{date_filter}')]"
                ]
                
                for selector in date_button_selectors:
                    try:
                        date_button = self.driver.find_element(By.XPATH, selector)
                        if date_button.is_displayed():
                            self.safe_click(date_button)
                            self.logger.info(f"Applied date filter: {date_filter}")
                            self.random_delay(1, 2)
                            break
                    except NoSuchElementException:
                        continue
                
        except Exception as e:
            self.logger.warning(f"Could not apply some filters: {str(e)}")
    
    def _get_job_cards(self):
        """Get job cards from search results"""
        try:
            # Updated selectors for LinkedIn 2024/2025
            selectors_to_try = [
                "//li[contains(@class, 'scaffold-layout__list-item')]",
                "//li[contains(@class, 'jobs-search-results__list-item')]",
                "//div[contains(@class, 'scaffold-layout__list-container')]//li",
                "//ul[contains(@class, 'scaffold-layout__list')]//li",
                "//main//ul//li[contains(@class, 'ember-view')]",
                "//div[contains(@class, 'jobs-search-results-list')]//li",
                "//li[contains(@class, 'ember-view') and .//a[contains(@href, '/jobs/view/')]]",
                "//div[contains(@class, 'job-search-card')]",
                "//div[contains(@class, 'base-card')]",
                "//div[contains(@data-entity-urn, 'job')]",
                "/html/body/div[6]/div[3]/div[3]/div/div[2]/main/div/div[2]/div[1]",
                "//main//li[contains(@class, 'ember-view')]"
            ]
            
            for selector in selectors_to_try:
                try:
                    job_cards = self.driver.find_elements(By.XPATH, selector)
                    if job_cards and len(job_cards) > 0:
                        self.logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                        return job_cards
                except Exception as e:
                    self.logger.debug(f"Selector failed: {selector} - {str(e)}")
                    continue
            
            self.logger.warning("No job cards found with any selector")
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting job cards: {str(e)}")
            return []
    
    def extract_job_details(self, job_element):
        """Extract detailed job information from LinkedIn job listing"""
        try:
            # Check if element is stale and re-find it if necessary
            try:
                # Test if element is still attached to DOM
                job_element.is_displayed()
            except StaleElementReferenceException:
                self.logger.warning("Job element is stale, trying to re-find...")
                # Try to re-find the element by refreshing the job list
                self.random_delay(2, 3)
                jobs = self.driver.find_elements(By.XPATH, "//main//li[contains(@class, 'ember-view')]")
                if jobs:
                    job_element = jobs[0]  # Use first available job element
                else:
                    self.logger.error("Could not re-find job elements")
                    return None
            
            job_details = {
                'job_title': '',
                'company_name': '',
                'location': '',
                'platform_job_id': '',
                'job_url': '',
                'job_description': '',
                'salary': '',
                'platform': 'linkedin',
                'requirements': ''
            }
            
            # Extract job title with 2024/2025 LinkedIn selectors
            title_selectors = [
                ".//div[contains(@class, 'artdeco-entity-lockup__title')]",
                ".//div[contains(@class, 'job-card-job-posting-card-wrapper__title')]",
                ".//strong",  # Title is inside a strong tag
                ".//a[contains(@class, 'job-card-list__title')]",
                ".//a[contains(@class, 'job-card-container__link')]",
                ".//a[contains(@href, '/jobs/view/')]",
                ".//h3//a"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = job_element.find_element(By.XPATH, selector)
                    job_details['job_title'] = title_element.text.strip()
                    
                    # Try to get URL from different attributes
                    job_url = title_element.get_attribute('href')
                    if not job_url:
                        # If not from title element, look for main link in job card
                        try:
                            main_link = job_element.find_element(By.XPATH, ".//a[contains(@class, 'job-card-job-posting-card-wrapper__card-link')]")
                            job_url = main_link.get_attribute('href')
                        except:
                            pass
                    
                    job_details['job_url'] = job_url or ''
                    
                    # Extract job ID from URL or data attribute
                    if job_url:
                        job_id_match = re.search(r'currentJobId=(\d+)', job_url)
                        if job_id_match:
                            job_details['platform_job_id'] = job_id_match.group(1)
                    
                    # Also try to get job ID from data attribute
                    if not job_details['platform_job_id']:
                        try:
                            job_data_element = job_element.find_element(By.XPATH, ".//*[@data-job-id]")
                            job_details['platform_job_id'] = job_data_element.get_attribute('data-job-id')
                        except:
                            pass
                    
                    if job_details['job_title']:  # If we got a title, consider this successful
                        break
                        
                except NoSuchElementException:
                    continue
            
            if not job_details['job_title']:
                self.logger.warning("Could not extract job title with any selector")
            
            # Extract company name with 2024/2025 LinkedIn selectors
            company_selectors = [
                ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]",
                ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]//div",
                ".//a[contains(@class, 'job-card-container__company-name')]",
                ".//span[contains(@class, 'job-card-container__company-name')]",
                ".//h4//a",
                ".//div[contains(@class, 'job-card-container__primary-description')]//a",
                ".//span[contains(@class, 'base-search-card__subtitle')]",
                ".//a[contains(@data-control-name, 'job_card_company_link')]"
            ]
            
            for selector in company_selectors:
                try:
                    company_element = job_element.find_element(By.XPATH, selector)
                    job_details['company_name'] = company_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            if not job_details['company_name']:
                self.logger.warning("Could not extract company name with any selector")
            
            # Extract location with 2024/2025 LinkedIn selectors
            location_selectors = [
                ".//div[contains(@class, 'artdeco-entity-lockup__caption')]",
                ".//div[contains(@class, 'artdeco-entity-lockup__caption')]//div",
                ".//span[contains(@class, 'job-card-container__metadata-item')]",
                ".//div[contains(@class, 'job-card-container__metadata')]//span",
                ".//span[contains(@class, 'base-search-card__info')]",
                ".//div[contains(@class, 'base-search-card__info')]//span"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = job_element.find_element(By.XPATH, selector)
                    location_text = location_element.text.strip()
                    # Filter out non-location metadata (like time posted)
                    if location_text and not any(word in location_text.lower() for word in ['ago', 'hour', 'day', 'week', 'month', 'just now']):
                        job_details['location'] = location_text
                        break
                except NoSuchElementException:
                    continue
            
            if not job_details['location']:
                self.logger.warning("Could not extract location with any selector")
            
            # Click on job to get more details
            self._get_detailed_job_info(job_element, job_details)
            
            return job_details
            
        except StaleElementReferenceException as e:
            self.logger.error(f"Stale element reference in job details extraction: {str(e)}")
            # Try one more time with a fresh search
            try:
                self.random_delay(2, 3)
                jobs = self.driver.find_elements(By.XPATH, "//main//li[contains(@class, 'ember-view')]")
                if jobs:
                    return self.extract_job_details(jobs[0])
            except Exception:
                pass
            return None
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return None
    
    def extract_job_details_from_panel(self):
        """Extract job details from the right panel after clicking a job card"""
        try:
            # Initialize job details structure
            job_details = {
                'job_title': '',
                'company_name': '',
                'location': '',
                'platform_job_id': '',
                'job_url': '',
                'job_description': '',
                'salary': '',
                'platform': 'linkedin',
                'requirements': ''
            }
            
            # Wait for the job details panel to load
            self.random_delay(2, 3)
            
            # Extract job title from the right panel
            panel_title_selectors = [
                "//div[contains(@class, 'jobs-unified-top-card__job-title')]//h1",
                "//div[contains(@class, 'job-details-jobs-unified-top-card__job-title')]//h1",
                "//div[contains(@class, 'jobs-unified-top-card')]//h1",
                "//main//section//h1",
                "//h1[contains(@class, 'job-title')]",
                "//div[contains(@class, 'jobs-unified-top-card')]//a",
                "//div[contains(@class, 'jobs-details__main-content')]//h1"
            ]
            
            for selector in panel_title_selectors:
                try:
                    title_element = self.driver.find_element(By.XPATH, selector)
                    job_details['job_title'] = title_element.text.strip()
                    if job_details['job_title']:
                        self.logger.info(f" Found job title from panel: {job_details['job_title']}")
                        break
                except NoSuchElementException:
                    continue
            
            # Extract company name from the right panel
            panel_company_selectors = [
                "//div[contains(@class, 'jobs-unified-top-card__company-name')]//a",
                "//div[contains(@class, 'job-details-jobs-unified-top-card__company-name')]//a",
                "//div[contains(@class, 'jobs-unified-top-card')]//span[contains(@class, 'jobs-unified-top-card__subtitle-primary-grouping')]//a",
                "//main//section//span//a[contains(@data-control-name, 'company_link')]",
                "//a[contains(@data-control-name, 'job_details_topcard_company_url')]",
                "//div[contains(@class, 'jobs-unified-top-card')]//h3//span//a"
            ]
            
            for selector in panel_company_selectors:
                try:
                    company_element = self.driver.find_element(By.XPATH, selector)
                    job_details['company_name'] = company_element.text.strip()
                    if job_details['company_name']:
                        self.logger.info(f" Found company from panel: {job_details['company_name']}")
                        break
                except NoSuchElementException:
                    continue
            
            # Extract location from the right panel
            panel_location_selectors = [
                "//div[contains(@class, 'jobs-unified-top-card__primary-description')]//span[contains(@class, 'tvm__text')]",
                "//div[contains(@class, 'jobs-unified-top-card')]//span[contains(@class, 'jobs-unified-top-card__bullet')]",
                "//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description-container')]//span",
                "//main//section//div[contains(@class, 'job-details-jobs-unified-top-card')]//span[2]",
                "//div[contains(@class, 'jobs-unified-top-card')]//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description')]//span"
            ]
            
            for selector in panel_location_selectors:
                try:
                    location_elements = self.driver.find_elements(By.XPATH, selector)
                    for location_element in location_elements:
                        location_text = location_element.text.strip()
                        # Filter out non-location text
                        if location_text and not any(word in location_text.lower() for word in ['ago', 'hour', 'day', 'week', 'month', 'just now', 'applicant', 'employee', 'reposted']):
                            if any(location_word in location_text.lower() for location_word in ['mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'india', 'remote', 'on-site', 'hybrid']):
                                job_details['location'] = location_text
                                self.logger.info(f" Found location from panel: {job_details['location']}")
                                break
                    if job_details['location']:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract job ID from current URL
            current_url = self.driver.current_url
            job_id_match = re.search(r'currentJobId=(\d+)', current_url)
            if job_id_match:
                job_details['platform_job_id'] = job_id_match.group(1)
                job_details['job_url'] = current_url
                self.logger.info(f" Found job ID from URL: {job_details['platform_job_id']}")
            
            # Try to extract job description (optional)
            description_selectors = [
                "//div[contains(@class, 'jobs-description-content')]//div[contains(@class, 'jobs-description-content__text')]",
                "//div[contains(@class, 'jobs-box__html-content')]",
                "//div[contains(@class, 'job-details-jobs-unified-top-card__job-description')]//div",
                "//section[contains(@class, 'jobs-description')]//div"
            ]
            
            for selector in description_selectors:
                try:
                    desc_element = self.driver.find_element(By.XPATH, selector)
                    job_details['job_description'] = desc_element.text.strip()[:1000]  # Limit to first 1000 chars
                    if job_details['job_description']:
                        self.logger.info(f" Found job description from panel (length: {len(job_details['job_description'])})")
                        break
                except NoSuchElementException:
                    continue
            
            # Log what we extracted
            self.logger.info(f"📋 Extracted from panel - Title: '{job_details['job_title']}', Company: '{job_details['company_name']}', Location: '{job_details['location']}', ID: '{job_details['platform_job_id']}'")
            
            return job_details if job_details['job_title'] else None
            
        except Exception as e:
            self.logger.error(f"Error extracting job details from panel: {str(e)}")
            return None
    
    def _get_detailed_job_info(self, job_element, job_details):
        """Get detailed job information by clicking on the job"""
        try:
            # Find and click job title link with multiple attempts
            title_link = None
            title_link_selectors = [
                ".//a[contains(@class, 'job-card-list__title')]",
                ".//a[contains(@class, 'job-card-container__link')]",
                ".//a[contains(@href, '/jobs/view/')]",
                ".//div[contains(@class, 'artdeco-entity-lockup__title')]//a",
                ".//strong//a",
                ".//h3//a"
            ]
            
            for selector in title_link_selectors:
                try:
                    title_link = job_element.find_element(By.XPATH, selector)
                    if title_link and title_link.is_displayed() and title_link.is_enabled():
                        break
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
            
            if title_link:
                try:
                    self.safe_click(title_link)
                    self.random_delay(2, 3)
                except StaleElementReferenceException:
                    self.logger.warning("Title link became stale, skipping detailed job info")
                    return
            else:
                self.logger.warning("Could not find clickable title link")
                return
            
            # Wait for job details to load
            try:
                job_description = self.wait_for_element(
                    (By.XPATH, "//div[contains(@class, 'jobs-description-content__text')]" ), timeout=5)
                job_details['job_description'] = job_description.text.strip()
            except TimeoutException:
                self.logger.warning("Could not load detailed job description")
            
            # Try to extract salary information
            try:
                salary_element = self.driver.find_element(
                    By.XPATH, "//span[contains(@class, 'jobs-details-top-card__salary-info')]")
                job_details['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                pass  # Salary not always available
            
        except Exception as e:
            self.logger.warning(f"Could not get detailed job info: {str(e)}")
            return job_details
    
    def _match_job_to_preferences(self, job_details, user_preferences, user_skills):
        """Match job details to user preferences - prioritize job title matching"""
        try:
            self.logger.info(f"\n=== MATCHING JOB: {job_details.get('job_title', 'N/A')} ===")
            
            # Check job title - if it matches, apply regardless of other criteria
            preferred_titles = [title.lower() for title in user_preferences.get_preferred_job_titles()]
            job_title_lower = job_details['job_title'].lower()
            
            self.logger.info(f"Job title (lowercase): '{job_title_lower}'")
            self.logger.info(f"Preferred titles: {preferred_titles}")
            
            # Method 1: Exact phrase matching (most accurate)
            for preferred_title in preferred_titles:
                if preferred_title in job_title_lower or job_title_lower in preferred_title:
                    self.logger.info(f" EXACT TITLE MATCH: '{preferred_title}' found in '{job_title_lower}'")
                    self.logger.info(f" JOB APPROVED: Title matches user preference - applying regardless of other criteria")
                    return True
            
            # Method 2: Word-based matching with lower threshold
            preferred_words = {word for title in preferred_titles for word in title.split() if len(word) > 2}
            job_title_words = {word for word in job_title_lower.split() if len(word) > 2}
            word_matches = preferred_words.intersection(job_title_words)
            
            self.logger.info(f"Preferred words (>2 chars): {preferred_words}")
            self.logger.info(f"Job title words (>2 chars): {job_title_words}")
            self.logger.info(f"Word matches found: {word_matches} (count: {len(word_matches)})")
            
            # If we have at least 1 significant word match, consider it a match
            if len(word_matches) >= 1:
                self.logger.info(f" WORD-BASED TITLE MATCH: {len(word_matches)} word(s) matched")
                self.logger.info(f" JOB APPROVED: Title matches user preference - applying regardless of other criteria")
                return True
            
            # Method 3: Partial word matching (most lenient)
            for preferred_title in preferred_titles:
                for job_word in job_title_words:
                    for pref_word in preferred_title.split():
                        if len(pref_word) > 3 and (pref_word in job_word or job_word in pref_word):
                            self.logger.info(f" PARTIAL TITLE MATCH: '{pref_word}' matches '{job_word}'")
                            self.logger.info(f" JOB APPROVED: Title matches user preference - applying regardless of other criteria")
                            return True
            
            # If no title match found, reject the job
            self.logger.info(f" NO TITLE MATCH: Job title '{job_details['job_title']}' doesn't match any preferred titles")
            self.logger.info(f" JOB REJECTED: Title doesn't match user preferences")
            return False
            
        except Exception as e:
            self.logger.error(f"Error matching job to preferences: {str(e)}")
            return False

    def process_jobs_sequentially(self, user_preferences=None, user_skills=None, user_data=None, max_applications=10):
        """Process jobs sequentially - click each job card, extract details, and apply if suitable"""
        try:
            applications_made = 0
            
            self.logger.info(f"[START] STARTING SEQUENTIAL JOB PROCESSING - Target: {max_applications} applications")
            
            while applications_made < max_applications:
                # Get current job cards
                job_cards = self._get_job_cards()
                
                if not job_cards:
                    self.logger.info("No job cards found")
                    break
                
                self.logger.info(f"📋 Found {len(job_cards)} job cards, currently at index {self.current_job_index}")
                
                # Check if we've processed all available jobs
                if self.current_job_index >= len(job_cards):
                    self.logger.info("All available jobs processed, trying to load more...")
                    # Try to load more jobs
                    if self.scroll_to_load_more_jobs():
                        job_cards = self._get_job_cards()
                        self.logger.info(f"📋 After scrolling, found {len(job_cards)} job cards")
                    
                    # If still no new jobs, we're done
                    if self.current_job_index >= len(job_cards):
                        self.logger.info(" No more jobs available")
                        break
                
                # Get current job card
                current_job = job_cards[self.current_job_index]
                self.logger.info(f"\n🎯 PROCESSING JOB {self.current_job_index + 1}/{len(job_cards)}")
                
                # Process this specific job
                result = self.apply_to_job(current_job, user_preferences, user_skills, user_data)
                
                if result['success']:
                    applications_made += 1
                    self.logger.info(f" Successfully applied to job {self.current_job_index + 1}. Total applications: {applications_made}")
                else:
                    self.logger.info(f"⚠️ Skipped job {self.current_job_index + 1}: {result.get('error', 'Unknown error')}")
                
                # Move to next job
                self.current_job_index += 1
                
                # Small delay between jobs
                self.random_delay(2, 4)
            
            self.logger.info(f"[COMPLETE] JOB PROCESSING COMPLETED. Total applications made: {applications_made}/{max_applications}")
            return {'applications_made': applications_made, 'success': True}
            
        except Exception as e:
            self.logger.error(f" Error in sequential job processing: {str(e)}")
            return {'success': False, 'error': str(e), 'applications_made': applications_made}

    def apply_to_job(self, job_element_or_index, user_preferences=None, user_skills=None, user_data=None):
        """Apply to a job on LinkedIn if it matches user preferences"""
        try:
            self.logger.info("\n----------------------------------------")
            self.logger.info("Starting application process for a new job")
            self.logger.info("----------------------------------------")
            
            # Handle both job element and job index
            if isinstance(job_element_or_index, int):
                # If we get an index, get fresh job cards and use the index
                job_cards = self._get_job_cards()
                if job_element_or_index >= len(job_cards):
                    return {'success': False, 'error': 'Job index out of range'}
                job_element = job_cards[job_element_or_index]
            else:
                job_element = job_element_or_index
            
            # Check if element is stale and handle it
            try:
                job_element.is_displayed()  # Test if element is still valid
            except StaleElementReferenceException:
                self.logger.warning("Job element is stale, refreshing job cards...")
                # Refresh job cards and get current job
                job_cards = self._get_job_cards()
                if self.current_job_index < len(job_cards):
                    job_element = job_cards[self.current_job_index]
                else:
                    return {'success': False, 'error': 'Could not refresh stale job element'}
            
            # First click on the job card to load its details in the right panel
            self.logger.info("Clicking on job card to load details...")
            try:
                # Scroll job card into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", job_element)
                self.random_delay(1, 2)
                
                # Try multiple click methods
                clicked = False
                try:
                    job_element.click()
                    clicked = True
                except Exception as e1:
                    try:
                        self.driver.execute_script("arguments[0].click();", job_element)
                        clicked = True
                    except Exception as e2:
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(self.driver).move_to_element(job_element).click().perform()
                            clicked = True
                        except Exception as e3:
                            self.logger.error(f"All click methods failed: {str(e3)}")
                
                if clicked:
                    self.logger.info("Successfully clicked job card")
                    self.random_delay(3, 5)  # Wait for job details to load
                else:
                    self.logger.warning("Could not click job card")
                    return {'success': False, 'error': 'Could not click job card'}
                    
            except Exception as e:
                self.logger.error(f"Error clicking job card: {str(e)}")
                return {'success': False, 'error': f'Could not click job card: {str(e)}'}
            
            # Now extract job details from the right panel (detailed view)
            job_details = self.extract_job_details_from_panel()
            if not job_details or not job_details.get('job_title'):
                self.logger.warning("Could not extract job details from panel, trying from card")
                job_details = self.extract_job_details(job_element)
                
            if not job_details:
                return {'success': False, 'error': 'Could not extract job details'}
            
            # Store current job details for AI context
            self._current_job_details = job_details

            # Match job details against user preferences
            if not self._match_job_to_preferences(job_details, user_preferences, user_skills):
                return {'success': False, 'error': 'Job does not match user preferences'}

            # Check if already applied
            job_id = job_details.get('platform_job_id', f"job_{self.current_job_index}")
            if job_id in self.applied_jobs:
                return {'success': False, 'error': 'Already applied to this job'}
            
            # Now that we have job details loaded, look for Easy Apply button
            self.logger.info(f"🔍 SEARCHING FOR EASY APPLY BUTTON for: {job_details.get('job_title', 'Unknown Job')}")
            self.logger.info(f"Current URL: {self.driver.current_url}")
            
            # Wait a bit for the job details page to fully load
            self.random_delay(2, 4)
            
            # Comprehensive list of Easy Apply button selectors
            easy_apply_selectors = [
                "//button[contains(@class, 'jobs-apply-button') and contains(., 'Easy Apply')]",
                "//button[contains(., 'Easy Apply')]",
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//div[contains(@class, 'jobs-apply-button')]//button[contains(., 'Easy Apply')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Easy Apply')]",
                "//button[contains(@data-control-name, 'jobdetails_topcard_inapply')]",
                "//button[contains(@class, 'jobs-apply-button')]",
                "//button[contains(@class, 'artdeco-button') and contains(., 'Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Easy Apply')]",
                "//button[@data-control-name='jobdetails_topcard_inapply']",
                "//button[contains(@class, 'jobs-s-apply') and contains(., 'Easy Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card')]//button[contains(., 'Easy Apply')]"
            ]
            
            self.logger.info(f"Trying {len(easy_apply_selectors)} different selectors...")
            
            easy_apply_button = None
            found_selector = None
            
            for i, selector in enumerate(easy_apply_selectors):
                try:
                    self.logger.info(f"🔍 Trying selector {i+1}: {selector}")
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"   Found {len(buttons)} buttons with this selector")
                    
                    for j, button in enumerate(buttons):
                        try:
                            button_text = button.text.strip()
                            is_displayed = button.is_displayed()
                            is_enabled = button.is_enabled()
                            
                            self.logger.info(f"   Button {j+1}: Text='{button_text}', Displayed={is_displayed}, Enabled={is_enabled}")
                            
                            if is_displayed and is_enabled and ('easy apply' in button_text.lower() or 'apply' in button_text.lower()):
                                easy_apply_button = button
                                found_selector = selector
                                self.logger.info(f" FOUND EASY APPLY BUTTON: '{button_text}' using selector {i+1}")
                                break
                        except Exception as btn_e:
                            self.logger.warning(f"   Error checking button {j+1}: {str(btn_e)}")
                    
                    if easy_apply_button:
                        break
                        
                except NoSuchElementException:
                    self.logger.info(f"    No elements found with this selector")
                    continue
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Error with selector {i+1}: {str(e)}")
                    continue
            
            if easy_apply_button:
                if easy_apply_button.is_enabled():
                    self.logger.info("🖱️ CLICKING EASY APPLY BUTTON...")
                    
                    # Scroll to button and ensure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", easy_apply_button)
                    self.random_delay(1, 2)
                    
                    # Try multiple click methods with focus management
                    clicked = False
                    try:
                        # Clear any active input focus first to prevent search bar contamination
                        self.driver.execute_script("document.activeElement.blur();")
                        self.random_delay(0.5, 1)
                        
                        # Method 1: JavaScript click (most reliable for modal buttons)
                        self.driver.execute_script("arguments[0].click();", easy_apply_button)
                        clicked = True
                        self.logger.info(" CLICKED EASY APPLY BUTTON (JavaScript click)")
                    except Exception as e1:
                        self.logger.warning(f"JavaScript click failed: {str(e1)}")
                        try:
                            # Method 2: Regular click
                            easy_apply_button.click()
                            clicked = True
                            self.logger.info(" CLICKED EASY APPLY BUTTON (regular click)")
                        except Exception as e2:
                            self.logger.warning(f"Regular click failed: {str(e2)}")
                            try:
                                # Method 3: ActionChains click
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(self.driver).move_to_element(easy_apply_button).click().perform()
                                clicked = True
                                self.logger.info(" CLICKED EASY APPLY BUTTON (ActionChains click)")
                            except Exception as e3:
                                self.logger.error(f"All click methods failed: {str(e3)}")
                    
                    if clicked:
                        self.random_delay(3, 5)  # Wait for modal to appear
                        
                        # Handle application process with user data
                        application_result = self._handle_application_process(user_data)
                        
                        if application_result['success']:
                            self.applied_jobs.add(job_id)
                            self.successful_applications += 1  # Increment successful applications counter
                            self.logger.info(f" SUCCESSFULLY APPLIED to {job_details['job_title']} at {job_details['company_name']}")
                            self.logger.info(f"📊 DAILY APPLICATION COUNT: {self.successful_applications}/{self.daily_application_limit} applications used")
                            
                            # Wait a moment before moving to next job
                            self.random_delay(2, 3)
                            
                            return {
                                'success': True,
                                'job_details': job_details,
                                'application_method': 'easy_apply'
                            }
                        else:
                            self.logger.warning(f" APPLICATION FAILED for {job_details['job_title']}: {application_result.get('error', 'Unknown error')}")
                            return {
                                'success': False,
                                'error': application_result.get('error', 'Application process failed'),
                                'job_details': job_details
                            }
                    else:
                        return {
                            'success': False,
                            'error': 'Could not click Easy Apply button',
                            'job_details': job_details
                        }
                else:
                    return {
                        'success': False,
                        'error': 'Easy Apply button not available',
                        'job_details': job_details
                    }
            else:
                # No Easy Apply button found - look for other application methods
                self.logger.info(f" NO EASY APPLY FOUND for: {job_details.get('job_title', 'Unknown Job')}")
                
                # Check for regular "Apply" buttons or external application links
                fallback_applied = self._try_fallback_application_methods(job_details)
                
                if fallback_applied:
                    return {
                        'success': True,
                        'job_details': job_details,
                        'application_method': 'external_apply'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No Easy Apply available - requires external application',
                        'job_details': job_details,
                        'skip_reason': 'non_easy_apply'
                    }
                
        except Exception as e:
            self.logger.error(f"Error applying to job: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _try_fallback_application_methods(self, job_details):
        """Try fallback application methods for jobs without Easy Apply"""
        try:
            self.logger.info(f"🔄 ATTEMPTING FALLBACK APPLICATION METHODS...")
            
            # Look for regular "Apply" buttons
            regular_apply_selectors = [
                "//button[contains(., 'Apply') and not(contains(., 'Easy Apply'))]",
                "//a[contains(., 'Apply') and not(contains(., 'Easy Apply'))]",
                "//button[contains(@class, 'jobs-apply-button') and not(contains(., 'Easy Apply'))]",
                "//a[contains(@class, 'jobs-apply-button') and not(contains(., 'Easy Apply'))]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Apply') and not(contains(., 'Easy Apply'))]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//a[contains(., 'Apply') and not(contains(., 'Easy Apply'))]"
            ]
            
            for selector in regular_apply_selectors:
                try:
                    apply_elements = self.driver.find_elements(By.XPATH, selector)
                    for apply_element in apply_elements:
                        try:
                            if apply_element.is_displayed() and apply_element.is_enabled():
                                apply_text = apply_element.text.strip()
                                self.logger.info(f"🔍 Found regular apply button/link: '{apply_text}'")
                                
                                # Check if it's an external link
                                if apply_element.tag_name == 'a':
                                    href = apply_element.get_attribute('href')
                                    if href and 'linkedin.com' not in href:
                                        self.logger.info(f"📎 EXTERNAL APPLICATION DETECTED: {href}")
                                        self.logger.info(f"ℹ️ Job requires external application to: {href}")
                                        
                                        # Log the job details for manual follow-up
                                        self.logger.info(f"📝 JOB SAVED FOR MANUAL APPLICATION:")
                                        self.logger.info(f"   Title: {job_details.get('job_title', 'N/A')}")
                                        self.logger.info(f"   Company: {job_details.get('company_name', 'N/A')}")
                                        self.logger.info(f"   Location: {job_details.get('location', 'N/A')}")
                                        self.logger.info(f"   External URL: {href}")
                                        
                                        # For now, we'll consider this a 'partial success' since we found the application method
                                        # In a real implementation, you might want to save this to a database or file
                                        return False  # Don't auto-apply to external sites
                                else:
                                    # Try clicking the button if it's not external
                                    try:
                                        self.logger.info(f"🖱️ Clicking regular apply button: '{apply_text}'")
                                        self.safe_click(apply_element)
                                        self.random_delay(3, 5)
                                        
                                        # Check if this opened an Easy Apply modal or external site
                                        # If Easy Apply modal opened, handle it
                                        try:
                                            easy_apply_modal = self.driver.find_element(By.XPATH, "//div[contains(@class, 'jobs-easy-apply-modal')]")
                                            if easy_apply_modal.is_displayed():
                                                self.logger.info(" Regular Apply button opened Easy Apply modal - proceeding...")
                                                return True  # This will be handled by the main application process
                                        except NoSuchElementException:
                                            pass
                                        
                                        # Check if we're redirected to external site
                                        current_url = self.driver.current_url
                                        if 'linkedin.com' not in current_url:
                                            self.logger.info(f"🌐 REDIRECTED TO EXTERNAL SITE: {current_url}")
                                            self.logger.info(f"📝 JOB REQUIRES EXTERNAL APPLICATION")
                                            # Navigate back to LinkedIn
                                            self.driver.back()
                                            return False
                                        
                                        return True  # Successfully initiated application process
                                        
                                    except Exception as e:
                                        self.logger.warning(f"Error clicking regular apply button: {str(e)}")
                                        continue
                                        
                        except Exception as e:
                            self.logger.warning(f"Error checking apply element: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"Error with apply selector: {str(e)}")
                    continue
            
            # Look for "Apply on company website" or similar links
            external_apply_selectors = [
                "//a[contains(., 'Apply on company website')]",
                "//a[contains(., 'Apply on')]",
                "//a[contains(@href, 'apply') and not(contains(@href, 'linkedin.com'))]",
                "//button[contains(., 'company website')]",
                "//a[contains(., 'View job')]"
            ]
            
            for selector in external_apply_selectors:
                try:
                    external_links = self.driver.find_elements(By.XPATH, selector)
                    for link in external_links:
                        if link.is_displayed():
                            link_text = link.text.strip()
                            href = link.get_attribute('href')
                            self.logger.info(f"🔍 Found external application link: '{link_text}' -> {href}")
                            
                            # Log for manual follow-up
                            self.logger.info(f"📝 EXTERNAL APPLICATION REQUIRED:")
                            self.logger.info(f"   Job: {job_details.get('job_title', 'N/A')} at {job_details.get('company_name', 'N/A')}")
                            self.logger.info(f"   Apply at: {href}")
                            
                            return False  # Don't auto-navigate to external sites
                            
                except Exception as e:
                    self.logger.warning(f"Error checking external link: {str(e)}")
                    continue
            
            self.logger.info(" No suitable application methods found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in fallback application methods: {str(e)}")
            return False
    
    def _handle_application_process(self, user_data=None):
        """Handle the multi-step application process with auto-fill"""
        try:
            max_steps = 5  # Reduced to prevent endless loops
            current_step = 0
            
            while current_step < max_steps:
                self.random_delay(2, 4)
                self.logger.info(f"🔄 Application step {current_step + 1}/{max_steps}")
                
                # Check for success first
                if self._check_application_success():
                    self.logger.info(" Application already submitted successfully!")
                    return {'success': True}
                
                # AI-powered form filling if available, otherwise fallback to basic auto-fill
                if user_data:
                    if self.ai_answerer and self.form_parser:
                        # Pass job details from the main context
                        current_job_details = getattr(self, '_current_job_details', {})
                        filled_by_ai = self._ai_fill_application_form(user_data, current_job_details)
                        if not filled_by_ai:
                            # Fallback to basic auto-fill
                            self._auto_fill_application_form(user_data)
                    else:
                        # Basic auto-fill when AI is not available
                        self._auto_fill_application_form(user_data)
                
                # Look for Review button first (some apps have Review -> Submit flow)
                review_found = False
                review_selectors = [
                    "//button[contains(@aria-label, 'Review') and not(@disabled)]",
                    "//button[contains(text(), 'Review') and not(@disabled)]",
                    "//button[contains(text(), 'Review application') and not(@disabled)]",
                    "//button[contains(@class, 'artdeco-button--primary') and contains(text(), 'Review') and not(@disabled)]"
                ]
                
                for selector in review_selectors:
                    try:
                        review_buttons = self.driver.find_elements(By.XPATH, selector)
                        for review_button in review_buttons:
                            if review_button.is_displayed() and review_button.is_enabled():
                                button_text = review_button.text.strip()
                                self.logger.info(f"👁️ FOUND REVIEW BUTTON: '{button_text}' - CLICKING FIRST!")
                                
                                # Scroll to button
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", review_button)
                                self.random_delay(1, 2)
                                
                                # Click review
                                self.safe_click(review_button)
                                review_found = True
                                self.random_delay(2, 3)
                                break
                        if review_found:
                            break
                    except Exception as e:
                        self.logger.debug(f"Review button check failed: {str(e)}")
                        continue
                
                # Look for submit button (higher priority if no review found, or after review)
                submit_found = False
                submit_selectors = [
                    "//button[contains(@aria-label, 'Submit application') and @aria-disabled='false']",
                    "//button[contains(text(), 'Submit application') and not(@disabled)]",
                    "//button[contains(text(), 'Submit') and contains(@class, 'artdeco-button--primary') and not(@disabled)]",
                    "//button[contains(@class, 'jobs-apply-form__submit-button') and not(@disabled)]",
                    "//div[contains(@class, 'jobs-apply-form')]//button[contains(text(), 'Submit')]"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_buttons = self.driver.find_elements(By.XPATH, selector)
                        for submit_button in submit_buttons:
                            if submit_button.is_displayed() and submit_button.is_enabled():
                                button_text = submit_button.text.strip()
                                self.logger.info(f"🎯 FOUND SUBMIT BUTTON: '{button_text}' - CLICKING NOW!")
                                
                                # Scroll to button
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                                self.random_delay(1, 2)
                                
                                # Click submit
                                self.safe_click(submit_button)
                                submit_found = True
                                self.random_delay(3, 5)
                                
                                # Check if application was successful
                                if self._check_application_success():
                                    self.logger.info(" APPLICATION SUBMITTED SUCCESSFULLY!")
                                    return {'success': True}
                                
                                # If not successful, might need more steps
                                break
                        if submit_found:
                            break
                    except Exception as e:
                        self.logger.debug(f"Submit button check failed: {str(e)}")
                        continue
                
                if submit_found or review_found:
                    # If we found and clicked submit or review, wait and check again
                    self.random_delay(2, 3)
                    if self._check_application_success():
                        return {'success': True}
                    # Continue to next iteration without incrementing step
                    # (step will be incremented at the end of the loop if needed)
                
                # Look for next/continue buttons only if no submit or review found
                if not submit_found and not review_found:
                    next_found = False
                    next_selectors = [
                        "//button[contains(@aria-label, 'Continue to next step') and not(@disabled)]",
                        "//button[contains(@aria-label, 'Continue') and not(@disabled)]",
                        "//button[contains(text(), 'Next') and not(@disabled)]",
                        "//button[contains(text(), 'Continue') and not(@disabled)]",
                        "//button[contains(@class, 'artdeco-button--primary') and (contains(text(), 'Next') or contains(text(), 'Continue')) and not(@disabled)]"
                    ]
                    
                    for selector in next_selectors:
                        try:
                            next_buttons = self.driver.find_elements(By.XPATH, selector)
                            for next_button in next_buttons:
                                if next_button.is_displayed() and next_button.is_enabled():
                                    button_text = next_button.text.strip()
                                    self.logger.info(f"➡️ Found next button: '{button_text}' - proceeding to next step")
                                    
                                    # Scroll to button
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                    self.random_delay(1, 2)
                                    
                                    # Click next
                                    self.safe_click(next_button)
                                    next_found = True
                                    current_step += 1
                                    self.random_delay(2, 3)
                                    break
                            if next_found:
                                break
                        except Exception as e:
                            self.logger.debug(f"Next button check failed: {str(e)}")
                            continue
                    
                    if not next_found:
                        # No buttons found, might be done or stuck
                        self.logger.warning("⚠️ No next or submit buttons found. Checking if application completed...")
                        
                        # Final check for success
                        if self._check_application_success():
                            return {'success': True}
                        
                        # Check if we're stuck due to required fields
                        if self._has_required_fields_missing():
                            self.logger.error(" Required fields missing - cannot proceed")
                            self._close_application_modal()
                            return {'success': False, 'error': 'Required form fields not filled'}
                        
                        # If no progress possible, exit
                        self.logger.error(" No way to proceed - application stuck")
                        break
                else:
                    # We clicked submit but it didn't work, try final checks
                    if current_step >= 3:  # If we've tried multiple steps
                        self.logger.warning("⚠️ Multiple steps completed, trying final submit attempts...")
                        if self._try_final_submit():
                            return {'success': True}
                        break
                
                # Increment step at the end if we haven't broken out of the loop
                if not (submit_found or review_found):
                    current_step += 1
            
            # Final attempts
            self.logger.info("🔄 Attempting final submission...")
            if self._try_final_submit():
                return {'success': True}
            
            # Clean exit
            self._close_application_modal()
            return {'success': False, 'error': 'Application process completed but submission unclear'}
            
        except Exception as e:
            self.logger.error(f" Error in application process: {str(e)}")
            self._close_application_modal()
            return {'success': False, 'error': str(e)}
    
    def _close_application_modal(self):
        """Close the application modal if open"""
        try:
            close_button_selectors = [
                "//button[contains(@aria-label, 'Dismiss')]",
                "//button[contains(@aria-label, 'Cancel')]",
                "//button[contains(., 'Close')]"
            ]
            for selector in close_button_selectors:
                try:
                    close_button = self.driver.find_element(By.XPATH, selector)
                    if close_button.is_displayed():
                        self.safe_click(close_button)
                        self.logger.info("Application modal closed successfully.")
                        self.random_delay(2, 3)
                        return True
                except NoSuchElementException:
                    continue
        except Exception as e:
            self.logger.error(f"Error closing application modal: {str(e)}")
        
    def _check_application_success(self):
        """Check if the application was successful with comprehensive detection"""
        try:
            # Enhanced success detection with more indicators
            success_indicators = {
                'done_buttons': [
                    "/html/body/div[4]/div/div/div[3]/button",
                    "/html/body/div[4]/div/div/div[3]/button/span",
                    "//button[contains(text(), 'Done')]",
                    "//button[contains(@aria-label, 'Done')]",
                    "//button[contains(@class, 'artdeco-button--primary') and contains(text(), 'Done')]",
                    "//div[contains(@class, 'artdeco-modal')]//button[contains(text(), 'Done')]",
                    "//div[contains(@class, 'jobs-easy-apply-modal')]//button[contains(text(), 'Done')]",
                    "//button[contains(@data-control-name, 'continue_unify')]",
                    "//button[contains(@data-control-name, 'dismiss_modal')]"
                ],
                'success_messages': [
                    "//h2[contains(text(), 'Application sent')]",
                    "//h3[contains(text(), 'Your application was sent')]",
                    "//div[contains(@class, 'artdeco-toast-message')][contains(., 'Application sent')]",
                    "//span[contains(text(), 'Application submitted successfully')]"
                ],
                'confirmation_elements': [
                    "//div[contains(@class, 'jobs-apply-success')]",
                    "//div[@data-test-modal-id='application-submitted-modal']",
                    "//div[contains(@class, 'application-confirmation')]"
                ]
            }
            
            # Check each type of success indicator
            for indicator_type, selectors in success_indicators.items():
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                self.logger.info(f" SUCCESS DETECTED ({indicator_type}): {element.text[:50]}...")
                                if indicator_type == 'done_buttons' and element.is_enabled():
                                    self.safe_click(element)
                                    self.random_delay(1, 2)
                                return True
                    except:
                        continue
            
            # Original done button detection for backward compatibility
            done_button_selectors = success_indicators['done_buttons']
            
            for selector in done_button_selectors:
                try:
                    done_button = self.driver.find_element(By.XPATH, selector)
                    if done_button.is_displayed() and done_button.is_enabled():
                        self.logger.info(f"🔘 FOUND DONE BUTTON: Clicking to complete application process")
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", done_button)
                        self.random_delay(1, 2)
                        self.safe_click(done_button)
                        self.logger.info(" DONE BUTTON CLICKED - Application process completed")
                        self.random_delay(2, 3)  # Wait for modal to close
                        return True
                except NoSuchElementException:
                    continue
                except Exception as e:
                    self.logger.debug(f"Error with Done button: {str(e)}")
                    continue
            
            # Enhanced success message selectors
            success_messages = [
                "//div[contains(text(), 'Application submitted')]",
                "//div[contains(text(), 'Your application was sent')]",
                "//div[contains(text(), 'Application sent')]", 
                "//div[contains(text(), 'Thank you for applying')]",
                "//h2[contains(., 'You applied')]",
                "//h2[contains(., 'Application submitted')]",
                "//h3[contains(., 'Application submitted')]",
                "//span[contains(., 'successfully applied')]",
                "//span[contains(., 'application submitted')]",
                "//div[contains(@class, 'application-success')]",
                "//div[contains(@class, 'success-message')]",
                "//div[contains(text(), 'We'll let you know if you're a fit')]",
                "//div[contains(text(), 'Application complete')]",
                "//div[contains(text(), 'Applied successfully')]",
                "//p[contains(text(), 'Your application has been submitted')]",
                "//span[contains(text(), 'Applied')]"
            ]
            
            for selector in success_messages:
                try:
                    message = self.driver.find_element(By.XPATH, selector)
                    if message.is_displayed():
                        message_text = message.text.strip()
                        self.logger.info(f" APPLICATION SUBMITTED SUCCESSFULLY: {message_text}")
                        
                        # After finding success message, also look for Done button
                        self.random_delay(1, 2)
                        for done_selector in done_button_selectors:
                            try:
                                done_button = self.driver.find_element(By.XPATH, done_selector)
                                if done_button.is_displayed() and done_button.is_enabled():
                                    self.logger.info(f"🔘 SUCCESS MESSAGE FOUND - Also clicking Done button")
                                    self.safe_click(done_button)
                                    self.random_delay(2, 3)
                                    break
                            except:
                                continue
                        
                        return True
                except NoSuchElementException:
                    continue
            
            # Check for URL changes that indicate success
            current_url = self.driver.current_url
            success_url_patterns = [
                '/jobs/application-submitted',
                '/jobs/application-complete', 
                '/jobs/thankyou',
                'application-sent',
                'applied-successfully'
            ]
            
            for pattern in success_url_patterns:
                if pattern in current_url:
                    self.logger.info(f" APPLICATION SUCCESS DETECTED from URL: {current_url}")
                    return True
            
            # Check if modal disappeared (sometimes indicates success)
            try:
                modal_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'jobs-easy-apply-modal') or contains(@class, 'application-modal')]")
                visible_modals = [m for m in modal_elements if m.is_displayed()]
                
                if not visible_modals:
                    # Modal disappeared - might indicate success
                    # But we need additional confirmation
                    self.random_delay(2, 3)
                    
                    # Look for success indicators on the main page
                    main_page_success = [
                        "//button[contains(text(), 'Applied') and @disabled]",
                        "//button[contains(@aria-label, 'Applied')]",
                        "//span[contains(text(), 'Applied')]",
                        "//div[contains(@class, 'jobs-apply-button')][contains(., 'Applied')]"
                    ]
                    
                    for selector in main_page_success:
                        try:
                            element = self.driver.find_element(By.XPATH, selector)
                            if element.is_displayed():
                                self.logger.info(f" APPLICATION SUCCESS: Modal closed and found 'Applied' status")
                                return True
                        except NoSuchElementException:
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Error checking modal state: {str(e)}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking application success: {str(e)}")
            return False
    
    def _application_requires_manual_input(self):
        """Check if application requires manual input like resume or other documents"""
        try:
            manual_input_elements = [
                "//input[@type='file']",
                "//textarea",
                "//button[contains(@aria-label, 'Add resume')]",
                "//button[contains(@aria-label, 'Upload')]",
                "//button[contains(@aria-label, 'Attach')]"
            ]
            for selector in manual_input_elements:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        self.logger.info("Manual input is required.")
                        return True
                except NoSuchElementException:
                    continue
        except Exception as e:
            self.logger.error(f"Error checking manual input requirement: {str(e)}")
        return False

    def _try_final_submit(self):
        """Attempt a final submit if previous steps failed with enhanced detection."""
        try:
            # Enhanced final submit button selectors
            submit_final_selectors = [
                "//button[contains(text(), 'Submit Application')]",
                "//button[contains(text(), 'Submit application')]", 
                "//button[contains(text(), 'Submit')]",
                "//button[contains(@aria-label, 'Submit application')]",
                "//button[contains(@aria-label, 'Submit Application')]",
                "//button[contains(@class, 'submit') and contains(@class, 'primary')]",
                "//button[contains(@class, 'jobs-apply-form__submit-button')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//div[contains(@class, 'jobs-apply-form')]//button[contains(text(), 'Submit')]"
            ]
            
            for i, selector in enumerate(submit_final_selectors):
                try:
                    submit_buttons = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"🔍 Final submit selector {i+1}: Found {len(submit_buttons)} buttons")
                    
                    for j, submit_button in enumerate(submit_buttons):
                        try:
                            if submit_button.is_displayed() and submit_button.is_enabled():
                                button_text = submit_button.text.strip()
                                self.logger.info(f"🎯 FINAL SUBMIT ATTEMPT: Clicking '{button_text}'")
                                
                                # Scroll to button and click
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
                                self.random_delay(1, 2)
                                
                                self.safe_click(submit_button)
                                self.logger.info(f"Final submit attempt made with button: {button_text}")
                                
                                # Wait longer for submission to process
                                self.random_delay(5, 8)
                                
                                # Check for success with multiple attempts
                                for attempt in range(3):
                                    if self._check_application_success():
                                        self.logger.info(f" FINAL SUBMIT SUCCESSFUL after {attempt + 1} attempts")
                                        return True
                                    self.random_delay(2, 3)
                                
                                self.logger.warning(f"⚠️ Final submit completed but success unclear")
                                return False
                                
                        except Exception as btn_e:
                            self.logger.warning(f"Error with submit button {j+1}: {str(btn_e)}")
                            continue
                            
                except NoSuchElementException:
                    self.logger.info(f"No buttons found with selector {i+1}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error with selector {i+1}: {str(e)}")
                    continue
            
            # If no submit buttons found, check if we're already on a success page
            if self._check_application_success():
                self.logger.info(" Application already successful (no submit needed)")
                return True
            
            self.logger.warning(" No final submit buttons found or none worked")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in final submit attempt: {str(e)}")
            return False
    
    def _has_required_fields_missing(self):
        """Check if there are required fields that are not filled"""
        try:
            # Look for required field indicators
            required_indicators = [
                "//input[@required and @value='']",
                "//input[@aria-required='true' and @value='']", 
                "//select[@required and not(option[@selected])]",
                "//textarea[@required and text()='']",
                "//span[contains(@class, 'error')]",
                "//div[contains(@class, 'error')]",
                "//span[contains(text(), 'required')]",
                "//div[contains(text(), 'This field is required')]"
            ]
            
            for selector in required_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        visible_elements = [e for e in elements if e.is_displayed()]
                        if visible_elements:
                            self.logger.info(f"Found {len(visible_elements)} required field issues")
                            return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking required fields: {str(e)}")
            return False
    
    def _auto_fill_application_form(self, user_data):
        """Auto-fill application form with comprehensive field detection"""
        try:
            if not user_data:
                self.logger.warning("No user data provided for auto-fill")
                return
            
            self.logger.info("🖊️ Starting auto-fill of application form...")
            
            # Enhanced field mappings
            field_mappings = {
                # Email fields
                'email': {
                    'value': user_data.get('email', ''),
                    'selectors': [
                        "//input[@type='email']",
                        "//input[contains(@name, 'email')]",
                        "//input[contains(@id, 'email')]",
                        "//input[contains(@placeholder, 'email')]"
                    ]
                },
                # Phone fields
                'phone': {
                    'value': user_data.get('phone', ''),
                    'selectors': [
                        "//input[@type='tel']",
                        "//input[contains(@name, 'phone')]",
                        "//input[contains(@id, 'phone')]",
                        "//input[contains(@placeholder, 'phone')]",
                        "//input[contains(@placeholder, 'mobile')]"
                    ]
                },
                # Name fields
                'first_name': {
                    'value': user_data.get('first_name', ''),
                    'selectors': [
                        "//input[contains(@name, 'firstName')]",
                        "//input[contains(@name, 'first-name')]",
                        "//input[contains(@id, 'firstName')]",
                        "//input[contains(@placeholder, 'first name')]"
                    ]
                },
                'last_name': {
                    'value': user_data.get('last_name', ''),
                    'selectors': [
                        "//input[contains(@name, 'lastName')]",
                        "//input[contains(@name, 'last-name')]",
                        "//input[contains(@id, 'lastName')]",
                        "//input[contains(@placeholder, 'last name')]"
                    ]
                },
                'full_name': {
                    'value': user_data.get('full_name', ''),
                    'selectors': [
                        "//input[contains(@name, 'name') and not(contains(@name, 'first')) and not(contains(@name, 'last'))]",
                        "//input[contains(@placeholder, 'full name')]",
                        "//input[contains(@placeholder, 'your name')]"
                    ]
                }
            }
            
            # Fill text fields
            for field_name, field_config in field_mappings.items():
                value = field_config['value']
                if not value:
                    continue
                    
                self.logger.info(f"🔍 Looking for {field_name} fields...")
                filled = False
                
                for selector in field_config['selectors']:
                    try:
                        fields = self.driver.find_elements(By.XPATH, selector)
                        for field in fields:
                            if field.is_displayed() and field.is_enabled():
                                current_value = field.get_attribute('value')
                                if not current_value:
                                    self.logger.info(f"✍️ Filling {field_name}: {value}")
                                    field.clear()
                                    self.safe_send_keys(field, value)
                                    filled = True
                                    break
                                else:
                                    self.logger.info(f"⏭️ {field_name} field already filled: {current_value}")
                                    filled = True
                                    break
                        if filled:
                            break
                    except Exception as e:
                        self.logger.debug(f"Error filling {field_name}: {str(e)}")
                        continue
                
                if not filled:
                    self.logger.warning(f"⚠️ Could not find or fill {field_name} field")
            
            # Handle resume upload
            self._handle_resume_upload(user_data)
            
            # Handle dropdowns and checkboxes
            self._handle_form_controls()
            
            self.logger.info(" Auto-fill completed")
            
        except Exception as e:
            self.logger.error(f"Error in auto-fill: {str(e)}")
    
    def _handle_resume_upload(self, user_data):
        """Handle resume upload if required"""
        try:
            resume_path = user_data.get('resume_path')
            if not resume_path or not os.path.exists(resume_path):
                self.logger.info("📄 No resume file available for upload")
                return
            
            self.logger.info(f"📤 Looking for resume upload options...")
            
            # Look for file upload inputs
            upload_selectors = [
                "//input[@type='file']",
                "//input[contains(@accept, '.pdf')]",
                "//input[contains(@accept, '.doc')]",
                "//button[contains(text(), 'Upload resume')]",
                "//button[contains(text(), 'Choose file')]",
                "//div[contains(@class, 'file-upload')]//input"
            ]
            
            for selector in upload_selectors:
                try:
                    upload_elements = self.driver.find_elements(By.XPATH, selector)
                    for upload_element in upload_elements:
                        if upload_element.is_enabled():
                            if upload_element.tag_name == 'input' and upload_element.get_attribute('type') == 'file':
                                self.logger.info(f"📤 Uploading resume: {resume_path}")
                                upload_element.send_keys(resume_path)
                                self.random_delay(2, 3)
                                self.logger.info(" Resume uploaded successfully")
                                return
                            elif upload_element.tag_name == 'button':
                                # Click button to open file dialog
                                self.safe_click(upload_element)
                                self.random_delay(1, 2)
                                # Look for file input that appeared
                                hidden_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                                for hidden_input in hidden_inputs:
                                    try:
                                        hidden_input.send_keys(resume_path)
                                        self.random_delay(2, 3)
                                        self.logger.info(" Resume uploaded via button click")
                                        return
                                    except:
                                        continue
                except Exception as e:
                    self.logger.debug(f"Resume upload attempt failed: {str(e)}")
                    continue
            
            self.logger.info("📄 No resume upload field found or upload not required")
            
        except Exception as e:
            self.logger.warning(f"Error handling resume upload: {str(e)}")
    
    def _handle_form_controls(self):
        """Handle dropdowns, checkboxes, and other form controls"""
        try:
            # Handle common dropdowns with default selections
            dropdown_selectors = [
                "//select[not(@disabled)]",
                "//div[contains(@class, 'select')]//button"
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.XPATH, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed() and dropdown.is_enabled():
                            # For select elements, try to select first valid option
                            if dropdown.tag_name == 'select':
                                options = dropdown.find_elements(By.TAG_NAME, 'option')
                                if len(options) > 1:  # Skip if only placeholder option
                                    # Select second option (first is usually placeholder)
                                    options[1].click()
                                    self.logger.info(f" Selected dropdown option: {options[1].text}")
                except Exception as e:
                    self.logger.debug(f"Error handling dropdown: {str(e)}")
                    continue
            
            # Handle checkboxes for terms/conditions
            checkbox_selectors = [
                "//input[@type='checkbox' and contains(@id, 'terms')]",
                "//input[@type='checkbox' and contains(@id, 'agree')]",
                "//input[@type='checkbox' and contains(@name, 'terms')]",
                "//input[@type='checkbox' and contains(@name, 'consent')]"
            ]
            
            for selector in checkbox_selectors:
                try:
                    checkboxes = self.driver.find_elements(By.XPATH, selector)
                    for checkbox in checkboxes:
                        if checkbox.is_displayed() and checkbox.is_enabled() and not checkbox.is_selected():
                            checkbox.click()
                            self.logger.info(" Checked terms/agreement checkbox")
                except Exception as e:
                    self.logger.debug(f"Error handling checkbox: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error handling form controls: {str(e)}")
    
    def _ai_fill_application_form(self, user_data: dict, job_details: dict = None) -> bool:
        """
        AI-powered form filling using Gemini API to intelligently answer questions
        
        Args:
            user_data: User information dictionary
            job_details: Job context for better answers
            
        Returns:
            True if form was processed by AI, False otherwise
        """
        try:
            if not self.ai_answerer or not self.form_parser:
                self.logger.warning("AI components not initialized")
                return False
            
            self.logger.info(" Starting AI-powered form filling...")
            
            # Find all questions on the current page
            questions = self.form_parser.find_all_questions()
            
            if not questions:
                self.logger.info("No form questions found on current page")
                return True  # No questions to fill
            
            self.logger.info(f"Found {len(questions)} form questions to process")
            
            # Prepare user context for AI
            user_context = self.ai_answerer.prepare_user_context(user_data)
            
            # Prepare job context
            job_context = job_details or {}
            
            # Process each question
            successful_fills = 0
            total_questions = len(questions)
            
            for i, question in enumerate(questions):
                try:
                    self.logger.info(f"\n--- Processing Question {i+1}/{total_questions} ---")
                    self.logger.info(f"Question: {question.question_text}")
                    self.logger.info(f"Type: {question.input_type}")
                    if question.options:
                        self.logger.info(f"Options: {question.options}")
                    
                    # Analyze question type
                    question_analysis = self.ai_answerer.analyze_question_type(
                        question.question_text, 
                        question.input_type
                    )
                    
                    self.logger.info(f"Analysis: Category={question_analysis['category']}, Required={question_analysis['is_required']}")
                    
                    # Generate AI answer
                    answer = self.ai_answerer.generate_answer(
                        question_text=question.question_text,
                        user_context=user_context,
                        question_analysis=question_analysis,
                        options=question.options,
                        job_context=job_context
                    )
                    
                    if answer:
                        self.logger.info(f" AI Answer: '{answer}'")
                        
                        # Fill the answer using the form parser
                        success = self.form_parser.fill_question_answer(question, answer)
                        
                        if success:
                            successful_fills += 1
                            self.logger.info(" Successfully filled question")
                            
                            # Small delay between questions to appear more human-like
                            self.random_delay(0.5, 1.5)
                        else:
                            self.logger.warning("⚠️ Failed to fill question")
                    else:
                        self.logger.warning("AI could not generate answer")
                        
                except Exception as e:
                    self.logger.error(f"Error processing question {i+1}: {str(e)}")
                    continue
            
            # Summary
            self.logger.info(f"\n📊 AI Form Filling Summary:")
            self.logger.info(f"   Total questions: {total_questions}")
            self.logger.info(f"   Successfully filled: {successful_fills}")
            self.logger.info(f"   Success rate: {(successful_fills/total_questions*100):.1f}%" if total_questions > 0 else "   Success rate: N/A")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in AI form filling: {str(e)}")
            return False
    
    def run_automated_job_applications(self, keywords, location=None, user_preferences=None, user_skills=None, max_applications=10, resume_path=None):
        """
        Complete end-to-end LinkedIn job application automation
        
        This method orchestrates the entire workflow:
        1. Login to LinkedIn
        2. Search for jobs with given keywords and location
        3. For each job: click → check eligibility → apply if suitable
        4. Handle Easy Apply: fill forms → upload resume → answer questions with AI → review → submit
        5. Move to next job and repeat
        
        Args:
            keywords (str): Job search keywords
            location (str): Job location (optional)
            user_preferences: User job preferences object
            user_skills: User skills list
            max_applications (int): Maximum number of applications to submit
            resume_path (str): Path to resume file for upload
            
        Returns:
            dict: Summary of automation run with statistics
        """
        try:
            self.logger.info("\n" + "="*80)
            self.logger.info("🚀 STARTING AUTOMATED LINKEDIN JOB APPLICATION PROCESS")
            self.logger.info("="*80)
            
            # Prepare user data for applications
            user_data = self._prepare_user_data_for_automation(user_preferences, resume_path)
            
            # Initialize counters
            automation_stats = {
                'total_jobs_viewed': 0,
                'jobs_matched_criteria': 0,
                'applications_attempted': 0,
                'applications_successful': 0,
                'applications_failed': 0,
                'jobs_skipped_no_easy_apply': 0,
                'jobs_skipped_criteria': 0,
                'errors_encountered': 0,
                'started_at': time.time()
            }
            
            # Step 1: Login to LinkedIn
            self.logger.info("\n🔐 STEP 1: LOGGING INTO LINKEDIN")
            login_success = self.login()
            if not login_success:
                return {
                    'success': False,
                    'error': 'Failed to login to LinkedIn',
                    'stats': automation_stats
                }
            self.logger.info(" LinkedIn login successful!")
            
            # Step 2: Search for jobs
            self.logger.info(f"\n🔍 STEP 2: SEARCHING FOR JOBS - '{keywords}' in '{location or 'Any Location'}'")
            job_cards = self.search_jobs(keywords, location)
            if not job_cards:
                return {
                    'success': False,
                    'error': 'No jobs found matching search criteria',
                    'stats': automation_stats
                }
            
            self.logger.info(f"Found {len(job_cards)} jobs to process")
            
            # Step 3: Process jobs sequentially
            self.logger.info(f"\n🎯 STEP 3: PROCESSING JOBS (Target: {max_applications} applications)")
            
            job_index = 0
            while (automation_stats['applications_successful'] < max_applications and 
                   job_index < len(job_cards) * 2):  # Allow for job refreshes
                
                try:
                    # Refresh job cards if we've exhausted current list
                    if job_index >= len(job_cards):
                        self.logger.info("\n🔄 Refreshing job list...")
                        new_job_count = self.scroll_to_load_more_jobs()
                        job_cards = self._get_job_cards()
                        
                        if len(job_cards) <= job_index:
                            self.logger.info("No more jobs available")
                            break
                    
                    current_job = job_cards[job_index]
                    automation_stats['total_jobs_viewed'] += 1
                    
                    self.logger.info(f"\n" + "-"*50)
                    self.logger.info(f"📋 PROCESSING JOB {job_index + 1}/{len(job_cards)}")
                    self.logger.info(f"📊 Progress: {automation_stats['applications_successful']}/{max_applications} applications completed")
                    self.logger.info("-"*50)
                    
                    # Step 3a: Click job to view details
                    self.logger.info("👆 Clicking job card to view details...")
                    try:
                        # Click job card to load details
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", current_job)
                        self.random_delay(1, 2)
                        current_job.click()
                        self.random_delay(3, 4)
                    except Exception as click_error:
                        self.logger.warning(f"Failed to click job card: {str(click_error)}")
                        job_index += 1
                        automation_stats['errors_encountered'] += 1
                        continue
                    
                    # Step 3b: Extract job details from panel
                    job_details = self.extract_job_details_from_panel()
                    if not job_details or not job_details.get('job_title'):
                        self.logger.warning("Could not extract job details, skipping...")
                        job_index += 1
                        continue
                    
                    self.logger.info(f"📄 Job: {job_details['job_title']} at {job_details.get('company_name', 'Unknown Company')}")
                    
                    # Step 3c: Check if job matches user preferences
                    self.logger.info("🎯 Checking job eligibility...")
                    if not self._match_job_to_preferences(job_details, user_preferences, user_skills):
                        self.logger.info(" Job doesn't match criteria, skipping...")
                        automation_stats['jobs_skipped_criteria'] += 1
                        job_index += 1
                        continue
                    
                    automation_stats['jobs_matched_criteria'] += 1
                    self.logger.info(" Job matches criteria!")
                    
                    # Step 3d: Look for Easy Apply button
                    self.logger.info("🔍 Looking for Easy Apply button...")
                    easy_apply_found = self._find_and_click_easy_apply_button()
                    
                    if not easy_apply_found:
                        self.logger.info(" No Easy Apply available, skipping job...")
                        automation_stats['jobs_skipped_no_easy_apply'] += 1
                        job_index += 1
                        continue
                    
                    # Step 3e: Handle application process
                    self.logger.info("📝 Starting application process...")
                    automation_stats['applications_attempted'] += 1
                    
                    # Store job details for AI context
                    self._current_job_details = job_details
                    
                    application_result = self._handle_complete_application_process(user_data, job_details)
                    
                    if application_result['success']:
                        automation_stats['applications_successful'] += 1
                        self.applied_jobs.add(job_details.get('platform_job_id', f"job_{job_index}"))
                        self.logger.info(f" APPLICATION SUCCESSFUL! ({automation_stats['applications_successful']}/{max_applications})")
                        
                        # Delay between applications to appear human-like
                        self.random_delay(5, 10)
                    else:
                        automation_stats['applications_failed'] += 1
                        self.logger.warning(f" Application failed: {application_result.get('error', 'Unknown error')}")
                    
                    job_index += 1
                    
                    # Brief delay before next job
                    self.random_delay(2, 4)
                    
                except Exception as job_error:
                    self.logger.error(f"Error processing job {job_index + 1}: {str(job_error)}")
                    automation_stats['errors_encountered'] += 1
                    job_index += 1
                    continue
            
            # Final statistics
            automation_stats['completed_at'] = time.time()
            automation_stats['total_duration'] = automation_stats['completed_at'] - automation_stats['started_at']
            
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 AUTOMATION COMPLETED - FINAL STATISTICS")
            self.logger.info("="*80)
            self.logger.info(f"⏱️  Total Duration: {automation_stats['total_duration']:.1f} seconds")
            self.logger.info(f"👀 Jobs Viewed: {automation_stats['total_jobs_viewed']}")
            self.logger.info(f"🎯 Jobs Matched Criteria: {automation_stats['jobs_matched_criteria']}")
            self.logger.info(f"📝 Applications Attempted: {automation_stats['applications_attempted']}")
            self.logger.info(f" Applications Successful: {automation_stats['applications_successful']}")
            self.logger.info(f" Applications Failed: {automation_stats['applications_failed']}")
            self.logger.info(f"⏭️  Jobs Skipped (No Easy Apply): {automation_stats['jobs_skipped_no_easy_apply']}")
            self.logger.info(f"🚫 Jobs Skipped (Criteria): {automation_stats['jobs_skipped_criteria']}")
            self.logger.info(f"⚠️  Errors Encountered: {automation_stats['errors_encountered']}")
            
            success_rate = (automation_stats['applications_successful'] / 
                          max(automation_stats['applications_attempted'], 1)) * 100
            self.logger.info(f"📈 Success Rate: {success_rate:.1f}%")
            
            return {
                'success': True,
                'message': f"Automation completed successfully. {automation_stats['applications_successful']} applications submitted.",
                'stats': automation_stats
            }
            
        except Exception as e:
            self.logger.error(f"Fatal error in automation: {str(e)}")
            automation_stats['errors_encountered'] += 1
            return {
                'success': False,
                'error': str(e),
                'stats': automation_stats
            }
    
    def scroll_to_load_more_jobs(self):
        """Enhanced job loading with multiple strategies"""
        try:
            self.logger.info("🔄 Attempting to load more jobs...")
            
            # Strategy 1: Scroll to bottom to trigger infinite scroll
            self.logger.info("📜 Strategy 1: Scrolling to trigger infinite loading...")
            for i in range(3):
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height > current_height:
                    self.logger.info(f" Page expanded from {current_height}px to {new_height}px")
                    self.random_delay(2, 3)  # Wait for content to load
                else:
                    self.logger.info(f"🛑 No more content loaded after scroll {i+1}")
                    break
            
            # Strategy 2: Look for explicit "Load more" buttons
            self.logger.info("🔍 Strategy 2: Looking for load more buttons...")
            more_jobs_selectors = [
                "//button[contains(text(), 'See more jobs')]",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Show more')]",
                "//button[contains(@aria-label, 'Load more jobs')]",
                "//button[contains(@aria-label, 'See more jobs')]",
                "//div[contains(@class, 'jobs-search-results-list')]//button[contains(., 'more')]",
                "//button[contains(@class, 'infinite-scroller__show-more-button')]",
                "//button[contains(@class, 'jobs-search__pagination-button')]",
                "//div[contains(@class, 'jobs-search-results')]//button[contains(., 'more')]"
            ]
            
            button_found = False
            for selector in more_jobs_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            self.logger.info(f"🖱️ Found and clicking: '{button_text}'")
                            
                            # Scroll to button first
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                            self.random_delay(1, 2)
                            
                            # Click button
                            self.safe_click(button)
                            self.logger.info(" Clicked load more button successfully")
                            self.random_delay(3, 5)  # Wait for new jobs to load
                            button_found = True
                            break
                    if button_found:
                        break
                except Exception as e:
                    self.logger.debug(f"Error with load more button: {str(e)}")
                    continue
            
            if not button_found:
                self.logger.info("🛑 No load more buttons found")
            
            # Strategy 3: Check if new jobs were actually loaded
            current_job_count = len(self._get_job_cards())
            self.logger.info(f"📊 Current job count: {current_job_count}")
            
            return current_job_count
            
        except Exception as e:
            self.logger.warning(f"Error loading more jobs: {str(e)}")
            return 0
    
    def _prepare_user_data_for_automation(self, user_preferences, resume_path):
        """
        Prepare user data dictionary for the automation process
        
        Args:
            user_preferences: User preferences object from database
            resume_path (str): Path to resume file
            
        Returns:
            dict: Prepared user data for form filling
        """
        try:
            # Get user object from preferences if available
            user = getattr(user_preferences, 'user', None) if user_preferences else None
            
            user_data = {
                # Basic info
                'full_name': user.full_name if user else 'John Doe',
                'first_name': user.full_name.split(' ')[0] if user and user.full_name else 'John',
                'last_name': user.full_name.split(' ')[-1] if user and user.full_name and ' ' in user.full_name else 'Doe',
                'email': user.email if user else 'example@email.com',
                'phone': user.phone if user else '+1234567890',
                'city': user.location if user else 'Mumbai',
                'location': user.location if user else 'Mumbai, India',
                
                # Professional info
                'experience_years': user.experience_years if user else 3,
                'current_role': 'Software Developer',
                'education': user.education if user else "Bachelor's in Computer Science",
                'skills': ['Python', 'JavaScript', 'React', 'SQL', 'Node.js'],
                
                # Common application answers
                'work_authorization': 'Yes',
                'willing_to_relocate': 'Yes',
                'availability': 'Immediately',
                'expected_salary': '15 LPA',
                'notice_period': '30 days',
                'visa_sponsorship': 'No',
                'remote_work': 'Yes',
                
                # Resume
                'resume_path': resume_path
            }
            
            self.logger.info(f"📋 User data prepared for {user_data['full_name']}")
            return user_data
            
        except Exception as e:
            self.logger.error(f"Error preparing user data: {str(e)}")
            # Return default data
            return {
                'full_name': 'John Doe',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'example@email.com',
                'phone': '+1234567890',
                'city': 'Mumbai',
                'location': 'Mumbai, India',
                'experience_years': 3,
                'current_role': 'Software Developer',
                'education': "Bachelor's in Computer Science",
                'skills': ['Python', 'JavaScript', 'React', 'SQL'],
                'work_authorization': 'Yes',
                'willing_to_relocate': 'Yes',
                'availability': 'Immediately',
                'resume_path': resume_path
            }
    
    def _find_and_click_easy_apply_button(self):
        """
        Find and click the Easy Apply button
        
        Returns:
            bool: True if Easy Apply button was found and clicked, False otherwise
        """
        try:
            self.logger.info("🔍 Searching for Easy Apply button...")
            
            # Comprehensive Easy Apply button selectors
            easy_apply_selectors = [
                "//button[contains(@class, 'jobs-apply-button') and contains(., 'Easy Apply')]",
                "//button[contains(., 'Easy Apply')]",
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//div[contains(@class, 'jobs-apply-button')]//button[contains(., 'Easy Apply')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Easy Apply')]",
                "//button[contains(@data-control-name, 'jobdetails_topcard_inapply')]",
                "//button[contains(@class, 'jobs-apply-button')]",
                "//button[contains(@class, 'artdeco-button') and contains(., 'Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Easy Apply')]",
                "//button[@data-control-name='jobdetails_topcard_inapply']",
                "//button[contains(@class, 'jobs-s-apply') and contains(., 'Easy Apply')]",
                "//div[contains(@class, 'jobs-unified-top-card')]//button[contains(., 'Easy Apply')]"
            ]
            
            for i, selector in enumerate(easy_apply_selectors):
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"   Selector {i+1}: Found {len(buttons)} buttons")
                    
                    for j, button in enumerate(buttons):
                        try:
                            button_text = button.text.strip().lower()
                            is_displayed = button.is_displayed()
                            is_enabled = button.is_enabled()
                            
                            self.logger.info(f"     Button {j+1}: '{button.text.strip()}' (displayed={is_displayed}, enabled={is_enabled})")
                            
                            if is_displayed and is_enabled and ('easy apply' in button_text or 'apply' in button_text):
                                self.logger.info(f" Found suitable Easy Apply button: '{button.text.strip()}'")
                                
                                # Scroll to button and click
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                self.random_delay(1, 2)
                                
                                # Try multiple click methods
                                clicked = False
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    clicked = True
                                    self.logger.info(" Easy Apply button clicked (JavaScript)")
                                except Exception as e1:
                                    try:
                                        button.click()
                                        clicked = True
                                        self.logger.info(" Easy Apply button clicked (WebDriver)")
                                    except Exception as e2:
                                        try:
                                            from selenium.webdriver.common.action_chains import ActionChains
                                            ActionChains(self.driver).move_to_element(button).click().perform()
                                            clicked = True
                                            self.logger.info(" Easy Apply button clicked (ActionChains)")
                                        except Exception as e3:
                                            self.logger.error(f"All click methods failed: {str(e3)}")
                                
                                if clicked:
                                    self.random_delay(3, 5)  # Wait for modal to appear
                                    return True
                                    
                        except Exception as btn_error:
                            self.logger.debug(f"Error checking button {j+1}: {str(btn_error)}")
                            continue
                            
                except Exception as selector_error:
                    self.logger.debug(f"Error with selector {i+1}: {str(selector_error)}")
                    continue
            
            self.logger.info(" No Easy Apply button found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Easy Apply button: {str(e)}")
            return False
    
    def _handle_complete_application_process(self, user_data, job_details):
        """
        Handle the complete application process with all steps:
        1. Fill basic form fields
        2. Upload resume
        3. Answer questions with AI
        4. Review application
        5. Submit application
        
        Args:
            user_data (dict): User information
            job_details (dict): Job context information
            
        Returns:
            dict: Result with success status and details
        """
        try:
            self.logger.info("🚀 Starting complete application process...")
            
            max_steps = 10  # Allow more steps for complex applications
            current_step = 0
            
            while current_step < max_steps:
                self.random_delay(2, 4)
                self.logger.info(f"📋 Application Step {current_step + 1}/{max_steps}")
                
                # Check for success first
                if self._check_application_success():
                    self.logger.info(" Application completed successfully!")
                    return {'success': True}
                
                # Step 1: Basic form auto-fill (traditional fields)
                self.logger.info("📝 Filling basic form fields...")
                self._auto_fill_application_form(user_data)
                
                # Step 2: AI-powered question answering
                if self.ai_answerer and self.form_parser:
                    self.logger.info(" Processing questions with AI...")
                    ai_success = self._ai_fill_application_form(user_data, job_details)
                    if ai_success:
                        self.logger.info(" AI successfully processed questions")
                else:
                    self.logger.info("⚠️ AI not available, skipping AI question processing")
                
                # Step 3: Look for and handle different button types in priority order
                
                # Priority 1: Submit/Submit Application (final step)
                if self._try_submit_application():
                    self.logger.info("🎯 Submit button clicked, checking for success...")
                    self.random_delay(3, 5)
                    if self._check_application_success():
                        return {'success': True}
                    # Continue if not successful
                
                # Priority 2: Review Application
                elif self._try_review_application():
                    self.logger.info("👁️ Review button clicked, proceeding...")
                    self.random_delay(2, 3)
                    # Continue to next iteration to look for submit
                
                # Priority 3: Next/Continue buttons
                elif self._try_next_step():
                    self.logger.info("➡️ Proceeding to next step...")
                    self.random_delay(2, 3)
                    current_step += 1
                    
                else:
                    # No actionable buttons found
                    self.logger.warning("⚠️ No actionable buttons found")
                    
                    # Check if there are missing required fields
                    if self._has_required_fields_missing():
                        self.logger.error(" Required fields are missing")
                        return {'success': False, 'error': 'Required fields missing'}
                    
                    # Final attempt at submission
                    if self._try_final_submit():
                        return {'success': True}
                    
                    # If nothing works, exit
                    self.logger.error(" Unable to proceed with application")
                    break
                
                current_step += 1
            
            # Final checks before giving up
            self.logger.info("🔄 Final submission attempts...")
            if self._try_final_submit():
                return {'success': True}
            
            return {'success': False, 'error': 'Application process incomplete'}
            
        except Exception as e:
            self.logger.error(f"Error in complete application process: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _try_submit_application(self):
        """Try to find and click submit button"""
        try:
            submit_selectors = [
                "//button[contains(@aria-label, 'Submit application') and not(@disabled)]",
                "//button[contains(text(), 'Submit application') and not(@disabled)]",
                "//button[contains(text(), 'Submit') and contains(@class, 'artdeco-button--primary') and not(@disabled)]",
                "//button[contains(@class, 'jobs-apply-form__submit-button') and not(@disabled)]"
            ]
            
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            self.logger.info(f"🎯 Clicking submit button: '{button_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            self.random_delay(1, 2)
                            self.safe_click(button)
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def _try_review_application(self):
        """Try to find and click review button"""
        try:
            review_selectors = [
                "//button[contains(text(), 'Review') and not(@disabled)]",
                "//button[contains(@aria-label, 'Review') and not(@disabled)]",
                "//button[contains(text(), 'Review application') and not(@disabled)]"
            ]
            
            for selector in review_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            self.logger.info(f"👁️ Clicking review button: '{button_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            self.random_delay(1, 2)
                            self.safe_click(button)
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def _try_next_step(self):
        """Try to find and click next/continue button"""
        try:
            next_selectors = [
                "//button[contains(@aria-label, 'Continue to next step') and not(@disabled)]",
                "//button[contains(text(), 'Next') and not(@disabled)]",
                "//button[contains(text(), 'Continue') and not(@disabled)]",
                "//button[contains(@class, 'artdeco-button--primary') and (contains(text(), 'Next') or contains(text(), 'Continue')) and not(@disabled)]"
            ]
            
            for selector in next_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            self.logger.info(f"➡️ Clicking next button: '{button_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            self.random_delay(1, 2)
                            self.safe_click(button)
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def _dismiss_save_password_popup(self):
        """Dismiss save password popup if it appears"""
        try:
            # Look for save password popups
            popup_selectors = [
                "//button[contains(text(), 'Not now')]",
                "//button[contains(@aria-label, 'Not now')]", 
                "//button[contains(text(), 'Skip')]",
                "//button[contains(@aria-label, 'Dismiss')]"
            ]
            
            for selector in popup_selectors:
                try:
                    popup_button = self.driver.find_element(By.XPATH, selector)
                    if popup_button.is_displayed():
                        self.safe_click(popup_button)
                        self.logger.info("Dismissed save password popup")
                        self.random_delay(1, 2)
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"No save password popup to dismiss: {str(e)}")
    
    def _fill_basic_info_fields(self, user_data):
        """Fill basic information fields in application forms"""
        try:
            self.logger.info("📝 Filling basic information fields...")
            
            # Fill first name if field exists
            if user_data.get('first_name'):
                first_name_selectors = [
                    "//input[contains(@name, 'firstName')]",
                    "//input[contains(@name, 'first_name')]",
                    "//input[contains(@placeholder, 'First name')]",
                    "//input[contains(@aria-label, 'First name')]"
                ]
                
                for selector in first_name_selectors:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        if field.is_displayed() and field.is_enabled():
                            current_value = field.get_attribute('value')
                            if not current_value or current_value.strip() == '':
                                self.safe_send_keys(field, user_data['first_name'])
                                self.logger.info(f"First name filled: {user_data['first_name']}")
                            break
                    except NoSuchElementException:
                        continue
            
            # Fill last name if field exists
            if user_data.get('last_name'):
                last_name_selectors = [
                    "//input[contains(@name, 'lastName')]",
                    "//input[contains(@name, 'last_name')]",
                    "//input[contains(@placeholder, 'Last name')]",
                    "//input[contains(@aria-label, 'Last name')]"
                ]
                
                for selector in last_name_selectors:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        if field.is_displayed() and field.is_enabled():
                            current_value = field.get_attribute('value')
                            if not current_value or current_value.strip() == '':
                                self.safe_send_keys(field, user_data['last_name'])
                                self.logger.info(f"Last name filled: {user_data['last_name']}")
                            break
                    except NoSuchElementException:
                        continue
            
            # Fill email if field exists (though LinkedIn usually auto-fills this)
            if user_data.get('email'):
                email_selectors = [
                    "//input[@type='email']",
                    "//input[contains(@name, 'email')]",
                    "//input[contains(@placeholder, 'Email')]",
                    "//input[contains(@aria-label, 'Email')]"
                ]
                
                for selector in email_selectors:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        if field.is_displayed() and field.is_enabled():
                            current_value = field.get_attribute('value')
                            if not current_value or current_value.strip() == '':
                                self.safe_send_keys(field, user_data['email'])
                                self.logger.info(f"Email filled: {user_data['email']}")
                            break
                    except NoSuchElementException:
                        continue
            # Fill city/location if field exists
            if user_data.get('location'):
                city_selectors = [
                    "/html/body/div[4]/div/div/div[2]/div/div[2]/form/div/div[1]/div[7]/div/div[1]/div/input",
                    "//input[contains(@name, 'city')]",
                    "//input[contains(@placeholder, 'City')]",
                    "//input[contains(@aria-label, 'City')]",
                    "//input[contains(@placeholder, 'Location')]",
                    "//input[contains(@aria-label, 'Location')]"
                ]
            
                for selector in city_selectors:
                    try:
                        field = self.driver.find_element(By.XPATH, selector)
                        if field.is_displayed() and field.is_enabled():
                            current_value = field.get_attribute('value')
                            if not current_value or current_value.strip() == '':
                                self.safe_send_keys(field, user_data['location'])
                                self.logger.info(f"Location filled: {user_data['location']}")
                            break
                    except NoSuchElementException:
                        continue
        except Exception as e:
            self.logger.error(f"Error auto-filling application form: {str(e)}")

    
    def _fill_location_fields(self, user_data):
        """Fill location/address fields with user data"""
        try:
            location_info = user_data.get('location', '')
            if not location_info:
                return
            
            self.logger.info(f"🌍 FILLING LOCATION FIELDS with: {location_info}")
            
            # Location field selectors
            location_selectors = [
                "//input[contains(@name, 'location')]",
                "//input[contains(@placeholder, 'Location')]",
                "//input[contains(@placeholder, 'City')]",
                "//input[contains(@placeholder, 'Address')]",
                "//input[contains(@aria-label, 'Location')]",
                "//input[contains(@aria-label, 'City')]",
                "//input[contains(@aria-label, 'Address')]",
                "//input[contains(@name, 'city')]",
                "//input[contains(@name, 'address')]",
                "//input[contains(@id, 'location')]",
                "//input[contains(@id, 'city')]",
                "//input[contains(@id, 'address')]"
            ]
            
            for selector in location_selectors:
                try:
                    location_field = self.driver.find_element(By.XPATH, selector)
                    if location_field.is_displayed() and location_field.is_enabled():
                        current_value = location_field.get_attribute('value')
                        if not current_value or current_value.strip() == '':
                            self.safe_send_keys(location_field, location_info)
                            self.logger.info(f" Location filled: {location_info}")
                            self.random_delay(1, 2)
                            break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error filling location fields: {str(e)}")
    
    def _answer_experience_questions(self, user_data):
        """Intelligently answer Yes/No questions based on user data"""
        try:
            self.logger.info("🧠 ANSWERING EXPERIENCE QUESTIONS...")
            
            # Get user's skills and experience data
            user_skills = [skill.lower() for skill in user_data.get('skills', [])]
            user_education = user_data.get('education', {})
            user_experience = user_data.get('experience_years', 0)
            
            # Find all radio buttons and checkbox groups
            radio_groups = self.driver.find_elements(By.XPATH, "//fieldset | //div[contains(@class, 'question') or contains(@class, 'form-group')]")
            
            for group in radio_groups:
                try:
                    # Look for question text in this group
                    question_elements = group.find_elements(By.XPATH, ".//label | .//legend | .//span | .//div")
                    question_text = ""
                    
                    for element in question_elements:
                        text = element.text.strip().lower()
                        if text and ('?' in text or any(word in text for word in ['do you have', 'are you', 'can you', 'years of', 'experience'])):
                            question_text = text
                            break
                    
                    if not question_text:
                        continue
                        
                    self.logger.info(f"🤔 Found question: {question_text}")
                    
                    # Find radio buttons or checkboxes in this group
                    inputs = group.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']")
                    
                    if not inputs:
                        continue
                    
                    # Determine the best answer based on question content
                    should_answer_yes = self._determine_answer_from_question(question_text, user_data, user_skills)
                    
                    # Select the appropriate answer
                    answer_selected = False
                    for input_elem in inputs:
                        try:
                            if not input_elem.is_displayed() or not input_elem.is_enabled():
                                continue
                                
                            # Get the label text for this input
                            label_text = ""
                            try:
                                # Try multiple ways to find the label
                                input_id = input_elem.get_attribute('id')
                                if input_id:
                                    label = self.driver.find_element(By.XPATH, f"//label[@for='{input_id}']")
                                    label_text = label.text.strip().lower()
                                else:
                                    # Look for parent label or nearby text
                                    parent = input_elem.find_element(By.XPATH, "./parent::*")
                                    label_text = parent.text.strip().lower()
                            except:
                                # Fallback: check value attribute
                                label_text = input_elem.get_attribute('value').lower() if input_elem.get_attribute('value') else ""
                            
                            # Determine if this is the answer we want to select
                            is_yes_option = any(word in label_text for word in ['yes', 'true', 'i have', 'i can', 'i do'])
                            is_no_option = any(word in label_text for word in ['no', 'false', 'i don\'t', 'i cannot', 'i do not'])
                            
                            # Handle number-based answers (years of experience)
                            if not is_yes_option and not is_no_option:
                                # Check if it's a number that matches our experience
                                if label_text.isdigit():
                                    years_option = int(label_text)
                                    if abs(years_option - user_experience) <= 1:  # Within 1 year tolerance
                                        self.safe_click(input_elem)
                                        self.logger.info(f" Selected experience level: {years_option} years")
                                        answer_selected = True
                                        break
                                
                                # Check for range answers like "2-4 years", "5+", etc.
                                if any(char in label_text for char in ['+', '-', 'year']):
                                    if self._matches_experience_range(label_text, user_experience):
                                        self.safe_click(input_elem)
                                        self.logger.info(f" Selected experience range: {label_text}")
                                        answer_selected = True
                                        break
                            
                            # For yes/no questions
                            elif (should_answer_yes and is_yes_option) or (not should_answer_yes and is_no_option):
                                self.safe_click(input_elem)
                                answer_text = "YES" if should_answer_yes else "NO"
                                self.logger.info(f" Answered {answer_text} to: {question_text[:50]}...")
                                answer_selected = True
                                break
                                
                        except Exception as e:
                            self.logger.warning(f"Error processing input option: {str(e)}")
                            continue
                    
                    if answer_selected:
                        self.random_delay(1, 2)
                    else:
                        self.logger.warning(f"⚠️ Could not answer question: {question_text[:50]}...")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing question group: {str(e)}")
                    continue
            
            # Handle dropdown questions
            self._answer_dropdown_questions(user_data, user_skills)
                    
        except Exception as e:
            self.logger.error(f"Error answering experience questions: {str(e)}")
    
    def _determine_answer_from_question(self, question_text, user_data, user_skills):
        """Determine whether to answer yes or no to a question based on user data"""
        try:
            question_lower = question_text.lower()
            
            # Education questions - improved detection
            if any(word in question_lower for word in ['bachelor', 'degree', 'university', 'college', 'graduation', 'undergraduate', 'graduate']):
                # Assume user has a degree (most common case)
                self.logger.info(f" EDUCATION QUESTION: Answering YES (assuming user has degree)")
                return True
            
            # Work authorization questions
            if any(word in question_lower for word in ['authorized', 'work authorization', 'legally authorized', 'eligible to work']):
                self.logger.info(f" WORK AUTHORIZATION: Answering YES")
                return True  # Assume user is authorized to work
            
            # Visa/sponsorship questions - conservative approach
            if any(word in question_lower for word in ['visa', 'sponsorship', 'sponsor', 'require sponsorship']):
                self.logger.info(f" VISA SPONSORSHIP: Answering NO (conservative)")
                return False  # Most users don't require sponsorship
            
            # Remote work comfort questions
            if any(phrase in question_lower for phrase in ['remote setting', 'remote work', 'work remotely', 'work from home', 'comfortable working remotely']):
                self.logger.info(f" REMOTE WORK: Answering YES (most people are comfortable)")
                return True
            
            # On-site work comfort questions  
            if any(phrase in question_lower for phrase in ['onsite setting', 'on-site', 'office setting', 'comfortable working onsite', 'comfortable working on-site']):
                self.logger.info(f" ONSITE WORK: Answering YES (most people are comfortable)")
                return True
            
            # Immediately start questions
            if any(phrase in question_lower for phrase in ['start immediately', 'can you start', 'available to start', 'start urgently']):
                self.logger.info(f" START IMMEDIATELY: Answering YES")
                return True
            
            # Security clearance questions
            if any(phrase in question_lower for phrase in ['security clearance', 'clearance', 'government clearance']):
                self.logger.info(f" SECURITY CLEARANCE: Answering NO (uncommon)")
                return False
            
            # Experience with specific technologies
            for skill in user_skills:
                if skill in question_lower and len(skill) > 3:  # Avoid matching short words
                    self.logger.info(f" SKILL MATCH: Found {skill} in question - answering YES")
                    return True
            
            # Programming languages and common tech terms
            tech_terms = ['python', 'java', 'javascript', 'c++', 'c#', 'react', 'node', 'angular', 'vue', 'sql', 
                         'html', 'css', 'git', 'docker', 'aws', 'azure', 'kubernetes', 'mongodb', 'postgresql']
            user_skills_lower = [s.lower() for s in user_skills]
            for term in tech_terms:
                if term in question_lower and term in user_skills_lower:
                    self.logger.info(f" TECH SKILL MATCH: Found {term} in question - answering YES")
                    return True
            
            # Years of experience questions
            experience_years = user_data.get('experience_years', 0)
            if 'years' in question_lower and ('experience' in question_lower or 'worked' in question_lower):
                # Extract number from question if possible
                import re
                numbers = re.findall(r'\d+', question_lower)
                if numbers:
                    required_years = int(numbers[0])
                    answer = experience_years >= required_years
                    self.logger.info(f" EXPERIENCE YEARS: User has {experience_years}, required {required_years} - answering {'YES' if answer else 'NO'}")
                    return answer
            
            # Generic "Do you have" questions - be optimistic for common skills
            if question_lower.startswith('do you have') or question_lower.startswith('have you'):
                # If it mentions common business skills, answer yes
                if any(term in question_lower for term in ['communication', 'teamwork', 'problem solving', 'leadership', 
                                                           'time management', 'project management', 'analytical']):
                    self.logger.info(f" SOFT SKILL QUESTION: Answering YES for common skill")
                    return True
            
            # "Are you" questions - be positive for work-related attributes
            if question_lower.startswith('are you'):
                if any(term in question_lower for term in ['detail-oriented', 'self-motivated', 'team player', 
                                                           'proactive', 'reliable', 'flexible']):
                    self.logger.info(f" PERSONALITY TRAIT: Answering YES for positive trait")
                    return True
            
            # Salary acknowledgment questions
            if any(phrase in question_lower for phrase in ['understand and acknowledge', 'salary', 'maximum starting salary', 
                                                           'by applying', 'acknowledge that', 'salary will be']):
                self.logger.info(f" SALARY ACKNOWLEDGMENT: Answering YES (agreeing to salary terms)")
                return True
            
            # Commuting/location comfort questions
            if any(phrase in question_lower for phrase in ['comfortable commuting', 'commuting to', 'location', 
                                                           'willing to commute', 'able to commute']):
                self.logger.info(f" COMMUTING: Answering YES (comfortable with commuting)")
                return True
            
            # Agreement/acceptance questions (terms, conditions, etc.)
            if any(phrase in question_lower for phrase in ['agree', 'accept', 'confirm', 'terms and conditions', 
                                                           'privacy policy', 'understand that']):
                self.logger.info(f" AGREEMENT: Answering YES (accepting terms)")
                return True
            
            # Default to conservative "No" for unknown questions
            self.logger.info(f" UNKNOWN QUESTION: No specific match found, defaulting to NO")
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining answer: {str(e)}")
            return False
    
    def _matches_experience_range(self, range_text, user_experience):
        """Check if user experience matches a given range like '2-4 years', '5+', etc."""
        try:
            import re
            range_lower = range_text.lower()
            
            # Handle "5+" format
            plus_match = re.search(r'(\d+)\+', range_lower)
            if plus_match:
                min_years = int(plus_match.group(1))
                return user_experience >= min_years
            
            # Handle "2-4" or "2 to 4" format
            range_match = re.search(r'(\d+)[-\s]*(to|-)\s*(\d+)', range_lower)
            if range_match:
                min_years = int(range_match.group(1))
                max_years = int(range_match.group(3))
                return min_years <= user_experience <= max_years
            
            # Handle "less than X" format
            less_match = re.search(r'less than (\d+)', range_lower)
            if less_match:
                max_years = int(less_match.group(1))
                return user_experience < max_years
            
            # Handle "more than X" format
            more_match = re.search(r'more than (\d+)', range_lower)
            if more_match:
                min_years = int(more_match.group(1))
                return user_experience > min_years
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error matching experience range: {str(e)}")
            return False
    
    def _answer_dropdown_questions(self, user_data, user_skills):
        """Handle dropdown/select questions"""
        try:
            # Find all select elements
            dropdowns = self.driver.find_elements(By.XPATH, "//select")
            
            for dropdown in dropdowns:
                try:
                    if not dropdown.is_displayed() or not dropdown.is_enabled():
                        continue
                    
                    # Try to identify what this dropdown is for
                    dropdown_context = ""
                    
                    # Look for nearby label or context
                    try:
                        # Check for associated label
                        dropdown_id = dropdown.get_attribute('id')
                        if dropdown_id:
                            label = self.driver.find_element(By.XPATH, f"//label[@for='{dropdown_id}']")
                            dropdown_context = label.text.strip().lower()
                        else:
                            # Look at parent elements for context
                            parent = dropdown.find_element(By.XPATH, "./parent::*")
                            dropdown_context = parent.text.strip().lower()
                    except:
                        pass
                    
                    if not dropdown_context:
                        continue
                    
                    self.logger.info(f"🔽 Found dropdown with context: {dropdown_context}")
                    
                    # Get all options
                    from selenium.webdriver.support.ui import Select
                    select = Select(dropdown)
                    options = select.options
                    
                    # Determine best option based on context
                    selected_option = None
                    
                    # Education level dropdown
                    if any(word in dropdown_context for word in ['education', 'degree', 'qualification']):
                        education_level = user_data.get('education', {}).get('level', '').lower()
                        for option in options:
                            option_text = option.text.lower()
                            if education_level and education_level in option_text:
                                selected_option = option
                                break
                            elif 'bachelor' in option_text and 'bachelor' in education_level:
                                selected_option = option
                                break
                    
                    # Experience level dropdown
                    elif any(word in dropdown_context for word in ['experience', 'years']):
                        experience_years = user_data.get('experience_years', 0)
                        for option in options:
                            option_text = option.text.lower()
                            if self._matches_experience_range(option_text, experience_years):
                                selected_option = option
                                break
                    
                    # Commuting comfort dropdown
                    elif any(phrase in dropdown_context for phrase in ['comfortable commuting', 'commuting to', 'location', 'willing to commute']):
                        # Look for "Yes" or positive options for commuting comfort
                        for option in options:
                            option_text = option.text.lower()
                            if any(word in option_text for word in ['yes', 'comfortable', 'willing', 'able']):
                                selected_option = option
                                self.logger.info(f"🚗 COMMUTING DROPDOWN: Selecting positive option '{option.text}'")
                                break
                    
                    # Work preferences (remote/onsite/hybrid)
                    elif any(phrase in dropdown_context for phrase in ['work preference', 'remote work', 'work location', 'work setting']):
                        # Prefer options that show flexibility
                        preference_priority = ['hybrid', 'flexible', 'remote', 'onsite', 'office']
                        for pref in preference_priority:
                            for option in options:
                                option_text = option.text.lower()
                                if pref in option_text:
                                    selected_option = option
                                    self.logger.info(f"💼 WORK PREFERENCE DROPDOWN: Selecting '{option.text}'")
                                    break
                            if selected_option:
                                break
                    
                    # Location dropdown
                    elif any(word in dropdown_context for word in ['location', 'country', 'city']):
                        user_location = user_data.get('location', '').lower()
                        if user_location:
                            for option in options:
                                option_text = option.text.lower()
                                if user_location in option_text or any(city in option_text for city in user_location.split()):
                                    selected_option = option
                                    break
                    
                    # Select the determined option
                    if selected_option and selected_option.text.strip() != "":
                        select.select_by_visible_text(selected_option.text)
                        self.logger.info(f" Selected dropdown option: {selected_option.text}")
                        self.random_delay(1, 2)
                    else:
                        self.logger.info(f"⚠️ No suitable option found for dropdown: {dropdown_context}")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing dropdown: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error answering dropdown questions: {str(e)}")

    def _dismiss_save_password_popup(self):
        """Dismiss the save password popup that appears after login"""
        try:
            # Wait a bit for popup to appear
            self.random_delay(2, 3)
            
            # Multiple selectors for "Never" or "Not now" buttons
            dismiss_selectors = [
                "//button[contains(text(), 'Never')]",
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'No thanks')]",
                "//button[contains(@aria-label, 'Never')]",
                "//button[contains(@aria-label, 'Not now')]",
                "//button[contains(@class, 'secondary') and contains(text(), 'Never')]",
                "//div[contains(@class, 'save-password')]//button[contains(text(), 'Never')]",
                "//div[contains(@class, 'password-save')]//button[contains(text(), 'Never')]"
            ]
            
            for selector in dismiss_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed():
                        self.safe_click(button)
                        self.logger.info("Save password popup dismissed successfully")
                        self.random_delay(1, 2)
                        return True
                except NoSuchElementException:
                    continue
            
            # Try to close any general popup/modal
            close_selectors = [
                "//button[@aria-label='Close']",
                "//button[contains(@class, 'modal-close')]",
                "//button[contains(@class, 'artdeco-modal__dismiss')]"
            ]
            
            for selector in close_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed():
                        self.safe_click(button)
                        self.logger.info("General popup dismissed")
                        self.random_delay(1, 2)
                        return True
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Could not dismiss save password popup: {str(e)}")
        
        return False

    def get_applied_jobs_count(self):
        """Get count of jobs applied to in current session"""
        return len(self.applied_jobs)
    
    def quit(self):
        """Close the browser and cleanup"""
        self.cleanup()
    
    def scroll_to_load_more_jobs(self, max_scrolls=3):
        """Scroll down to load more job listings"""
        try:
            for i in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                
                # Check if "Show more" button exists and click it
                try:
                    show_more_button = self.driver.find_element(
                        By.XPATH, "//button[contains(@aria-label, 'See more jobs')]")
                    if show_more_button.is_displayed():
                        self.safe_click(show_more_button)
                        self.random_delay(2, 3)
                except NoSuchElementException:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Error scrolling to load more jobs: {str(e)}")
            return False
        
        return True
    
    def _prepare_user_data_for_automation(self, user_preferences=None, resume_path=None):
        """Prepare user data dictionary for automation process"""
        try:
            user_data = {
                'first_name': getattr(self, 'first_name', ''),
                'last_name': getattr(self, 'last_name', ''),
                'full_name': getattr(self, 'full_name', ''),
                'email': getattr(self, 'email', ''),
                'phone': getattr(self, 'phone', ''),
                'location': getattr(self, 'location', ''),
                'resume_path': resume_path,
                'experience_years': getattr(self, 'experience_years', 0),
                'current_salary': getattr(self, 'current_salary', ''),
                'expected_salary': getattr(self, 'expected_salary', ''),
                'skills': getattr(self, 'skills', []),
                'education': getattr(self, 'education', ''),
                'achievements': getattr(self, 'achievements', '')
            }
            return user_data
        except Exception as e:
            self.logger.error(f"Error preparing user data: {str(e)}")
            return {}
    
    def _find_and_click_easy_apply_button(self):
        """Find and click Easy Apply button, returns True if successful"""
        try:
            # Use existing selectors from apply_to_job method
            easy_apply_selectors = [
                "//button[contains(@class, 'jobs-apply-button') and contains(., 'Easy Apply')]",
                "//button[contains(., 'Easy Apply')]",
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//div[contains(@class, 'jobs-apply-button')]//button[contains(., 'Easy Apply')]",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Easy Apply')]",
                "//button[contains(@data-control-name, 'jobdetails_topcard_inapply')]",
                "//div[contains(@class, 'jobs-unified-top-card__actions')]//button[contains(., 'Apply')]"
            ]
            
            for selector in easy_apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            if 'easy apply' in button_text.lower() or 'apply' in button_text.lower():
                                self.logger.info(f"🖱️ Clicking Easy Apply button: '{button_text}'")
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                self.random_delay(1, 2)
                                self.driver.execute_script("arguments[0].click();", button)
                                self.random_delay(3, 5)
                                return True
                except Exception as e:
                    continue
            
            self.logger.warning("No Easy Apply button found")
            return False
        except Exception as e:
            self.logger.error(f"Error finding Easy Apply button: {str(e)}")
            return False
    
    def _handle_complete_application_process(self, user_data, job_details):
        """Handle the complete application process with AI assistance"""
        try:
            self.logger.info(" Starting complete application process with AI...")
            
            # Store job details for AI context
            self._current_job_details = job_details
            
            # Use the existing application handler
            return self._handle_application_process(user_data)
            
        except Exception as e:
            self.logger.error(f"Error in complete application process: {str(e)}")
            return {'success': False, 'error': str(e)}
