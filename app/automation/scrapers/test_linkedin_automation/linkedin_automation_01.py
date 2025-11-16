from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from app.automation.base_automation import BaseJobAutomation
import time
import logging
import re
import os


class LinkedInAutomation(BaseJobAutomation):
    # Enhanced LinkedIn Automation including AI scoring and PDF generation
    """LinkedIn Job Automation"""
    
    def __init__(self, username, password, headless=True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs"
        self.applied_jobs = set()
        self.search_completed = False
        self.current_job_index = 0
        
        # Set up the Chrome driver
        try:
            self.setup_driver()
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
            
            # Navigate to jobs page
            self.driver.get(self.jobs_url)
            self.random_delay(3, 5)  # Increased delay for page load
            self.logger.info("Navigated to jobs page successfully")
            
            # Find search boxes with multiple fallback selectors
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
            
            # Clear and enter keywords
            try:
                keyword_box.clear()
                self.safe_send_keys(keyword_box, keywords)
                self.logger.info(f"Keyword '{keywords}' entered successfully")
            except Exception as e:
                self.logger.error(f"Failed to enter keywords: {str(e)}")
                return []
            
            self.random_delay(1, 2)
            
            # Enter location if provided
            if location:
                location_selectors = [
                    "/html/body/div[6]/div[3]/div[3]/div/div[1]/div/div/div[2]/div",
                    "/html/body/div[6]/div[3]/div[3]/div/div[1]/div/div/div[2]/div/button"
                    # "/html/body/div[6]/header/div/div/div/div[2]/div[3]/div/div/input[1]", #full XPath
                    "//input[contains(@placeholder, 'City')]",
                    "//input[contains(@placeholder, 'location')]",
                    "//input[contains(@class, 'jobs-search-box__text-input--with-clear')]",
                    "//input[@aria-label='City']"
                ]
                
                self.logger.info("Attempting to locate location search input")
                
                location_box = None
                for selector in location_selectors:
                    try:
                        location_box = self.driver.find_element(By.XPATH, selector)
                        if location_box.is_displayed() and location_box.is_enabled():
                            break
                    except NoSuchElementException:
                        continue
                
                if location_box:
                    try:
                        # Clear the field using multiple methods
                        location_box.clear()
                        self.driver.execute_script("arguments[0].value = '';", location_box)
                        self.safe_send_keys(location_box, location)
                        self.logger.info(f"Location '{location}' entered successfully")
                    except Exception as e:
                        self.logger.error(f"Failed to enter location: {str(e)}")
                        return []
                    
                    self.random_delay(1, 2)
                else:
                    self.logger.error("Location field not found")
                    return []
            
            
            # Try multiple methods to trigger search
            search_triggered = False
            
            # Method 1: Press Enter on keyword box
            try:
                if keyword_box.is_displayed() and keyword_box.is_enabled():
                    keyword_box.send_keys(Keys.RETURN)
                    search_triggered = True
                    self.logger.info("Search triggered via Enter key")
                else:
                    self.logger.error("Failed to trigger search using Enter key")
            except Exception as e:
                self.logger.warning(f"Could not trigger search via Enter: {str(e)}")
            
            # Method 2: Click search button if Enter didn't work
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
                
            self.random_delay(5, 8)  # Wait longer for results to load
            
            # Apply filters if provided (but skip easy apply by default)
            if filters:
                self._apply_search_filters(filters)
            
            # Get job listings
            job_cards = self._get_job_cards()
            self.logger.info(f"Found {len(job_cards)} job listings")
            
            # Mark search as completed
            self.search_completed = True
            self.current_job_index = 0  # Reset job index for new search
            
            return job_cards
            
        except Exception as e:
            self.logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
    
    def _apply_search_filters(self, filters):
        """Apply search filters"""
        try:
            # Apply easy apply filter only if explicitly requested
            if filters.get('easy_apply', False):  # Changed default to False
                self.logger.info("Applying Easy Apply filter as requested")
                easy_apply_button_selectors = [
                    "//button[contains(@aria-label, 'Easy Apply filter')]",
                    "//button[contains(text(), 'Easy Apply')]",
                    "/html/body/div[6]/div[3]/div[3]/section/div/div/div[1]/div/ul/li[5]/div/button",
                    "//div[contains(@class, 'search-reusables__filter-binary-toggle')]//button[contains(., 'Easy Apply')]"
                ]
                
                filter_applied = False
                for selector in easy_apply_button_selectors:
                    try:
                        easy_apply_button = self.driver.find_element(By.XPATH, selector)
                        if easy_apply_button.is_displayed() and not easy_apply_button.get_attribute('aria-pressed') == 'true':
                            self.safe_click(easy_apply_button)
                            self.logger.info("Easy Apply filter activated")
                            filter_applied = True
                            self.random_delay(1, 2)
                            break
                    except NoSuchElementException:
                        continue
                
                if not filter_applied:
                    self.logger.warning("Could not find or activate Easy Apply filter")
            else:
                self.logger.info("Easy Apply filter NOT applied - searching all job types")
            
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
                        self.logger.info(f"✅ Found job title from panel: {job_details['job_title']}")
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
                        self.logger.info(f"✅ Found company from panel: {job_details['company_name']}")
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
                                self.logger.info(f"✅ Found location from panel: {job_details['location']}")
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
                self.logger.info(f"✅ Found job ID from URL: {job_details['platform_job_id']}")
            
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
                        self.logger.info(f"✅ Found job description from panel (length: {len(job_details['job_description'])})")
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
                    self.logger.info(f"✅ EXACT TITLE MATCH: '{preferred_title}' found in '{job_title_lower}'")
                    self.logger.info(f"✅ JOB APPROVED: Title matches user preference - applying regardless of other criteria")
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
                self.logger.info(f"✅ WORD-BASED TITLE MATCH: {len(word_matches)} word(s) matched")
                self.logger.info(f"✅ JOB APPROVED: Title matches user preference - applying regardless of other criteria")
                return True
            
            # Method 3: Partial word matching (most lenient)
            for preferred_title in preferred_titles:
                for job_word in job_title_words:
                    for pref_word in preferred_title.split():
                        if len(pref_word) > 3 and (pref_word in job_word or job_word in pref_word):
                            self.logger.info(f"✅ PARTIAL TITLE MATCH: '{pref_word}' matches '{job_word}'")
                            self.logger.info(f"✅ JOB APPROVED: Title matches user preference - applying regardless of other criteria")
                            return True
            
            # If no title match found, reject the job
            self.logger.info(f"❌ NO TITLE MATCH: Job title '{job_details['job_title']}' doesn't match any preferred titles")
            self.logger.info(f"❌ JOB REJECTED: Title doesn't match user preferences")
            return False
            
        except Exception as e:
            self.logger.error(f"Error matching job to preferences: {str(e)}")
            return False

    def process_jobs_sequentially(self, user_preferences=None, user_skills=None, user_data=None, max_applications=10):
        """Process jobs sequentially - click each job card, extract details, and apply if suitable"""
        try:
            applications_made = 0
            
            while applications_made < max_applications:
                # Get current job cards
                job_cards = self._get_job_cards()
                
                if not job_cards:
                    self.logger.info("No job cards found")
                    break
                
                # Check if we've processed all available jobs
                if self.current_job_index >= len(job_cards):
                    self.logger.info("All available jobs processed")
                    # Try to load more jobs
                    self.scroll_to_load_more_jobs()
                    job_cards = self._get_job_cards()
                    
                    # If still no new jobs, we're done
                    if self.current_job_index >= len(job_cards):
                        self.logger.info("No more jobs available")
                        break
                
                # Get current job card
                current_job = job_cards[self.current_job_index]
                self.logger.info(f"Processing job {self.current_job_index + 1}/{len(job_cards)}")
                
                # Process this specific job
                result = self.apply_to_job(current_job, user_preferences, user_skills, user_data)
                
                if result['success']:
                    applications_made += 1
                    self.logger.info(f"Successfully applied to job {self.current_job_index + 1}. Total applications: {applications_made}")
                else:
                    self.logger.info(f"Skipped job {self.current_job_index + 1}: {result.get('error', 'Unknown error')}")
                
                # Move to next job
                self.current_job_index += 1
                
                # Small delay between jobs
                self.random_delay(2, 4)
            
            self.logger.info(f"Job processing completed. Total applications made: {applications_made}")
            return {'applications_made': applications_made, 'success': True}
            
        except Exception as e:
            self.logger.error(f"Error in sequential job processing: {str(e)}")
            return {'success': False, 'error': str(e), 'applications_made': applications_made}

    def apply_to_job(self, job_element_or_index, user_preferences=None, user_skills=None, user_data=None):
        """Apply to a job on LinkedIn if it matches user preferences"""
        try:
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
                                self.logger.info(f"✅ FOUND EASY APPLY BUTTON: '{button_text}' using selector {i+1}")
                                break
                        except Exception as btn_e:
                            self.logger.warning(f"   Error checking button {j+1}: {str(btn_e)}")
                    
                    if easy_apply_button:
                        break
                        
                except NoSuchElementException:
                    self.logger.info(f"   ❌ No elements found with this selector")
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
                        self.logger.info("✅ CLICKED EASY APPLY BUTTON (JavaScript click)")
                    except Exception as e1:
                        self.logger.warning(f"JavaScript click failed: {str(e1)}")
                        try:
                            # Method 2: Regular click
                            easy_apply_button.click()
                            clicked = True
                            self.logger.info("✅ CLICKED EASY APPLY BUTTON (regular click)")
                        except Exception as e2:
                            self.logger.warning(f"Regular click failed: {str(e2)}")
                            try:
                                # Method 3: ActionChains click
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(self.driver).move_to_element(easy_apply_button).click().perform()
                                clicked = True
                                self.logger.info("✅ CLICKED EASY APPLY BUTTON (ActionChains click)")
                            except Exception as e3:
                                self.logger.error(f"All click methods failed: {str(e3)}")
                    
                    if clicked:
                        self.random_delay(3, 5)  # Wait for modal to appear
                        
                        # Handle application process with user data
                        application_result = self._handle_application_process(user_data)
                        
                        if application_result['success']:
                            self.applied_jobs.add(job_id)
                            self.logger.info(f"✅ SUCCESSFULLY APPLIED to {job_details['job_title']} at {job_details['company_name']}")
                            
                            # Wait a moment before moving to next job
                            self.random_delay(2, 3)
                            
                            return {
                                'success': True,
                                'job_details': job_details,
                                'application_method': 'easy_apply'
                            }
                        else:
                            self.logger.warning(f"❌ APPLICATION FAILED for {job_details['job_title']}: {application_result.get('error', 'Unknown error')}")
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
                self.logger.info(f"❌ NO EASY APPLY FOUND for: {job_details.get('job_title', 'Unknown Job')}")
                
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
                                                self.logger.info("✅ Regular Apply button opened Easy Apply modal - proceeding...")
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
            
            self.logger.info("❌ No suitable application methods found")
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
                    self.logger.info("✅ Application already submitted successfully!")
                    return {'success': True}
                
                # Auto-fill any form fields if user data is available
                if user_data:
                    self._auto_fill_application_form(user_data)
                
                # Look for submit button first (higher priority)
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
                                    self.logger.info("✅ APPLICATION SUBMITTED SUCCESSFULLY!")
                                    return {'success': True}
                                
                                # If not successful, might need more steps
                                break
                        if submit_found:
                            break
                    except Exception as e:
                        self.logger.debug(f"Submit button check failed: {str(e)}")
                        continue
                
                if submit_found:
                    # If we found and clicked submit, wait and check again
                    self.random_delay(2, 3)
                    if self._check_application_success():
                        return {'success': True}
                    # Otherwise continue to next step
                
                # Look for next/continue buttons only if no submit found
                if not submit_found:
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
                            self.logger.error("❌ Required fields missing - cannot proceed")
                            self._close_application_modal()
                            return {'success': False, 'error': 'Required form fields not filled'}
                        
                        # If no progress possible, exit
                        self.logger.error("❌ No way to proceed - application stuck")
                        break
                else:
                    # We clicked submit but it didn't work, try final checks
                    if current_step >= 3:  # If we've tried multiple steps
                        self.logger.warning("⚠️ Multiple steps completed, trying final submit attempts...")
                        if self._try_final_submit():
                            return {'success': True}
                        break
            
            # Final attempts
            self.logger.info("🔄 Attempting final submission...")
            if self._try_final_submit():
                return {'success': True}
            
            # Clean exit
            self._close_application_modal()
            return {'success': False, 'error': 'Application process completed but submission unclear'}
            
        except Exception as e:
            self.logger.error(f"❌ Error in application process: {str(e)}")
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
        """Check if the application was successful"""
        try:
            success_messages = [
                "//div[contains(text(), 'Application submitted')]",
                "//h2[contains(., 'You applied')]",
                "//span[contains(., 'successfully applied')]"
            ]
            for selector in success_messages:
                try:
                    message = self.driver.find_element(By.XPATH, selector)
                    if message.is_displayed():
                        self.logger.info("Application submitted successfully.")
                        return True
                except NoSuchElementException:
                    continue
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
        """Attempt a final submit if previous steps failed."""
        try:
            submit_final_selectors = [
                "//button[contains(text(), 'Submit Application')]",
                "//button[contains(text(), 'Submit')]"
            ]
            for selector in submit_final_selectors:
                try:
                    submit_button = self.driver.find_element(By.XPATH, selector)
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        self.safe_click(submit_button)
                        self.logger.info("Final submit attempt made.")
                        self.random_delay(2, 3)
                        return self._check_application_success()
                except NoSuchElementException:
                    continue
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
        """Auto-fill application form with comprehensive user data and intelligent question answering"""
        try:
            self.logger.info("🔍 SCANNING FOR FORM FIELDS TO AUTO-FILL...")
            
            # Answer Yes/No questions intelligently based on user data
            self._answer_experience_questions(user_data)
            
            # Fill location/address fields
            self._fill_location_fields(user_data)
            
            # Fill phone number if field exists
            if user_data.get('phone'):
                phone_selectors = [
                    "//input[@type='tel']",
                    "//input[contains(@name, 'phone')]",
                    "//input[contains(@placeholder, 'Phone')]",
                    "//input[contains(@placeholder, 'phone')]",
                    "//input[contains(@aria-label, 'Phone')]",
                    "//input[contains(@aria-label, 'phone')]",
                    "//input[contains(@id, 'phone')]",
                    "//input[contains(@name, 'mobile')]",
                    "//input[contains(@placeholder, 'Mobile')]"
                ]
                
                for selector in phone_selectors:
                    try:
                        phone_field = self.driver.find_element(By.XPATH, selector)
                        if phone_field.is_displayed() and phone_field.is_enabled():
                            # Check if field is empty or needs updating
                            current_value = phone_field.get_attribute('value')
                            if not current_value or current_value.strip() == '':
                                self.safe_send_keys(phone_field, user_data['phone'])
                                self.logger.info(f"📞 Phone number '{user_data['phone']}' filled successfully")
                                self.random_delay(1, 2)
                            break
                    except NoSuchElementException:
                        continue
            
            # Upload resume if file upload field exists
            if user_data.get('resume_path'):
                resume_path = user_data['resume_path']
                # Verify the file exists
                if resume_path and os.path.exists(resume_path):
                    self.logger.info(f"📄 ATTEMPTING TO UPLOAD RESUME: {resume_path}")
                    
                    resume_selectors = [
                        "//input[@type='file']",
                        "//input[contains(@accept, '.pdf')]",
                        "//input[contains(@accept, '.doc')]",
                        "//input[contains(@name, 'resume')]",
                        "//input[contains(@name, 'file')]",
                        "//input[contains(@class, 'file-input')]",
                        "//div[contains(@class, 'file-upload')]//input[@type='file']",
                        "//input[@type='file' and not(contains(@style, 'display: none'))]",
                        "//input[@type='file' and @style!='display: none']"
                    ]
                    
                    uploaded = False
                    for i, selector in enumerate(resume_selectors):
                        try:
                            self.logger.info(f"🔍 Trying resume upload selector {i+1}: {selector}")
                            file_inputs = self.driver.find_elements(By.XPATH, selector)
                            self.logger.info(f"   Found {len(file_inputs)} file input elements")
                            
                            for j, file_input in enumerate(file_inputs):
                                try:
                                    # Check if element is interactable
                                    if file_input.is_enabled():
                                        self.logger.info(f"   File input {j+1}: Enabled=True")
                                        
                                        # Try to upload the file
                                        file_input.send_keys(resume_path)
                                        self.logger.info(f"✅ RESUME UPLOADED SUCCESSFULLY: {resume_path}")
                                        self.random_delay(3, 5)  # Wait for upload to process
                                        uploaded = True
                                        break
                                    else:
                                        self.logger.info(f"   File input {j+1}: Enabled=False")
                                except Exception as input_e:
                                    self.logger.warning(f"   Error with file input {j+1}: {str(input_e)}")
                            
                            if uploaded:
                                break
                                
                        except NoSuchElementException:
                            self.logger.info(f"   ❌ No file inputs found with selector {i+1}")
                            continue
                        except Exception as e:
                            self.logger.warning(f"   ⚠️ Error with selector {i+1}: {str(e)}")
                            continue
                    
                    if not uploaded:
                        self.logger.warning("❌ Could not find or use any file upload element")
                        # Look for upload buttons that might trigger file dialog
                        upload_button_selectors = [
                            "//button[contains(., 'Upload') and contains(., 'resume')]",
                            "//button[contains(., 'Upload') and contains(., 'CV')]",
                            "//button[contains(@aria-label, 'Upload')]",
                            "//button[contains(., 'Choose file')]",
                            "//button[contains(., 'Browse')]"
                        ]
                        for selector in upload_button_selectors:
                            try:
                                upload_btn = self.driver.find_element(By.XPATH, selector)
                                if upload_btn.is_displayed() and upload_btn.is_enabled():
                                    self.logger.info(f"Found upload button: {upload_btn.text}")
                                    # Note: We can't easily handle file dialogs in automated testing
                                    # This would require manual intervention
                                    break
                            except NoSuchElementException:
                                continue
                else:
                    self.logger.warning(f"❌ Resume file not found at path: {resume_path}")
            
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
                            self.logger.info(f"✅ Location filled: {location_info}")
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
                                        self.logger.info(f"✅ Selected experience level: {years_option} years")
                                        answer_selected = True
                                        break
                                
                                # Check for range answers like "2-4 years", "5+", etc.
                                if any(char in label_text for char in ['+', '-', 'year']):
                                    if self._matches_experience_range(label_text, user_experience):
                                        self.safe_click(input_elem)
                                        self.logger.info(f"✅ Selected experience range: {label_text}")
                                        answer_selected = True
                                        break
                            
                            # For yes/no questions
                            elif (should_answer_yes and is_yes_option) or (not should_answer_yes and is_no_option):
                                self.safe_click(input_elem)
                                answer_text = "YES" if should_answer_yes else "NO"
                                self.logger.info(f"✅ Answered {answer_text} to: {question_text[:50]}...")
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
            
            # Education questions
            if any(word in question_lower for word in ['bachelor', 'degree', 'university', 'college', 'graduation']):
                education_level = user_data.get('education', {}).get('level', '').lower()
                return 'bachelor' in education_level or 'degree' in education_level or 'graduate' in education_level
            
            # Work authorization questions
            if any(word in question_lower for word in ['authorized', 'work authorization', 'legally authorized']):
                return True  # Assume user is authorized to work
            
            # Visa/sponsorship questions
            if any(word in question_lower for word in ['visa', 'sponsorship', 'sponsor']):
                visa_status = user_data.get('visa_sponsorship_required', False)
                return visa_status
            
            # Experience with specific technologies
            for skill in user_skills:
                if skill in question_lower and len(skill) > 3:  # Avoid matching short words
                    self.logger.info(f"Found skill match: {skill} in question")
                    return True
            
            # Programming languages
            prog_languages = ['python', 'java', 'javascript', 'c++', 'c#', 'react', 'node', 'angular', 'vue']
            for lang in prog_languages:
                if lang in question_lower and lang in [s.lower() for s in user_skills]:
                    return True
            
            # Years of experience questions
            experience_years = user_data.get('experience_years', 0)
            if 'years' in question_lower and 'experience' in question_lower:
                # Extract number from question if possible
                import re
                numbers = re.findall(r'\d+', question_lower)
                if numbers:
                    required_years = int(numbers[0])
                    return experience_years >= required_years
            
            # Default to conservative "No" for unknown questions
            self.logger.info(f"No specific match found for question, defaulting to NO")
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
                        self.logger.info(f"✅ Selected dropdown option: {selected_option.text}")
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
