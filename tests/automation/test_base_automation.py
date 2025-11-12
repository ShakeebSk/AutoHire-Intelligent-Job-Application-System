"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Tests for base automation functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests import BaseAutomationTest
from app.automation.base_automation import BaseJobAutomation


class TestBaseAutomation(BaseAutomationTest):
    """Test base automation functionality"""
    
    def setUp(self):
        super().setUp()
        self.automation = None
    
    def tearDown(self):
        if self.automation:
            try:
                self.automation.cleanup()
            except:
                pass
        super().tearDown()
    
    @patch('app.automation.base_automation.webdriver.Chrome')
    @patch('app.automation.base_automation.ChromeDriverManager')
    def test_setup_driver(self, mock_chrome_manager, mock_chrome):
        """Test WebDriver setup"""
        # Create a concrete implementation for testing
        class TestAutomation(BaseJobAutomation):
            def login(self):
                return True
            def search_jobs(self, keywords, location=None):
                return []
            def apply_to_job(self, job_element):
                return {'success': True}
            def extract_job_details(self, job_element):
                return {'title': 'Test Job'}
        
        # Mock ChromeDriverManager
        mock_chrome_manager.return_value.install.return_value = '/path/to/chromedriver'
        
        # Mock Chrome WebDriver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Create automation instance
        automation = TestAutomation('test@example.com', 'password', headless=True)
        
        # Test driver setup
        automation.setup_driver()
        
        # Verify driver was created
        self.assertIsNotNone(automation.driver)
        self.assertIsNotNone(automation.wait)
        
        # Verify Chrome was called with correct options
        mock_chrome.assert_called_once()
        
        # Cleanup
        automation.cleanup()
    
    def test_safe_click(self):
        """Test safe click functionality"""
        class TestAutomation(BaseJobAutomation):
            def login(self):
                return True
            def search_jobs(self, keywords, location=None):
                return []
            def apply_to_job(self, job_element):
                return {'success': True}
            def extract_job_details(self, job_element):
                return {'title': 'Test Job'}
        
        automation = TestAutomation('test@example.com', 'password')
        automation.driver = Mock()
        
        # Test successful click
        mock_element = Mock()
        result = automation.safe_click(mock_element)
        
        self.assertTrue(result)
        automation.driver.execute_script.assert_called_once()
    
    def test_safe_send_keys(self):
        """Test safe send keys functionality"""
        class TestAutomation(BaseJobAutomation):
            def login(self):
                return True
            def search_jobs(self, keywords, location=None):
                return []
            def apply_to_job(self, job_element):
                return {'success': True}
            def extract_job_details(self, job_element):
                return {'title': 'Test Job'}
        
        automation = TestAutomation('test@example.com', 'password')
        
        # Test successful send keys
        mock_element = Mock()
        result = automation.safe_send_keys(mock_element, 'test text')
        
        self.assertTrue(result)
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with('test text')
    
    def test_random_delay(self):
        """Test random delay functionality"""
        class TestAutomation(BaseJobAutomation):
            def login(self):
                return True
            def search_jobs(self, keywords, location=None):
                return []
            def apply_to_job(self, job_element):
                return {'success': True}
            def extract_job_details(self, job_element):
                return {'title': 'Test Job'}
        
        automation = TestAutomation('test@example.com', 'password')
        
        # Test that random delay doesn't raise exception
        with patch('time.sleep') as mock_sleep:
            automation.random_delay(1, 2)
            mock_sleep.assert_called_once()
    
    @patch('app.automation.base_automation.WebDriverWait')
    def test_wait_for_element(self, mock_wait):
        """Test wait for element functionality"""
        class TestAutomation(BaseJobAutomation):
            def login(self):
                return True
            def search_jobs(self, keywords, location=None):
                return []
            def apply_to_job(self, job_element):
                return {'success': True}
            def extract_job_details(self, job_element):
                return {'title': 'Test Job'}
        
        automation = TestAutomation('test@example.com', 'password')
        automation.driver = Mock()
        
        # Mock WebDriverWait
        mock_wait_instance = Mock()
        mock_element = Mock()
        mock_wait_instance.until.return_value = mock_element
        mock_wait.return_value = mock_wait_instance
        
        # Test wait for element
        from selenium.webdriver.common.by import By
        locator = (By.ID, 'test-id')
        result = automation.wait_for_element(locator)
        
        self.assertEqual(result, mock_element)
        mock_wait.assert_called_once_with(automation.driver, 10)


if __name__ == '__main__':
    unittest.main()
