'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.utils.security import encrypt_password, decrypt_password


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    
    # Personal Information
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    
    # Professional Information
    experience_years = db.Column(db.Integer, default=0)
    current_salary = db.Column(db.Float)
    expected_salary = db.Column(db.Float)
    skills = db.Column(db.Text)  # JSON string of skills
    education = db.Column(db.Text)
    achievements = db.Column(db.Text)
    
    # Platform Credentials (encrypted)
    linkedin_username = db.Column(db.String(100))
    linkedin_password = db.Column(db.LargeBinary)
    indeed_username = db.Column(db.String(100))
    indeed_password = db.Column(db.LargeBinary)
    naukri_username = db.Column(db.String(100))
    naukri_password = db.Column(db.LargeBinary)
    internshala_username = db.Column(db.String(100))
    internshala_password = db.Column(db.LargeBinary)
    
    # Settings
    daily_application_limit = db.Column(db.Integer, default=10)
    platform_priorities = db.Column(db.Text)  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    job_applications = db.relationship('JobApplication', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_platform_password(self, platform, password):
        encrypted_password = encrypt_password(password)
        if platform == 'linkedin':
            self.linkedin_password = encrypted_password
        elif platform == 'indeed':
            self.indeed_password = encrypted_password
        elif platform == 'naukri':
            self.naukri_password = encrypted_password
        elif platform == 'internshala':
            self.internshala_password = encrypted_password

    def get_platform_password(self, platform):
        if platform == 'linkedin':
            return decrypt_password(self.linkedin_password)
        elif platform == 'indeed':
            return decrypt_password(self.indeed_password)
        elif platform == 'naukri':
            return decrypt_password(self.naukri_password)
        elif platform == 'internshala':
            return decrypt_password(self.internshala_password)
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'
