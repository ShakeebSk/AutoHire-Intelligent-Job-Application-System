"""
Enhanced Job Scoring System with AI Integration
Integrates Google Gemini AI to score job suitability against user resumes
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini not available. Job scoring will use basic scoring.")

from app.models.user import User
from app.models.job_preferences import JobPreferences
from app.models.job_application import JobApplication
from app import db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobScorer:
    """Enhanced job scoring system with AI integration"""
    
    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key
        self.client = None
        
        if GEMINI_AVAILABLE and gemini_api_key:
            try:
                self.client = genai.Client(api_key=gemini_api_key)
                logger.info("Gemini AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            logger.warning("Gemini API not available or API key not provided")
    
    def format_user_resume_data(self, user: User, job_preferences: JobPreferences) -> str:
        """Format user data into resume text for AI scoring"""
        resume_parts = []
        
        # Basic Info
        resume_parts.append(f"Name: {user.first_name} {user.last_name}")
        resume_parts.append(f"Email: {user.email}")
        if user.phone:
            resume_parts.append(f"Phone: {user.phone}")
        
        # Profile/Summary
        if hasattr(user, 'profile_summary') and user.profile_summary:
            resume_parts.append(f"\nProfessional Summary:\n{user.profile_summary}")
        
        # Job Preferences (as career objectives)
        if job_preferences:
            preferred_titles = job_preferences.get_preferred_job_titles()
            if preferred_titles:
                resume_parts.append(f"\nCareer Objectives: {', '.join(preferred_titles)}")
            
            required_skills = job_preferences.get_required_skills()
            if required_skills:
                resume_parts.append(f"\nCore Skills: {', '.join(required_skills)}")
            
            preferred_locations = job_preferences.get_preferred_locations()
            if preferred_locations:
                resume_parts.append(f"\nPreferred Locations: {', '.join(preferred_locations)}")
        
        # Experience (if available in user model)
        if hasattr(user, 'experience') and user.experience:
            resume_parts.append(f"\nExperience:\n{user.experience}")
        
        # Education (if available in user model)
        if hasattr(user, 'education') and user.education:
            resume_parts.append(f"\nEducation:\n{user.education}")
        
        # Skills (if available in user model)
        if hasattr(user, 'skills') and user.skills:
            resume_parts.append(f"\nTechnical Skills:\n{user.skills}")
        
        return "\n".join(resume_parts)
    
    def get_ai_job_score(self, resume_text: str, job_details: Dict[str, Any]) -> Optional[int]:
        """Get AI-powered job suitability score using Gemini"""
        if not self.client or not resume_text or not job_details.get('job_description'):
            return None
        
        job_title = job_details.get('job_title', 'N/A')
        company_name = job_details.get('company_name', 'N/A')
        job_description = job_details.get('job_description', 'N/A')
        location = job_details.get('location', 'N/A')
        
        logger.info(f"Scoring job: {job_title} at {company_name}")
        
        prompt = f"""
        You are a job suitability scoring assistant. You will be given a candidate's resume and a job description.
        Based ONLY on the information provided, return exactly one integer between 0 and 100 (inclusive) that represents the candidate's suitability for the role.
        
        Consider the following factors:
        - Skills match (technical and soft skills)
        - Experience relevance
        - Career progression alignment
        - Location compatibility
        - Industry fit
        
        Do NOT return any words, punctuation, or explanation—only the integer score.
        
        --- CANDIDATE RESUME ---
        {resume_text}
        --- END RESUME ---
        
        --- JOB DESCRIPTION ---
        Job Title: {job_title}
        Company: {company_name}
        Location: {location}
        
        {job_description}
        --- END JOB DESCRIPTION ---
        
        Score (0–100):
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=10
                )
            )
            
            score_text = response.text.strip()
            score = int(score_text)
            
            if 0 <= score <= 100:
                logger.info(f"AI score for {job_title}: {score}")
                return score
            else:
                logger.warning(f"AI score out of range ({score}) for {job_title}")
                return None
                
        except ValueError:
            logger.error(f"Could not parse AI score response: {response.text.strip()}")
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None
    
    def get_basic_job_score(self, user: User, job_preferences: JobPreferences, job_details: Dict[str, Any]) -> int:
        """Basic rule-based job scoring without AI"""
        score = 0
        max_score = 100
        
        # Job title matching (30 points) - requires 2 word matches
        if job_preferences:
            preferred_titles = [title.lower() for title in job_preferences.get_preferred_job_titles()]
            job_title_lower = job_details.get('job_title', '').lower()
            
            # Split job titles into words and match any two words
            preferred_words = {word for title in preferred_titles for word in title.split()}
            job_title_words = set(job_title_lower.split())
            word_matches = len(preferred_words.intersection(job_title_words))
            
            if word_matches >= 2:
                score += 30
            elif word_matches == 1:
                score += 15  # Partial credit for one word match
        
        # Location matching (20 points)
        if job_preferences:
            preferred_locations = [loc.lower() for loc in job_preferences.get_preferred_locations()]
            job_location_lower = job_details.get('location', '').lower()
            
            location_match = any(loc in job_location_lower or job_location_lower in loc for loc in preferred_locations)
            if location_match:
                score += 20
        
        # Skills matching (30 points) - requires at least 3 skill matches
        if job_preferences and job_details.get('job_description'):
            required_skills = [skill.lower() for skill in job_preferences.get_required_skills()]
            job_description_lower = job_details.get('job_description', '').lower()
            
            skill_matches = sum(1 for skill in required_skills if skill in job_description_lower)
            if skill_matches >= 3:
                # Full points for 3+ matches
                skill_score = min(30, (skill_matches / len(required_skills)) * 30)
                score += int(skill_score)
            elif skill_matches >= 1:
                # Reduced points for 1-2 matches
                skill_score = min(15, (skill_matches / len(required_skills)) * 15)
                score += int(skill_score)
        
        # Company preference (10 points) - basic implementation
        # You can extend this with company blacklist/whitelist
        score += 10
        
        # Salary range matching (10 points) - if salary data available
        if job_details.get('salary') and hasattr(job_preferences, 'min_salary'):
            # Basic salary matching logic
            score += 10
        
        return min(score, max_score)
    
    def score_job_for_user(self, user_id: int, job_details: Dict[str, Any]) -> Dict[str, Any]:
        """Score a job for a specific user and return detailed results"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found', 'score': 0}
            
            job_preferences = JobPreferences.query.filter_by(user_id=user_id).first()
            if not job_preferences:
                return {'error': 'User preferences not found', 'score': 0}
            
            # Try AI scoring first
            ai_score = None
            if self.client:
                resume_text = self.format_user_resume_data(user, job_preferences)
                ai_score = self.get_ai_job_score(resume_text, job_details)
            
            # Fallback to basic scoring
            basic_score = self.get_basic_job_score(user, job_preferences, job_details)
            
            # Use AI score if available, otherwise use basic score
            final_score = ai_score if ai_score is not None else basic_score
            
            result = {
                'user_id': user_id,
                'job_title': job_details.get('job_title'),
                'company_name': job_details.get('company_name'),
                'score': final_score,
                'ai_score': ai_score,
                'basic_score': basic_score,
                'scoring_method': 'ai' if ai_score is not None else 'basic',
                'scored_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Job scored for user {user_id}: {final_score} ({result['scoring_method']})")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring job for user {user_id}: {e}")
            return {'error': str(e), 'score': 0}
    
    def batch_score_jobs(self, user_id: int, jobs_list: List[Dict[str, Any]], max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Score multiple jobs for a user"""
        scored_jobs = []
        
        for i, job_details in enumerate(jobs_list[:max_jobs]):
            try:
                score_result = self.score_job_for_user(user_id, job_details)
                scored_jobs.append(score_result)
                
                # Add delay between AI calls to respect rate limits
                if self.client and i > 0 and i % 10 == 0:
                    import time
                    time.sleep(2)  # 2 second delay every 10 jobs
                    
            except Exception as e:
                logger.error(f"Error scoring job {i}: {e}")
                continue
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Batch scored {len(scored_jobs)} jobs for user {user_id}")
        return scored_jobs
    
    def should_apply_to_job(self, score_result: Dict[str, Any], min_score_threshold: int = 70) -> bool:
        """Determine if user should apply to job based on score"""
        score = score_result.get('score', 0)
        return score >= min_score_threshold
    
    def get_application_priority(self, score_result: Dict[str, Any]) -> str:
        """Get application priority based on score"""
        score = score_result.get('score', 0)
        
        if score >= 90:
            return 'high'
        elif score >= 75:
            return 'medium'
        elif score >= 60:
            return 'low'
        else:
            return 'skip'
