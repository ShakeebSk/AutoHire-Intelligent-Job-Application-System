#!/usr/bin/env python3
"""
AI-powered question answering service for job applications
Uses Google Gemini API to intelligently answer application questions
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AIQuestionAnswerer:
    """
    AI-powered service to answer job application questions using Google Gemini API
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the AI Question Answerer
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Google Gemini API key is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        logger.info(" AI Question Answerer initialized with Google Gemini")
    
    def prepare_user_context(self, user_data: Dict[str, Any]) -> str:
        """
        Prepare user context from database data for AI processing
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Formatted context string for AI
        """
        try:
            # Extract key information
            personal_info = {
                'name': user_data.get('full_name', ''),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phone', ''),
                'city': user_data.get('city', ''),
                'experience_years': user_data.get('experience_years', 0),
                'current_role': user_data.get('current_role', ''),
                'education': user_data.get('education', ''),
                'skills': user_data.get('skills', []),
                'previous_companies': user_data.get('previous_companies', []),
                'certifications': user_data.get('certifications', []),
                'languages': user_data.get('languages', []),
                'availability': user_data.get('availability', 'Immediately'),
                'salary_expectation': user_data.get('salary_expectation', ''),
                'work_authorization': user_data.get('work_authorization', 'Yes'),
                'willing_to_relocate': user_data.get('willing_to_relocate', 'Yes'),
                'preferred_work_type': user_data.get('preferred_work_type', 'Full-time'),
                'linkedin_url': user_data.get('linkedin_url', ''),
                'portfolio_url': user_data.get('portfolio_url', ''),
                'github_url': user_data.get('github_url', '')
            }
            
            # Build context string
            context = f"""
USER PROFILE INFORMATION:
===========================

Personal Details:
- Full Name: {personal_info['name']}
- Email: {personal_info['email']}
- Phone: {personal_info['phone']}
- Location: {personal_info['city']}

Professional Background:
- Years of Experience: {personal_info['experience_years']}
- Current Role: {personal_info['current_role']}
- Education: {personal_info['education']}
- Skills: {', '.join(personal_info['skills']) if personal_info['skills'] else 'Not specified'}
- Previous Companies: {', '.join(personal_info['previous_companies']) if personal_info['previous_companies'] else 'Not specified'}
- Certifications: {', '.join(personal_info['certifications']) if personal_info['certifications'] else 'None'}
- Languages: {', '.join(personal_info['languages']) if personal_info['languages'] else 'English'}

Availability & Preferences:
- Availability: {personal_info['availability']}
- Salary Expectation: {personal_info['salary_expectation']}
- Work Authorization: {personal_info['work_authorization']}
- Willing to Relocate: {personal_info['willing_to_relocate']}
- Preferred Work Type: {personal_info['preferred_work_type']}

Online Presence:
- LinkedIn: {personal_info['linkedin_url']}
- Portfolio: {personal_info['portfolio_url']}
- GitHub: {personal_info['github_url']}

CURRENT DATE: {datetime.now().strftime('%B %Y')}
"""
            
            return context.strip()
            
        except Exception as e:
            logger.error(f"Error preparing user context: {str(e)}")
            return "User information not available"
    
    def analyze_question_type(self, question_text: str, element_type: str = None) -> Dict[str, Any]:
        """
        Analyze the type of question and determine the appropriate response format
        
        Args:
            question_text: The question text
            element_type: HTML element type (input, select, textarea, etc.)
            
        Returns:
            Dictionary containing question analysis
        """
        try:
            question_lower = question_text.lower().strip()
            
            # Common question patterns
            patterns = {
                'yes_no': [
                    r'\b(are you|do you|have you|can you|will you|would you)\b.*\?',
                    r'\b(yes|no)\b.*\?',
                    r'\b(authorized to work|work authorization)\b',
                    r'\b(willing to relocate|relocate)\b',
                    r'\b(background check|drug test)\b'
                ],
                'experience': [
                    r'\b(years of experience|experience.*years)\b',
                    r'\bhow many years\b',
                    r'\byears.*working\b',
                    r'\bexperience.*level\b'
                ],
                'availability': [
                    r'\b(when can you start|start date|availability)\b',
                    r'\b(available to start|notice period)\b'
                ],
                'salary': [
                    r'\b(salary|compensation|pay|wage)\b.*\b(expectation|requirement|range)\b',
                    r'\b(expected salary|salary range)\b'
                ],
                'location': [
                    r'\b(current location|where.*located|city|state)\b',
                    r'\b(address|zip code|postal code)\b'
                ],
                'education': [
                    r'\b(degree|education|university|college|school)\b',
                    r'\b(graduation|graduated|gpa)\b'
                ],
                'cover_letter': [
                    r'\b(cover letter|why.*interested|why.*apply)\b',
                    r'\b(tell us about yourself|describe yourself)\b',
                    r'\b(motivation|interest.*position)\b'
                ],
                'skills': [
                    r'\b(skills|proficiency|expertise|technologies)\b',
                    r'\b(programming languages|software|tools)\b'
                ]
            }
            
            question_type = 'text'  # Default
            category = 'general'
            
            # Determine question category
            for cat, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, question_lower):
                        category = cat
                        break
                if category != 'general':
                    break
            
            # Determine input type based on element or content
            if element_type:
                if element_type.lower() in ['select', 'dropdown']:
                    question_type = 'select'
                elif element_type.lower() in ['radio']:
                    question_type = 'radio'
                elif element_type.lower() in ['checkbox']:
                    question_type = 'checkbox'
                elif element_type.lower() in ['textarea']:
                    question_type = 'textarea'
            
            # Override based on content analysis
            if any(word in question_lower for word in ['select', 'choose', 'pick']):
                question_type = 'select'
            elif '?' in question_text and len(question_text.split()) < 15:
                question_type = 'short_text'
            elif any(word in question_lower for word in ['explain', 'describe', 'tell', 'why', 'how']):
                question_type = 'textarea'
            
            return {
                'type': question_type,
                'category': category,
                'is_required': '*' in question_text or 'required' in question_lower,
                'is_yes_no': category == 'yes_no',
                'needs_detailed_response': question_type in ['textarea', 'cover_letter']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing question type: {str(e)}")
            return {
                'type': 'text',
                'category': 'general',
                'is_required': False,
                'is_yes_no': False,
                'needs_detailed_response': False
            }
    
    def generate_answer(self, question_text: str, user_context: str, question_analysis: Dict[str, Any], 
                       options: List[str] = None, job_context: Dict[str, Any] = None) -> str:
        """
        Generate an appropriate answer using Google Gemini API
        
        Args:
            question_text: The question to answer
            user_context: User's background information
            question_analysis: Analysis of question type and category
            options: Available options for select/radio questions
            job_context: Job-specific context (title, company, description)
            
        Returns:
            Generated answer
        """
        try:
            # Build job context
            job_info = ""
            if job_context:
                job_info = f"""
JOB CONTEXT:
- Position: {job_context.get('job_title', 'Not specified')}
- Company: {job_context.get('company_name', 'Not specified')}
- Location: {job_context.get('location', 'Not specified')}
"""
            
            # Build options context
            options_text = ""
            if options:
                options_text = f"Available Options: {', '.join(options)}"
            
            # Create specialized prompts based on question type
            if question_analysis['category'] == 'yes_no':
                prompt = f"""
Based on the user's profile, answer this yes/no question appropriately:

{user_context}
{job_info}

Question: {question_text}
{options_text}

Instructions:
- Answer with just "Yes" or "No" (or select the appropriate option if multiple choice)
- Base your answer on the user's profile information
- Be consistent with typical job application expectations
- If work authorization is asked, answer "Yes" unless specified otherwise
- If willing to relocate is asked, consider the user's preferences

Answer:"""

            elif question_analysis['category'] == 'experience':
                prompt = f"""
Based on the user's profile, provide their years of experience:

{user_context}
{job_info}

Question: {question_text}
{options_text}

Instructions:
- Provide the number of years from the user's profile
- If not specified, estimate based on their background
- Give just the number (e.g., "3" or "5")
- Round to the nearest whole number

Answer:"""

            elif question_analysis['category'] == 'salary':
                prompt = f"""
Based on the user's profile and job context, provide salary expectation:

{user_context}
{job_info}

Question: {question_text}
{options_text}

Instructions:
- If user has specified salary expectation, use that
- Otherwise, provide a reasonable range based on role and experience
- Keep it professional and market-appropriate
- Use format like "80000-90000" or "Negotiable" or "Market Rate"

Answer:"""

            elif question_analysis['category'] == 'availability':
                prompt = f"""
Based on the user's profile, answer the availability question:

{user_context}
{job_info}

Question: {question_text}
{options_text}

Instructions:
- Use the user's specified availability
- If not specified, use "Immediately" or "2 weeks notice" as appropriate
- Be professional and realistic

Answer:"""

            elif question_analysis['category'] == 'cover_letter':
                prompt = f"""
Write a professional response to this application question:

{user_context}
{job_info}

Question: {question_text}

Instructions:
- Write 2-4 sentences maximum
- Highlight relevant skills and experience from the user's profile
- Show enthusiasm for the role and company
- Be professional but personable
- Connect user's background to the job requirements
- Keep it concise and impactful

Answer:"""

            else:  # General questions
                prompt = f"""
Answer this job application question professionally based on the user's profile:

{user_context}
{job_info}

Question: {question_text}
{options_text}

Instructions:
- Use information from the user's profile when relevant
- Keep answers concise and professional
- If it's a multiple choice question, select the most appropriate option
- If it's a text question, provide a brief but complete answer
- Be honest and accurate based on the user's background

Answer:"""

            # Call Google Gemini API
            response = self._call_gemini_api(prompt)
            
            if response:
                # Clean and format the response
                answer = response.strip()
                
                # Post-process based on question type
                if question_analysis['is_yes_no'] and options:
                    # Ensure the answer matches available options
                    answer_lower = answer.lower()
                    for option in options:
                        if option.lower() in answer_lower or answer_lower in option.lower():
                            return option
                
                # Limit length for different input types
                if question_analysis['type'] == 'short_text':
                    answer = answer[:100]  # Limit short text responses
                elif question_analysis['type'] != 'textarea':
                    answer = answer[:200]  # Limit other responses
                
                logger.info(f" Generated answer for question: {question_text[:50]}...")
                return answer
            else:
                logger.warning("Failed to get response from AI, using fallback")
                return self._get_fallback_answer(question_analysis, options)
                
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return self._get_fallback_answer(question_analysis, options)
    
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """
        Call Google Gemini API with the given prompt
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            Generated response text or None if failed
        """
        try:
            url = f"{self.base_url}?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 200,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    if 'content' in data['candidates'][0]:
                        parts = data['candidates'][0]['content'].get('parts', [])
                        if parts and 'text' in parts[0]:
                            return parts[0]['text']
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("Gemini API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini API call error: {str(e)}")
        
        return None
    
    def _get_fallback_answer(self, question_analysis: Dict[str, Any], options: List[str] = None) -> str:
        """
        Provide fallback answers when AI API fails
        
        Args:
            question_analysis: Analysis of the question
            options: Available options if applicable
            
        Returns:
            Fallback answer
        """
        category = question_analysis['category']
        
        fallback_answers = {
            'yes_no': 'Yes',
            'experience': '3',
            'availability': 'Immediately',
            'salary': 'Negotiable',
            'location': 'Mumbai, India',
            'education': 'Bachelor\'s Degree',
            'cover_letter': 'I am excited about this opportunity and believe my skills and experience make me a strong candidate for this position.',
            'skills': 'Proficient in relevant technologies',
            'general': 'Yes'
        }
        
        if options and category in ['yes_no', 'general']:
            # Try to pick the most positive option
            positive_options = [opt for opt in options if any(word in opt.lower() for word in ['yes', 'agree', 'accept', 'available', 'authorized'])]
            if positive_options:
                return positive_options[0]
            return options[0] if options else fallback_answers.get(category, 'N/A')
        
        return fallback_answers.get(category, 'N/A')
