'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///autohire.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # WTF Forms CSRF configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # File upload settings
    UPLOAD_FOLDER = 'app/static/uploads/resumes'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size to match ResumeHandler
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Job application settings
    MAX_DAILY_APPLICATIONS = 10
    
    # Platform credentials (should be encrypted in production)
    PLATFORMS = {
        'linkedin': {'priority': 1, 'enabled': True},
        'indeed': {'priority': 2, 'enabled': True},
        'naukri': {'priority': 3, 'enabled': True},
        'internshala': {'priority': 4, 'enabled': True}
    }
    
    # AI Configuration
    GOOGLE_GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # For future OpenAI support
    
    # AI Service Settings
    AI_QUESTION_ANSWERING_ENABLED = os.environ.get('AI_QUESTION_ANSWERING_ENABLED', 'true').lower() == 'true'
    AI_DEFAULT_SERVICE = os.environ.get('AI_DEFAULT_SERVICE', 'gemini')  # 'gemini' or 'openai'
    AI_REQUEST_TIMEOUT = int(os.environ.get('AI_REQUEST_TIMEOUT', '10'))  # seconds
    AI_MAX_RETRIES = int(os.environ.get('AI_MAX_RETRIES', '3'))
    AI_FALLBACK_ANSWERS = os.environ.get('AI_FALLBACK_ANSWERS', 'true').lower() == 'true'
