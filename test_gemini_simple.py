#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Simple standalone test to verify Google Gemini API key
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api_direct():
    """Test Gemini API directly"""
    print("🔑 Testing Google Gemini API Key...")
    print("=" * 50)
    
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print(" No API key found in .env file")
        return False
    
    print(f" API Key found: {api_key[:20]}...{api_key[-10:]}")
    
    # Test API endpoint (updated model name)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Answer this job application question based on this profile: A software developer with 3 years of Python experience. Question: Are you authorized to work in this country? Answer with just Yes or No."
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 50
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print("\n🚀 Making API request...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                if 'content' in data['candidates'][0]:
                    parts = data['candidates'][0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        answer = parts[0]['text'].strip()
                        print(f"🎉 SUCCESS! AI Answer: '{answer}'")
                        print("\n Your Gemini API key is working perfectly!")
                        print(" AI Question Answering is ready to use!")
                        return True
            
            print(f" Unexpected response format: {data}")
            return False
        else:
            print(f" API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(" API request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f" Network error: {str(e)}")
        return False
    except Exception as e:
        print(f" Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Gemini API Key Test")
    print("=" * 35)
    
    success = test_gemini_api_direct()
    
    if success:
        print("\n🎊 CONGRATULATIONS!")
        print("Your Google Gemini API is working!")
        print("\nWhat this means:")
        print(" Your API key is valid")
        print(" You have internet connectivity")
        print(" AI integration is ready!")
        print("\nNext steps:")
        print("1. Run your existing LinkedIn automation")
        print("2. When it encounters forms, it will use AI!")
        print("3. Test with: python debug_linkedin_apply.py")
    else:
        print("\n API test failed.")
        print("Please check:")
        print("1. Your internet connection")
        print("2. API key validity") 
        print("3. Gemini API quotas")
        print("4. Make sure the API key has no restrictions")
