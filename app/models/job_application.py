'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from app import db
from datetime import datetime

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Job Details
    job_title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))
    job_description = db.Column(db.Text)
    salary = db.Column(db.String(100))
    work_type = db.Column(db.String(50))  # Full-time, Part-time, Contract, etc.
    location = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    job_url = db.Column(db.String(500))
    
    # Platform Info
    platform = db.Column(db.String(50), nullable=False)  # linkedin, indeed, naukri, internshala
    platform_job_id = db.Column(db.String(100))
    
    # Application Status
    status = db.Column(db.String(50), default='applied')  # applied, rejected, interview, hired, error
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    response_date = db.Column(db.DateTime)
    
    # Automation Details
    auto_applied = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    resume_used = db.Column(db.String(200))
    cover_letter_used = db.Column(db.Text)
    
    # Additional Fields
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<JobApplication {self.job_title} at {self.company_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_title': self.job_title,
            'company_name': self.company_name,
            'job_description': self.job_description,
            'salary': self.salary,
            'work_type': self.work_type,
            'location': self.location,
            'requirements': self.requirements,
            'platform': self.platform,
            'status': self.status,
            'application_date': self.application_date.strftime('%Y-%m-%d %H:%M:%S') if self.application_date else None,
            'response_date': self.response_date.strftime('%Y-%m-%d %H:%M:%S') if self.response_date else None,
            'auto_applied': self.auto_applied,
            'resume_used': self.resume_used,
            'notes': self.notes
        }
