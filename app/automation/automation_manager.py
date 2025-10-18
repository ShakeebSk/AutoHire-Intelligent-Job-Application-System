"""
Automation Manager - Integrates job automation with database


Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk


"""

import logging
from datetime import datetime, date
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.job_preferences import JobPreferences
from app.automation.scrapers.linkedin_automation import LinkedInAutomation
from app.automation.scrapers.indeed_automation import IndeedAutomation
# from app.automation.scrapers.naukri_automation import NaukriAutomation
# from app.automation.scrapers.internshala_automation import InternshalaAutomation
import json


class AutomationManager:
    """Manages job automation with database integration"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        self.job_preferences = JobPreferences.query.filter_by(user_id=user_id).first()
        self.logger = logging.getLogger(__name__)
        
        # Automation instances
        self.linkedin_bot = None
        self.indeed_bot = None
        
        # Session tracking
        self.session_stats = {
            'total_searched': 0,
            'total_applied': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'errors': []
        }
    
    def initialize_bots(self):
        """Initialize automation bots with user credentials"""
        try:
            # Initialize LinkedIn bot
            if self.user.linkedin_username and self.user.linkedin_password:
                linkedin_password = self.user.get_platform_password('linkedin')
                if linkedin_password:
                    self.linkedin_bot = LinkedInAutomation(
                        self.user.linkedin_username, 
                        linkedin_password,
                        headless=True
                    )
                    self.linkedin_bot.setup_driver()
                    self.logger.info("LinkedIn bot initialized")
                else:
                    self.logger.warning("LinkedIn password could not be decrypted")
            
            # Initialize Indeed bot
            if self.user.indeed_username and self.user.indeed_password:
                indeed_password = self.user.get_platform_password('indeed')
                if indeed_password:
                    self.indeed_bot = IndeedAutomation(
                        self.user.indeed_username,
                        indeed_password,
                        headless=True
                    )
                    self.indeed_bot.setup_driver()
                    self.logger.info("Indeed bot initialized")
                else:
                    self.logger.warning("Indeed password could not be decrypted")
                
        except Exception as e:
            self.logger.error(f"Error initializing bots: {str(e)}")
            raise
    
    def cleanup_bots(self):
        """Cleanup automation bots"""
        try:
            if self.linkedin_bot:
                self.linkedin_bot.cleanup()
            if self.indeed_bot:
                self.indeed_bot.cleanup()
        except Exception as e:
            self.logger.error(f"Error cleaning up bots: {str(e)}")
    
    def check_daily_limit(self):
        """Check if user has reached daily application limit"""
        today = date.today()
        today_applications = JobApplication.query.filter(
            JobApplication.user_id == self.user_id,
            db.func.date(JobApplication.application_date) == today
        ).count()
        
        daily_limit = self.user.daily_application_limit or 10
        return today_applications, daily_limit
    
    def get_user_search_criteria(self):
        """Get user's job search criteria"""
        if not self.job_preferences:
            return None
            
        return {
            'job_titles': self.job_preferences.get_preferred_job_titles(),
            'locations': self.job_preferences.get_preferred_locations(),
            'required_skills': self.job_preferences.get_required_skills(),
            'min_salary': self.job_preferences.min_salary,
            'max_salary': self.job_preferences.max_salary,
            'work_type': self.job_preferences.work_type,
            'work_mode': self.job_preferences.work_mode,
            'experience_level': self.job_preferences.experience_level
        }
    
    def get_platform_priorities(self):
        """Get platform priorities from user preferences"""
        if not self.job_preferences:
            return {'linkedin': 1, 'indeed': 2, 'naukri': 3, 'internshala': 4}
            
        return {
            'linkedin': self.job_preferences.linkedin_priority,
            'indeed': self.job_preferences.indeed_priority,
            'naukri': self.job_preferences.naukri_priority,
            'internshala': self.job_preferences.internshala_priority
        }
    
    def save_job_application(self, job_details, application_result):
        """Save job application to database"""
        try:
            # Check if application already exists
            existing_app = JobApplication.query.filter_by(
                user_id=self.user_id,
                platform_job_id=job_details.get('platform_job_id'),
                platform=job_details.get('platform')
            ).first()
            
            if existing_app:
                self.logger.warning(f"Application already exists for job {job_details.get('platform_job_id')}")
                return existing_app
            
            # Create new job application record
            job_app = JobApplication(
                user_id=self.user_id,
                job_title=job_details.get('job_title', ''),
                company_name=job_details.get('company_name', ''),
                job_description=job_details.get('job_description', ''),
                salary=job_details.get('salary', ''),
                work_type=job_details.get('work_type', ''),
                location=job_details.get('location', ''),
                requirements=job_details.get('requirements', ''),
                job_url=job_details.get('job_url', ''),
                platform=job_details.get('platform', ''),
                platform_job_id=job_details.get('platform_job_id', ''),
                status='applied' if application_result['success'] else 'error',
                application_date=datetime.utcnow(),
                auto_applied=True,
                error_message=application_result.get('error', '') if not application_result['success'] else None,
                resume_used=self._get_primary_resume_name(),
                cover_letter_used=None  # Can be implemented later
            )
            
            db.session.add(job_app)
            db.session.commit()
            
            self.logger.info(f"Saved application: {job_details.get('job_title')} at {job_details.get('company_name')}")
            return job_app
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error saving application: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error saving application: {str(e)}")
            raise
    
    def _get_primary_resume_name(self):
        """Get primary resume filename"""
        try:
            from app.models.job_preferences import Resume
            primary_resume = Resume.query.filter_by(
                user_id=self.user_id,
                is_primary=True,
                is_active=True
            ).first()
            
            return primary_resume.filename if primary_resume else None
        except Exception:
            return None
    
    def _get_primary_resume_path(self):
        """Get primary resume file path"""
        try:
            from app.models.job_preferences import Resume
            primary_resume = Resume.query.filter_by(
                user_id=self.user_id,
                is_primary=True,
                is_active=True
            ).first()
            
            return primary_resume.file_path if primary_resume else None
        except Exception:
            return None
    
    def _get_user_skills(self):
        """Get user skills from profile and job preferences"""
        try:
            skills = []
            
            # Get skills from user profile
            if self.user.skills:
                try:
                    # Try to parse as JSON first
                    user_skills = json.loads(self.user.skills)
                    if isinstance(user_skills, list):
                        skills.extend(user_skills)
                    else:
                        skills.extend([self.user.skills])
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, treat as comma-separated string
                    skills.extend([skill.strip() for skill in self.user.skills.split(',')])
            
            # Get required skills from job preferences
            if self.job_preferences:
                required_skills = self.job_preferences.get_required_skills()
                if required_skills:
                    skills.extend(required_skills)
                
                preferred_skills = self.job_preferences.get_preferred_skills()
                if preferred_skills:
                    skills.extend(preferred_skills)
            
            # Remove duplicates and return
            return list(set(skill.strip() for skill in skills if skill.strip()))
            
        except Exception as e:
            self.logger.error(f"Error getting user skills: {str(e)}")
            return []
    
    def _get_user_application_data(self):
        """Get user data needed for job applications"""
        try:
            # Parse full name into first and last name
            first_name = ''
            last_name = ''
            if self.user.full_name:
                name_parts = self.user.full_name.strip().split()
                if len(name_parts) >= 1:
                    first_name = name_parts[0]
                if len(name_parts) >= 2:
                    last_name = ' '.join(name_parts[1:])
            
            user_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': self.user.email or '',
                'phone': self.user.phone or '',
                'location': self.user.location or '',
                'resume_path': self._get_primary_resume_path(),
                'experience_years': self.user.experience_years or 0,
                'current_salary': self.user.current_salary,
                'expected_salary': self.user.expected_salary,
                'skills': self._get_user_skills(),
                'education': self.user.education or '',
                'achievements': self.user.achievements or ''
            }
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"Error getting user application data: {str(e)}")
            return {}
    
    def job_matches_preferences(self, job_details):
        """Check if job matches user preferences - using same logic as LinkedIn automation"""
        if not self.job_preferences:
            return True
            
        try:
            self.logger.info(f"\n=== AUTOMATION MANAGER MATCHING: {job_details.get('job_title', 'N/A')} ===")
            
            # Check job title - use word-based matching for better results
            preferred_titles = [title.lower() for title in self.job_preferences.get_preferred_job_titles()]
            job_title_lower = job_details.get('job_title', '').lower()
            
            self.logger.info(f"Job title (lowercase): '{job_title_lower}'")
            self.logger.info(f"Preferred titles: {preferred_titles}")
            
            # Split job titles into words and match any two words
            preferred_words = {word for title in preferred_titles for word in title.split()}
            job_title_words = set(job_title_lower.split())
            word_matches = preferred_words.intersection(job_title_words)
            
            self.logger.info(f"Preferred words: {preferred_words}")
            self.logger.info(f"Job title words: {job_title_words}")
            self.logger.info(f"Word matches found: {word_matches} (count: {len(word_matches)})")
            
            title_match = len(word_matches) >= 2
            if not title_match:
                self.logger.info(f" TITLE MATCH FAILED: Need 2+ word matches, found {len(word_matches)}")
                # Let's try a more lenient approach - check if any preferred title contains job words or vice versa
                fallback_match = any(
                    any(word in title for word in job_title_words if len(word) > 2) 
                    for title in preferred_titles
                ) or any(
                    any(word in job_title_lower for word in title.split() if len(word) > 2)
                    for title in preferred_titles
                )
                if fallback_match:
                    self.logger.info(f" FALLBACK TITLE MATCH: Found partial match")
                    title_match = True
                else:
                    return False
            else:
                self.logger.info(f" TITLE MATCH SUCCESS: {len(word_matches)} words matched")
            
            # Check location preferences
            preferred_locations = [loc.lower() for loc in self.job_preferences.get_preferred_locations()]
            job_location_lower = job_details.get('location', '').lower()
            
            self.logger.info(f"Job location: '{job_location_lower}'")
            self.logger.info(f"Preferred locations: {preferred_locations}")
            
            location_match = any(loc in job_location_lower or job_location_lower in loc for loc in preferred_locations)
            if not location_match:
                self.logger.info(f" LOCATION MATCH FAILED: Job location '{job_details.get('location', '')}' doesn't match {preferred_locations}")
                # For testing, let's be more lenient with location matching
                if not preferred_locations or any(loc.strip() == '' for loc in preferred_locations):
                    self.logger.info(f" LOCATION MATCH: No specific location requirement")
                    location_match = True
                elif 'remote' in job_location_lower or 'work from home' in job_location_lower:
                    self.logger.info(f" LOCATION MATCH: Remote work accepted")
                    location_match = True
                else:
                    return False
            else:
                self.logger.info(f" LOCATION MATCH SUCCESS")
            
            # Check required skills - require at least 3 skill matches
            required_skills = [skill.lower() for skill in self.job_preferences.get_required_skills()]
            if required_skills and job_details.get('job_description'):
                job_description_lower = job_details.get('job_description', '').lower()
                
                # More intelligent skill matching
                matched_skills = []
                for skill in required_skills:
                    if skill.lower() in job_description_lower:
                        matched_skills.append(skill)
                
                self.logger.info(f"Required skills: {required_skills[:10]}...")  # Show first 10
                self.logger.info(f"Matched skills: {matched_skills}")
                self.logger.info(f"Skill match count: {len(matched_skills)}")
                
                skill_match_count = len(matched_skills)
                if skill_match_count < 3:
                    self.logger.info(f" SKILL MATCH FAILED: Need 3+ skills, found {skill_match_count}")
                    # Let's be more lenient - check for 1+ skills for now
                    if skill_match_count >= 1:
                        self.logger.info(f" RELAXED SKILL MATCH: Found {skill_match_count} skill(s)")
                    else:
                        self.logger.info(f" NO SKILLS MATCHED AT ALL")
                        return False
                else:
                    self.logger.info(f" SKILL MATCH SUCCESS: {skill_match_count} skills matched")
            else:
                self.logger.info(f"⚠️ No required skills defined or no job description available")
            
            self.logger.info(f" JOB MATCH SUCCESS: '{job_details.get('job_title', '')}' matches user preferences")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking job preferences: {str(e)}")
            return True  # Default to True if error
    
    def run_automation_for_platform(self, platform_bot, platform_name, search_criteria, applications_limit, stop_event=None):
        """Run automation for a specific platform with stop event support"""
        applications_made = 0
        
        try:
            # Check if stopped before login
            if stop_event and stop_event.is_set():
                return applications_made
            
            self.session_stats['current_action'] = f'Logging into {platform_name.title()}...'
            
            # Login to platform
            if not platform_bot.login():
                self.logger.error(f"Failed to login to {platform_name}")
                return applications_made
            
            self.logger.info(f"Successfully logged into {platform_name}")
            
            # Search and apply for each job title and location combination
            for job_title in search_criteria.get('job_titles', []):
                for location in search_criteria.get('locations', []):
                    # Check if stopped
                    if stop_event and stop_event.is_set():
                        return applications_made
                    
                    if applications_made >= applications_limit:
                        break
                    
                    try:
                        # Update current action
                        self.session_stats['current_action'] = f'Searching {platform_name.title()} for "{job_title}" in "{location}" with Easy Apply filter'
                        
                        # Create filter for Easy Apply jobs only
                        search_filters = {'easy_apply': True}
                        
                        # Search for jobs with mandatory Easy Apply filter
                        self.logger.info(f"Searching {platform_name} for '{job_title}' in '{location}' with Easy Apply filter")
                        jobs = platform_bot.search_jobs(job_title, location, filters=search_filters)
                        
                        if not jobs:
                            self.logger.info(f"No jobs found for '{job_title}' in '{location}'")
                            continue
                            
                        self.session_stats['total_searched'] += len(jobs)
                        self.logger.info(f" Found {len(jobs)} jobs, starting sequential processing...")
                        
                        # Use LinkedIn's built-in sequential processing instead of manual iteration
                        if hasattr(platform_bot, 'process_jobs_sequentially'):
                            # Get user data for sequential processing
                            user_data = self._get_user_application_data()
                            
                            # Update current action
                            self.session_stats['current_action'] = f'Processing {len(jobs)} jobs sequentially with AI assistance...'
                            
                            # Use LinkedIn's optimized sequential processing
                            processing_result = platform_bot.process_jobs_sequentially(
                                user_preferences=self.job_preferences,
                                user_skills=self._get_user_skills(),
                                user_data=user_data,
                                max_applications=applications_limit - applications_made
                            )
                            
                            if processing_result['success']:
                                apps_made_this_search = processing_result['applications_made']
                                applications_made += apps_made_this_search
                                
                                # Update session stats
                                self.session_stats['successful_applications'] += apps_made_this_search
                                self.session_stats['total_applied'] += apps_made_this_search
                                
                                self.logger.info(f" Sequential processing completed: {apps_made_this_search} applications made")
                            else:
                                self.logger.warning(f"⚠️ Sequential processing had issues: {processing_result.get('error', 'Unknown error')}")
                                self.session_stats['errors'].append(processing_result.get('error', 'Sequential processing failed'))
                        
                        else:
                            # Fallback to manual iteration for platforms without sequential processing
                            self.logger.info("Using fallback manual job iteration...")
                            
                            for job_element in jobs:
                                # Check if stopped
                                if stop_event and stop_event.is_set():
                                    return applications_made
                                
                                if applications_made >= applications_limit:
                                    break
                                
                                try:
                                    # Extract job details
                                    job_details = platform_bot.extract_job_details(job_element)
                                    if not job_details:
                                        continue
                                    
                                    # Update current action
                                    self.session_stats['current_action'] = f'Evaluating job: {job_details.get("job_title", "Unknown")} at {job_details.get("company_name", "Unknown")}'
                                    
                                    # Check if job matches user preferences
                                    if not self.job_matches_preferences(job_details):
                                        self.logger.info(f"Job doesn't match preferences: {job_details.get('job_title')}")
                                        continue
                                    
                                    # Check if already applied to this job
                                    existing_app = JobApplication.query.filter_by(
                                        user_id=self.user_id,
                                        platform_job_id=job_details.get('platform_job_id'),
                                        platform=platform_name
                                    ).first()
                                    
                                    if existing_app:
                                        self.logger.info(f"Already applied to: {job_details.get('job_title')}")
                                        continue
                                    
                                    # Update current action for application
                                    self.session_stats['current_action'] = f'Applying to: {job_details.get("job_title", "Unknown")} at {job_details.get("company_name", "Unknown")}'
                                    
                                    # Get user data for application
                                    user_data = self._get_user_application_data()
                                    
                                    # Apply to job with proper parameters
                                    self.logger.info(f"Applying to: {job_details.get('job_title')} at {job_details.get('company_name')}")
                                    application_result = platform_bot.apply_to_job(
                                        job_element, 
                                        user_preferences=self.job_preferences,
                                        user_skills=self._get_user_skills(),
                                        user_data=user_data
                                    )
                                    
                                    # Save to database
                                    saved_app = self.save_job_application(job_details, application_result)
                                    
                                    # Update session stats
                                    self.session_stats['total_applied'] += 1
                                    if application_result['success']:
                                        self.session_stats['successful_applications'] += 1
                                        applications_made += 1
                                        self.logger.info(f" Successfully applied and saved: {job_details.get('job_title')}")
                                    else:
                                        self.session_stats['failed_applications'] += 1
                                        self.logger.warning(f" Application failed: {application_result.get('error')}")
                                    
                                    # Add delay between applications
                                    platform_bot.random_delay(3, 6)
                                    
                                except Exception as e:
                                    self.logger.error(f"Error processing job: {str(e)}")
                                    self.session_stats['errors'].append(str(e))
                                    continue
                        
                        # Add delay between searches
                        platform_bot.random_delay(2, 4)
                        
                    except Exception as e:
                        self.logger.error(f"Error searching {platform_name}: {str(e)}")
                        self.session_stats['errors'].append(str(e))
                        continue
                
                if applications_made >= applications_limit:
                    break
        
        except Exception as e:
            self.logger.error(f"Error running automation for {platform_name}: {str(e)}")
            self.session_stats['errors'].append(str(e))
        
        return applications_made
    
    def run_full_automation(self, stop_event=None):
        """Run full automation process with stop event support"""
        try:
            self.session_stats['status'] = 'initializing'
            self.session_stats['current_action'] = 'Checking daily limits and preferences...'
            
            # Check if stopped
            if stop_event and stop_event.is_set():
                return self._get_stopped_result()
            
            # Check daily limit
            today_apps, daily_limit = self.check_daily_limit()
            if today_apps >= daily_limit:
                self.logger.info(f"Daily limit of {daily_limit} applications already reached")
                return {
                    'success': False,
                    'message': f'Daily limit of {daily_limit} applications already reached',
                    'stats': self.session_stats
                }
            
            remaining_applications = daily_limit - today_apps
            self.logger.info(f"Can apply to {remaining_applications} more jobs today")
            
            # Get user preferences
            search_criteria = self.get_user_search_criteria()
            if not search_criteria:
                return {
                    'success': False,
                    'message': 'No job preferences found. Please set up your preferences first.',
                    'stats': self.session_stats
                }
            
            # Check if stopped
            if stop_event and stop_event.is_set():
                return self._get_stopped_result()
            
            self.session_stats['current_action'] = 'Initializing automation bots...'
            
            # Initialize bots
            self.initialize_bots()
            
            # Get platform priorities
            priorities = self.get_platform_priorities()
            
            # Sort platforms by priority (lower number = higher priority)
            sorted_platforms = sorted(priorities.items(), key=lambda x: x[1])
            
            total_applications_made = 0
            
            # Run automation for each platform in priority order
            for platform_name, priority in sorted_platforms:
                if priority == 0:  # Skip disabled platforms
                    continue
                
                # Check if stopped
                if stop_event and stop_event.is_set():
                    self.cleanup_bots()
                    return self._get_stopped_result()
                    
                if total_applications_made >= remaining_applications:
                    break
                
                self.session_stats['current_action'] = f'Processing {platform_name.title()} platform...'
                platform_limit = min(5, remaining_applications - total_applications_made)  # Max 5 per platform
                
                if platform_name == 'linkedin' and self.linkedin_bot:
                    apps_made = self.run_automation_for_platform(
                        self.linkedin_bot, 'linkedin', search_criteria, platform_limit, stop_event
                    )
                    total_applications_made += apps_made
                    
                elif platform_name == 'indeed' and self.indeed_bot:
                    apps_made = self.run_automation_for_platform(
                        self.indeed_bot, 'indeed', search_criteria, platform_limit, stop_event
                    )
                    total_applications_made += apps_made
            
            # Cleanup
            self.cleanup_bots()
            
            # Check if stopped during cleanup
            if stop_event and stop_event.is_set():
                return self._get_stopped_result()
            
            self.session_stats['status'] = 'completed'
            self.session_stats['current_action'] = f'Automation completed successfully!'
            
            # Return results
            return {
                'success': True,
                'message': f'Automation completed. Applied to {total_applications_made} jobs.',
                'stats': self.session_stats,
                'applications_made': total_applications_made
            }
            
        except Exception as e:
            self.logger.error(f"Error running full automation: {str(e)}")
            self.cleanup_bots()
            self.session_stats['status'] = 'error'
            self.session_stats['current_action'] = f'Error: {str(e)}'
            return {
                'success': False,
                'message': f'Automation failed: {str(e)}',
                'stats': self.session_stats
            }
    
    def _get_stopped_result(self):
        """Get result when automation is stopped"""
        self.session_stats['status'] = 'stopped'
        self.session_stats['current_action'] = 'Automation stopped by user'
        return {
            'success': False,
            'message': 'Automation stopped by user',
            'stats': self.session_stats
        }
    
    def get_session_summary(self):
        """Get summary of current session"""
        return {
            'user_id': self.user_id,
            'username': self.user.username,
            'session_stats': self.session_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
