"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Platform-specific job automation scrapers
"""

from .linkedin_automation import LinkedInAutomation
from .indeed_automation import IndeedAutomation
# TODO: Implement these platforms
# from .naukri_automation import NaukriAutomation
# from .internshala_automation import InternshalaAutomation

__all__ = [
    'LinkedInAutomation',
    'IndeedAutomation', 
    # 'NaukriAutomation',
    # 'InternshalaAutomation'
]
