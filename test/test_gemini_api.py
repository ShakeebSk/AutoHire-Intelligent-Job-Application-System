#!/usr/bin/env python3
"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Quick test to verify Google Gemini API key is working
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.utils.ai_question_answerer import AIQuestionAnswerer

def test_gemini_api():
    """Test the Gemini API with your key"""
    print("🔑 Testing Google Gemini API Key...")
    print("=" * 50)
    
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print(" No API key found in .env file")
        return False
    
    print(f" API Key found: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        # Initialize AI service
        ai_answerer = AIQuestionAnswerer(api_key=api_key)
        print(" AI Question Answerer initialized successfully")
        
        # Test user data
        test_user_data = {
            'full_name': 'name',
            'email': 'emai@example.com',
            'phone': '+91-number',
            'city': 'cuty',
            'experience_years': 3,
            'current_role': 'your current role ',
            'education': 'degree name',
            'skills': ['Python', 'JavaScript', 'React', 'SQL'],
            'work_authorization': 'Yes',
            'willing_to_relocate': 'Yes',
            'availability': 'your availability'
        }
        
        print(" Test user data prepared")
        
        # Prepare context
        user_context = ai_answerer.prepare_user_context(test_user_data)
        print(f" User context prepared (length: {len(user_context)} chars)")
        
        # Test a simple question
        test_question = "Are you authorized to work in this country?"
        print(f"\n Testing AI with question: '{test_question}'")
        
        # Analyze question
        analysis = ai_answerer.analyze_question_type(test_question, 'radio')
        print(f"Analysis: {analysis}")
        
        # Generate answer
        answer = ai_answerer.generate_answer(
            question_text=test_question,
            user_context=user_context,
            question_analysis=analysis,
            options=['Yes', 'No']
        )
        
        if answer:
            print(f"🎉 SUCCESS! AI Answer: '{answer}'")
            print("\n Your Gemini API key is working perfectly!")
            print(" AI Question Answering is ready to use!")
            return True
        else:
            print(" AI failed to generate answer")
            return False
            
    except Exception as e:
        print(f" Error testing API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Gemini API Key Test")
    print("=" * 30)
    
    success = test_gemini_api()
    
    if success:
        print("\n🎊 CONGRATULATIONS!")
        print("Your AI-powered question answering is ready!")
        print("\nNext steps:")
        print("1. Run: python test_ai_question_answering.py")
        print("2. Or use with LinkedIn: python debug_linkedin_apply.py")
    else:
        print("\n API test failed. Please check:")
        print("1. Your internet connection")
        print("2. API key validity")
        print("3. Gemini API quotas")
