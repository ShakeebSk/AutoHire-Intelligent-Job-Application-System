'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.automation.base_automation import BaseJobAutomation
import time
import re


class IndeedAutomation(BaseJobAutomation):
    """Indeed Job Automation"""
    
    def __init__(self, username, password, headless=True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.indeed.com"
        self.login_url = "https://secure.indeed.com/account/login"
        self.applied_jobs = set()
    
    def login(self):
        """Login to Indeed"""
        try:
            self.logger.info("Navigating to Indeed login page")
            self.driver.get(self.login_url)
            
            # Wait for login form
            email_field = self.wait_for_element((By.ID, "ifl-InputFormField-3"))
            
            # Enter email
            self.safe_send_keys(email_field, self.username)
            self.random_delay(1, 2)
            
            # Click continue
            continue_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.safe_click(continue_button)
            self.random_delay(2, 3)
            
            # Wait for password field
            password_field = self.wait_for_element((By.ID, "ifl-InputFormField-7"))
            self.safe_send_keys(password_field, self.password)
            self.random_delay(1, 2)
            
            # Click sign in
            signin_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.safe_click(signin_button)
            
            # Wait for login to complete
            self.random_delay(3, 5)
            
            # Check if login was successful
            if "indeed.com" in self.driver.current_url and "login" not in self.driver.current_url:
                self.logger.info("Successfully logged into Indeed")
                return True
            else:
                self.logger.error("Indeed login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Indeed login: {str(e)}")
            return False
    
    def search_jobs(self, keywords, location=None, filters=None):
        """Search for jobs on Indeed"""
        try:
            self.logger.info(f"Searching Indeed jobs: {keywords} in {location or 'Any location'}")
            
            # Navigate to Indeed search page
            self.driver.get(self.base_url)
            self.random_delay(2, 3)
            
            # Find search boxes
            what_field = self.wait_for_element((By.ID, "text-input-what"))
            where_field = self.driver.find_element(By.ID, "text-input-where")
            
            # Clear and enter search terms
            what_field.clear()
            self.safe_send_keys(what_field, keywords)
            self.random_delay(1, 2)
            
            if location:
                where_field.clear()
                self.safe_send_keys(where_field, location)
                self.random_delay(1, 2)
            
            # Click search button
            search_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.safe_click(search_button)
            self.random_delay(3, 5)
            
            # Apply filters if provided
            if filters:
                self._apply_search_filters(filters)
            
            # Get job listings
            job_cards = self._get_job_cards()
            self.logger.info(f"Found {len(job_cards)} job listings")
            
            return job_cards
            
        except Exception as e:
            self.logger.error(f"Error searching Indeed jobs: {str(e)}")
            return []
    
    def _apply_search_filters(self, filters):
        """Apply search filters on Indeed"""
        try:
            # Apply date filter
            if filters.get('date_posted'):
                date_filter = filters['date_posted']
                try:
                    date_button = self.driver.find_element(
                        By.XPATH, f"//a[contains(@href, 'fromage') and contains(., '{date_filter}')]")
                    self.safe_click(date_button)
                    self.random_delay(2, 3)
                except NoSuchElementException:
                    self.logger.warning(f"Date filter '{date_filter}' not found")
            
            # Apply salary filter
            if filters.get('min_salary'):
                try:
                    salary_filter = self.driver.find_element(
                        By.XPATH, "//button[contains(@aria-label, 'Salary')]")
                    self.safe_click(salary_filter)
                    self.random_delay(1, 2)
                    
                    # Enter minimum salary
                    min_salary_input = self.driver.find_element(
                        By.XPATH, "//input[@placeholder='Min']")
                    self.safe_send_keys(min_salary_input, str(filters['min_salary']))
                    self.random_delay(1, 2)
                    
                    # Apply salary filter
                    apply_button = self.driver.find_element(
                        By.XPATH, "//button[contains(., 'Apply')]")
                    self.safe_click(apply_button)
                    self.random_delay(2, 3)
                except NoSuchElementException:
                    self.logger.warning("Could not apply salary filter")
            
            # Apply job type filter
            if filters.get('job_type'):
                job_type = filters['job_type']
                try:
                    job_type_button = self.driver.find_element(
                        By.XPATH, f"//a[contains(@href, 'jt') and contains(., '{job_type}')]")
                    self.safe_click(job_type_button)
                    self.random_delay(2, 3)
                except NoSuchElementException:
                    self.logger.warning(f"Job type filter '{job_type}' not found")
                    
        except Exception as e:
            self.logger.warning(f"Could not apply some filters: {str(e)}")
    
    def _get_job_cards(self):
        """Get job cards from search results"""
        try:
            # Wait for job cards to load
            job_cards = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'job_seen_beacon')]")
            
            if not job_cards:
                # Try alternative selector
                job_cards = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'jobsearch-SerpJobCard')]")
            
            return job_cards
            
        except Exception as e:
            self.logger.error(f"Error getting job cards: {str(e)}")
            return []
    
    def extract_job_details(self, job_element):
        """Extract job details from job card"""
        try:
            job_details = {
                'platform': 'indeed',
                'job_title': '',
                'company_name': '',
                'location': '',
                'job_description': '',
                'salary': '',
                'job_url': '',
                'platform_job_id': '',
                'work_type': '',
                'requirements': ''
            }
            
            # Extract job title and URL
            try:
                title_element = job_element.find_element(
                    By.XPATH, ".//h2[contains(@class, 'jobTitle')]//a")
                job_details['job_title'] = title_element.text.strip()
                job_details['job_url'] = title_element.get_attribute('href')
                
                # Extract job ID from URL
                job_id_match = re.search(r'jk=([^&]+)', job_details['job_url'])
                if job_id_match:
                    job_details['platform_job_id'] = job_id_match.group(1)
                    
            except NoSuchElementException:
                try:
                    # Alternative selector
                    title_element = job_element.find_element(
                        By.XPATH, ".//span[@title]")
                    job_details['job_title'] = title_element.get_attribute('title')
                except NoSuchElementException:
                    self.logger.warning("Could not extract job title")
            
            # Extract company name
            try:
                company_element = job_element.find_element(
                    By.XPATH, ".//span[contains(@class, 'companyName')]")
                job_details['company_name'] = company_element.text.strip()
            except NoSuchElementException:
                try:
                    company_element = job_element.find_element(
                        By.XPATH, ".//a[@data-testid='company-name']")
                    job_details['company_name'] = company_element.text.strip()
                except NoSuchElementException:
                    self.logger.warning("Could not extract company name")
            
            # Extract location
            try:
                location_element = job_element.find_element(
                    By.XPATH, ".//div[contains(@class, 'companyLocation')]")
                job_details['location'] = location_element.text.strip()
            except NoSuchElementException:
                self.logger.warning("Could not extract location")
            
            # Extract salary if available
            try:
                salary_element = job_element.find_element(
                    By.XPATH, ".//span[contains(@class, 'salary-snippet')]")
                job_details['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                pass  # Salary not always available
            
            # Extract job snippet/description
            try:
                snippet_element = job_element.find_element(
                    By.XPATH, ".//div[contains(@class, 'job-snippet')]")
                job_details['job_description'] = snippet_element.text.strip()
            except NoSuchElementException:
                self.logger.warning("Could not extract job snippet")
            
            return job_details
            
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return None
    
    def apply_to_job(self, job_element):
        """Apply to a job on Indeed"""
        try:
            job_details = self.extract_job_details(job_element)
            if not job_details or not job_details.get('platform_job_id'):
                return {'success': False, 'error': 'Could not extract job details'}
            
            # Check if already applied
            job_id = job_details['platform_job_id']
            if job_id in self.applied_jobs:
                return {'success': False, 'error': 'Already applied to this job'}
            
            # Click on job title to open job details
            try:
                title_link = job_element.find_element(
                    By.XPATH, ".//h2[contains(@class, 'jobTitle')]//a")
                self.safe_click(title_link)
                self.random_delay(2, 3)
                
                # Look for apply button
                apply_button = self._find_apply_button()
                
                if apply_button:
                    self.safe_click(apply_button)
                    self.random_delay(2, 3)
                    
                    # Handle application process
                    application_result = self._handle_application_process()
                    
                    if application_result['success']:
                        self.applied_jobs.add(job_id)
                        self.logger.info(f"Successfully applied to {job_details['job_title']} at {job_details['company_name']}")
                        
                        return {
                            'success': True,
                            'job_details': job_details,
                            'application_method': 'indeed_apply'
                        }
                    else:
                        return {
                            'success': False,
                            'error': application_result.get('error', 'Application process failed'),
                            'job_details': job_details
                        }
                else:
                    return {
                        'success': False,
                        'error': 'Apply button not found',
                        'job_details': job_details
                    }
                    
            except NoSuchElementException:
                return {
                    'success': False,
                    'error': 'Could not open job details',
                    'job_details': job_details
                }
                
        except Exception as e:
            self.logger.error(f"Error applying to job: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _find_apply_button(self):
        """Find the apply button on job page"""
        try:
            # Try different apply button selectors
            apply_selectors = [
                "//button[contains(@class, 'ia-IndeedApplyButton')]",
                "//button[contains(., 'Apply now')]",
                "//a[contains(@class, 'ia-IndeedApplyButton')]",
                "//button[contains(@aria-label, 'Apply')]"
            ]
            
            for selector in apply_selectors:
                try:
                    apply_button = self.driver.find_element(By.XPATH, selector)
                    if apply_button.is_displayed() and apply_button.is_enabled():
                        return apply_button
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding apply button: {str(e)}")
            return None
    
    def _handle_application_process(self):
        """Handle the Indeed application process"""
        try:
            self.random_delay(2, 3)
            
            # Check if we're on Indeed's application page
            if "apply" in self.driver.current_url.lower():
                # Look for submit/continue buttons
                submit_selectors = [
                    "//button[contains(., 'Submit application')]",
                    "//button[contains(., 'Continue')]",
                    "//button[contains(., 'Apply')]",
                    "//input[@type='submit']"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_button = self.driver.find_element(By.XPATH, selector)
                        if submit_button.is_displayed() and submit_button.is_enabled():
                            self.safe_click(submit_button)
                            self.random_delay(2, 3)
                            
                            # Check for confirmation
                            if self._check_application_success():
                                return {'success': True}
                            
                    except NoSuchElementException:
                        continue
                
                # If we get here, try to handle multi-step process
                return self._handle_multi_step_application()
            
            # If redirected to external site, we can't complete the application
            return {'success': False, 'error': 'Redirected to external application site'}
            
        except Exception as e:
            self.logger.error(f"Error in application process: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_multi_step_application(self):
        """Handle multi-step application process"""
        try:
            max_steps = 3
            current_step = 0
            
            while current_step < max_steps:
                self.random_delay(1, 2)
                
                # Look for next/continue buttons
                next_selectors = [
                    "//button[contains(., 'Next')]",
                    "//button[contains(., 'Continue')]",
                    "//button[contains(., 'Review')]"
                ]
                
                button_found = False
                for selector in next_selectors:
                    try:
                        next_button = self.driver.find_element(By.XPATH, selector)
                        if next_button.is_displayed() and next_button.is_enabled():
                            self.safe_click(next_button)
                            self.random_delay(2, 3)
                            button_found = True
                            break
                    except NoSuchElementException:
                        continue
                
                if not button_found:
                    # Try to find submit button
                    try:
                        submit_button = self.driver.find_element(
                            By.XPATH, "//button[contains(., 'Submit')]")
                        if submit_button.is_displayed() and submit_button.is_enabled():
                            self.safe_click(submit_button)
                            self.random_delay(2, 3)
                            
                            if self._check_application_success():
                                return {'success': True}
                            
                    except NoSuchElementException:
                        pass
                    
                    break
                
                current_step += 1
            
            return {'success': False, 'error': 'Could not complete multi-step application'}
            
        except Exception as e:
            self.logger.error(f"Error in multi-step application: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _check_application_success(self):
        """Check if application was submitted successfully"""
        try:
            success_indicators = [
                "application submitted",
                "application sent",
                "thank you for applying",
                "your application has been"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator in page_text:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking application success: {str(e)}")
            return False
    
    def get_applied_jobs_count(self):
        """Get count of jobs applied to in current session"""
        return len(self.applied_jobs)
    
    def scroll_to_load_more_jobs(self, max_scrolls=3):
        """Scroll down to load more job listings"""
        try:
            for i in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                
                # Check if "Next" page button exists
                try:
                    next_page_button = self.driver.find_element(
                        By.XPATH, "//a[@aria-label='Next Page']")
                    if next_page_button.is_displayed():
                        self.safe_click(next_page_button)
                        self.random_delay(3, 5)
                        break
                except NoSuchElementException:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Error scrolling to load more jobs: {str(e)}")
