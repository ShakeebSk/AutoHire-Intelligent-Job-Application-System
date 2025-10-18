'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''


from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import logging

class BaseJobAutomation(ABC):
    """Base class for job platform automation"""
    
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to get the correct chromedriver path
            import platform
            import os
            
            driver_path = ChromeDriverManager().install()
            
            # On Windows, ensure we have the correct executable
            if platform.system() == "Windows":
                if not driver_path.endswith(".exe"):
                    # Look for the actual chromedriver.exe in the directory
                    driver_dir = os.path.dirname(driver_path)
                    for root, dirs, files in os.walk(driver_dir):
                        for file in files:
                            if file == "chromedriver.exe":
                                driver_path = os.path.join(root, file)
                                break
                        if driver_path.endswith(".exe"):
                            break
            
            self.logger.info(f"Using ChromeDriver at: {driver_path}")
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Execute script to prevent detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            self.logger.error(f"Failed to setup ChromeDriver: {str(e)}")
            raise
        

    # def setup_driver(self):
    #     """Setup Chrome WebDriver with options"""
    #     chrome_options = Options()
    #     if self.headless:
    #         chrome_options.add_argument("--headless")
        
    #     # Common Chrome options
    #     chrome_options.add_argument("--disable-dev-shm-usage")
    #     chrome_options.add_argument("--no-sandbox")
    #     chrome_options.add_argument("--disable-gpu")
    #     chrome_options.add_argument("--window-size=1920,1080")
    #     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    #     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #     chrome_options.add_experimental_option('useAutomationExtension', False)

    #     try:
    #         # Use WebDriverManager to automatically download and manage ChromeDriver
    #         import os
    #         driver_path = ChromeDriverManager().install()
            
    #         # Fix the path issue - WebDriverManager sometimes returns wrong file
    #         if not driver_path.endswith(".exe"):
    #             # Look for the actual chromedriver.exe in the directory
    #             driver_dir = os.path.dirname(driver_path)
    #             for root, dirs, files in os.walk(driver_dir):
    #                 for file in files:
    #                     if file == "chromedriver.exe":
    #                         driver_path = os.path.join(root, file)
    #                         break
    #                 if driver_path.endswith(".exe"):
    #                     break
            
    #         self.logger.info(f"Using ChromeDriver at: {driver_path}")
            
    #         if not os.path.exists(driver_path):
    #             raise Exception(f"ChromeDriver not found at: {driver_path}")
            
    #         service = Service(driver_path)
    #         self.driver = webdriver.Chrome(service=service, options=chrome_options)
    #         self.wait = WebDriverWait(self.driver, 10)

    #         # Prevent detection
    #         self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    #         self.logger.info("ChromeDriver setup completed successfully")

    #     except Exception as e:
    #         self.logger.error(f"Failed to setup ChromeDriver: {str(e)}")
    #         raise

    def cleanup(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            
    @abstractmethod
    def login(self):
        """Login to the platform"""
        pass
    
    @abstractmethod
    def search_jobs(self, keywords, location=None):
        """Search for jobs based on keywords and location"""
        pass
    
    @abstractmethod
    def apply_to_job(self, job_element):
        """Apply to a specific job"""
        pass
    
    @abstractmethod
    def extract_job_details(self, job_element):
        """Extract job details from job element"""
        pass
    
    def wait_for_element(self, locator, timeout=10):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
    
    def safe_click(self, element):
        """Safely click an element"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            self.logger.error(f"Failed to click element: {e}")
            return False
    
    def safe_send_keys(self, element, text):
        """Safely send keys to an element"""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send keys: {e}")
            return False
    
    def scroll_to_element(self, element):
        """Scroll to element"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        import random
        time.sleep(random.uniform(min_seconds, max_seconds))
