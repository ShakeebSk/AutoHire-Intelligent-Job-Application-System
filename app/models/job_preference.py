'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from app import db
from datetime import datetime
import json


class JobPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Job Search Preferences
    preferred_job_titles = db.Column(db.Text)  # JSON list of job titles
    preferred_companies = db.Column(db.Text)  # JSON list of companies (optional)
    preferred_locations = db.Column(db.Text)  # JSON list of locations
    work_type = db.Column(db.String(50))  # full-time, part-time, contract, internship, freelance
    work_mode = db.Column(db.String(50))  # remote, hybrid, onsite, any
    
    # Experience and Skills
    experience_level = db.Column(db.String(50))  # entry, mid, senior, executive
    required_skills = db.Column(db.Text)  # JSON list of must-have skills
    preferred_skills = db.Column(db.Text)  # JSON list of nice-to-have skills
    avoid_skills = db.Column(db.Text)  # JSON list of skills to avoid
    
    # Salary and Benefits
    min_salary = db.Column(db.Float)
    max_salary = db.Column(db.Float)
    salary_negotiable = db.Column(db.Boolean, default=True)
    currency = db.Column(db.String(10), default='INR')
    
    # Industry and Company Preferences
    preferred_industries = db.Column(db.Text)  # JSON list
    company_size_preference = db.Column(db.String(50))  # startup, small, medium, large, any
    avoid_companies = db.Column(db.Text)  # JSON list of companies to avoid
    
    # Application Preferences
    auto_apply_enabled = db.Column(db.Boolean, default=True)
    max_applications_per_day = db.Column(db.Integer, default=10)
    application_priority = db.Column(db.String(50), default='quality')  # quality, quantity, balanced
    
    # Platform Priorities (1=highest, 5=disabled)
    linkedin_priority = db.Column(db.Integer, default=1)
    indeed_priority = db.Column(db.Integer, default=2)
    naukri_priority = db.Column(db.Integer, default=3)
    internshala_priority = db.Column(db.Integer, default=4)
    
    # Availability
    available_start_date = db.Column(db.Date)
    notice_period = db.Column(db.Integer)  # in days
    
    # Matching Criteria
    job_match_threshold = db.Column(db.Float, default=0.7)  # 0.0 to 1.0
    skills_match_weight = db.Column(db.Float, default=0.4)
    location_match_weight = db.Column(db.Float, default=0.3)
    salary_match_weight = db.Column(db.Float, default=0.3)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('job_preferences', uselist=False))
    
    def set_preferred_job_titles(self, titles_list):
        """Set preferred job titles as JSON"""
        self.preferred_job_titles = json.dumps(titles_list)
    
    def get_preferred_job_titles(self):
        """Get preferred job titles as list"""
        if self.preferred_job_titles:
            return json.loads(self.preferred_job_titles)
        return []
    
    def set_preferred_locations(self, locations_list):
        """Set preferred locations as JSON"""
        self.preferred_locations = json.dumps(locations_list)
    
    def get_preferred_locations(self):
        """Get preferred locations as list"""
        if self.preferred_locations:
            return json.loads(self.preferred_locations)
        return []
    
    def set_required_skills(self, skills_list):
        """Set required skills as JSON"""
        self.required_skills = json.dumps(skills_list)
    
    def get_required_skills(self):
        """Get required skills as list"""
        if self.required_skills:
            return json.loads(self.required_skills)
        return []
    
    def set_preferred_skills(self, skills_list):
        """Set preferred skills as JSON"""
        self.preferred_skills = json.dumps(skills_list)
    
    def get_preferred_skills(self):
        """Get preferred skills as list"""
        if self.preferred_skills:
            return json.loads(self.preferred_skills)
        return []
    
    def set_preferred_industries(self, industries_list):
        """Set preferred industries as JSON"""
        self.preferred_industries = json.dumps(industries_list)
    
    def get_preferred_industries(self):
        """Get preferred industries as list"""
        if self.preferred_industries:
            return json.loads(self.preferred_industries)
        return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_job_titles': self.get_preferred_job_titles(),
            'preferred_locations': self.get_preferred_locations(),
            'work_type': self.work_type,
            'work_mode': self.work_mode,
            'experience_level': self.experience_level,
            'required_skills': self.get_required_skills(),
            'preferred_skills': self.get_preferred_skills(),
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'preferred_industries': self.get_preferred_industries(),
            'auto_apply_enabled': self.auto_apply_enabled,
            'max_applications_per_day': self.max_applications_per_day,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Resume Information
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # in bytes
    file_type = db.Column(db.String(50))  # pdf, doc, docx
    
    # Resume Details
    resume_name = db.Column(db.String(200))  # user-given name
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Parsed Information (extracted from resume)
    parsed_text = db.Column(db.Text)  # extracted text content
    parsed_skills = db.Column(db.Text)  # JSON list of extracted skills
    parsed_experience = db.Column(db.Text)  # JSON list of work experience
    parsed_education = db.Column(db.Text)  # JSON list of education
    parsed_certifications = db.Column(db.Text)  # JSON list of certifications
    
    # Usage Statistics
    times_used = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    success_rate = db.Column(db.Float, default=0.0)  # calculated based on application responses
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('resumes', lazy='dynamic'))
    
    def set_parsed_skills(self, skills_list):
        """Set parsed skills as JSON"""
        self.parsed_skills = json.dumps(skills_list)
    
    def get_parsed_skills(self):
        """Get parsed skills as list"""
        if self.parsed_skills:
            return json.loads(self.parsed_skills)
        return []
    
    def set_parsed_experience(self, experience_list):
        """Set parsed experience as JSON"""
        self.parsed_experience = json.dumps(experience_list)
    
    def get_parsed_experience(self):
        """Get parsed experience as list"""
        if self.parsed_experience:
            return json.loads(self.parsed_experience)
        return []
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'resume_name': self.resume_name,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size_mb': self.get_file_size_mb(),
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'times_used': self.times_used,
            'success_rate': self.success_rate,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'parsed_skills': self.get_parsed_skills()
        }
