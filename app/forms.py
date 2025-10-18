'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from app.models.user import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    
    # Professional Information
    experience_years = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=50)])
    current_salary = FloatField('Current Salary (LPA)', validators=[Optional(), NumberRange(min=0)])
    expected_salary = FloatField('Expected Salary (LPA)', validators=[Optional(), NumberRange(min=0)])
    skills = TextAreaField('Skills (comma separated)', validators=[Optional()])
    education = TextAreaField('Education', validators=[Optional()])
    achievements = TextAreaField('Achievements', validators=[Optional()])
    
    # Settings
    daily_application_limit = IntegerField('Daily Application Limit', 
                                         validators=[DataRequired(), NumberRange(min=1, max=50)], 
                                         default=10)
    
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')


class PlatformCredentialsForm(FlaskForm):
    # LinkedIn
    linkedin_username = StringField('LinkedIn Username/Email', validators=[Optional()])
    linkedin_password = PasswordField('LinkedIn Password', validators=[Optional()])
    
    # Indeed
    indeed_username = StringField('Indeed Username/Email', validators=[Optional()])
    indeed_password = PasswordField('Indeed Password', validators=[Optional()])
    
    # Naukri
    naukri_username = StringField('Naukri Username/Email', validators=[Optional()])
    naukri_password = PasswordField('Naukri Password', validators=[Optional()])
    
    # InternShala
    internshala_username = StringField('InternShala Username/Email', validators=[Optional()])
    internshala_password = PasswordField('InternShala Password', validators=[Optional()])
    
    submit = SubmitField('Save Credentials')


class JobPreferencesForm(FlaskForm):
    WORK_TYPE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance')
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (2-5 years)'),
        ('senior', 'Senior Level (5+ years)'),
        ('executive', 'Executive Level')
    ]
    
    preferred_job_titles = TextAreaField('Preferred Job Titles (one per line)', 
                                       validators=[DataRequired()])
    preferred_locations = TextAreaField('Preferred Locations (one per line)', 
                                      validators=[DataRequired()])
    work_type = SelectField('Work Type', choices=WORK_TYPE_CHOICES, 
                           validators=[DataRequired()])
    experience_level = SelectField('Experience Level', choices=EXPERIENCE_LEVEL_CHOICES, 
                                 validators=[DataRequired()])
    min_salary = FloatField('Minimum Salary (LPA)', validators=[Optional(), NumberRange(min=0)])
    max_salary = FloatField('Maximum Salary (LPA)', validators=[Optional(), NumberRange(min=0)])
    
    # Platform priorities
    linkedin_priority = SelectField('LinkedIn Priority', 
                                  choices=[('1', 'High'), ('2', 'Medium'), ('3', 'Low'), ('0', 'Disabled')],
                                  default='1')
    indeed_priority = SelectField('Indeed Priority', 
                                choices=[('1', 'High'), ('2', 'Medium'), ('3', 'Low'), ('0', 'Disabled')],
                                default='2')
    naukri_priority = SelectField('Naukri Priority', 
                                choices=[('1', 'High'), ('2', 'Medium'), ('3', 'Low'), ('0', 'Disabled')],
                                default='3')
    internshala_priority = SelectField('InternShala Priority', 
                                     choices=[('1', 'High'), ('2', 'Medium'), ('3', 'Low'), ('0', 'Disabled')],
                                     default='3')
    
    submit = SubmitField('Save Preferences')


class ResumeFileForm(FlaskForm):
    resume = FileField('Upload Resume', validators=[
        DataRequired(message='Please select a file.'),
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF, DOC, and DOCX files are allowed.')
    ])
    resume_name = StringField('Resume Name', validators=[
        DataRequired(message='Please provide a name for your resume.'),
        Length(min=3, max=100)
    ])
    is_primary = BooleanField('Set as Primary Resume', default=False)
    submit = SubmitField('Upload Resume')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('Repeat New Password',
                                validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')


class JobSetupForm(FlaskForm):
    """Comprehensive job setup form for new users"""

    # Job Search Preferences
    preferred_job_titles = TextAreaField('Job Titles You Are Looking For',
                                       validators=[DataRequired()],
                                       render_kw={'placeholder': 'Software Engineer\nPython Developer\nFull Stack Developer\n(One per line)'})

    preferred_locations = TextAreaField('Preferred Job Locations',
                                      validators=[DataRequired()],
                                      render_kw={'placeholder': 'Mumbai\nBangalore\nRemote\n(One per line)'})

    work_type = SelectField('Work Type', choices=[
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance')
    ], validators=[DataRequired()])

    work_mode = SelectField('Work Mode Preference', choices=[
        ('any', 'Any (Remote/Hybrid/Office)'),
        ('remote', 'Remote Only'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'Office Only')
    ], validators=[DataRequired()])

    experience_level = SelectField('Experience Level', choices=[
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (2-5 years)'),
        ('senior', 'Senior Level (5+ years)'),
        ('executive', 'Executive/Leadership')
    ], validators=[DataRequired()])

    # Skills
    required_skills = TextAreaField('Must-Have Skills',
                                  validators=[DataRequired()],
                                  render_kw={'placeholder': 'Python, JavaScript, React, SQL\n(Comma separated)'})

    preferred_skills = TextAreaField('Nice-to-Have Skills',
                                   validators=[Optional()],
                                   render_kw={'placeholder': 'AWS, Docker, Machine Learning\n(Comma separated)'})

    # Salary Expectations
    min_salary = FloatField('Minimum Expected Salary (LPA)',
                          validators=[DataRequired(), NumberRange(min=0)],
                          render_kw={'placeholder': '5.0'})

    max_salary = FloatField('Maximum Expected Salary (LPA)',
                          validators=[DataRequired(), NumberRange(min=0)],
                          render_kw={'placeholder': '15.0'})

    salary_negotiable = BooleanField('Salary is Negotiable', default=True)

    # Industry Preferences
    preferred_industries = SelectField('Preferred Industry', choices=[
        ('technology', 'Technology/IT'),
        ('finance', 'Finance/Banking'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('ecommerce', 'E-commerce'),
        ('consulting', 'Consulting'),
        ('manufacturing', 'Manufacturing'),
        ('media', 'Media/Entertainment'),
        ('government', 'Government/Public Sector'),
        ('nonprofit', 'Non-profit'),
        ('any', 'Any Industry')
    ], validators=[DataRequired()])

    company_size_preference = SelectField('Company Size Preference', choices=[
        ('any', 'Any Size'),
        ('startup', 'Startup (1-50 employees)'),
        ('small', 'Small (51-200 employees)'),
        ('medium', 'Medium (201-1000 employees)'),
        ('large', 'Large (1000+ employees)')
    ], validators=[DataRequired()])

    # Application Settings
    max_applications_per_day = IntegerField('Maximum Applications Per Day',
                                          validators=[DataRequired(), NumberRange(min=1, max=50)],
                                          default=10)

    application_priority = SelectField('Application Strategy', choices=[
        ('quality', 'Quality - Apply to fewer, better-matched jobs'),
        ('balanced', 'Balanced - Mix of quality and quantity'),
        ('quantity', 'Quantity - Apply to more jobs with lower match threshold')
    ], validators=[DataRequired()], default='balanced')

    # Platform Priorities
    linkedin_priority = SelectField('LinkedIn Priority', choices=[
        ('1', 'High Priority'),
        ('2', 'Medium Priority'),
        ('3', 'Low Priority'),
        ('0', 'Disabled')
    ], default='1')

    indeed_priority = SelectField('Indeed Priority', choices=[
        ('1', 'High Priority'),
        ('2', 'Medium Priority'),
        ('3', 'Low Priority'),
        ('0', 'Disabled')
    ], default='2')

    naukri_priority = SelectField('Naukri Priority', choices=[
        ('1', 'High Priority'),
        ('2', 'Medium Priority'),
        ('3', 'Low Priority'),
        ('0', 'Disabled')
    ], default='3')

    internshala_priority = SelectField('InternShala Priority', choices=[
        ('1', 'High Priority'),
        ('2', 'Medium Priority'),
        ('3', 'Low Priority'),
        ('0', 'Disabled')
    ], default='3')

    # Availability
    notice_period = IntegerField('Notice Period (Days)',
                               validators=[Optional(), NumberRange(min=0, max=365)],
                               default=30)

    # Resume Upload
    resume_file = FileField('Upload Your Resume', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF, DOC, and DOCX files allowed!')
    ])

    resume_name = StringField('Resume Name',
                            validators=[DataRequired(), Length(max=100)],
                            render_kw={'placeholder': 'My Resume - Software Engineer'})

    # Agreement
    terms_agreement = BooleanField('I agree to AutoHire Terms of Service and Privacy Policy',
                                 validators=[DataRequired()])

    auto_apply_consent = BooleanField('I consent to AutoHire automatically applying to jobs on my behalf',
                                    validators=[DataRequired()])

    submit = SubmitField('Complete Setup & Start Auto-Applying')


class QuickJobPreferencesForm(FlaskForm):
    """Simplified form for updating job preferences"""

    preferred_job_titles = TextAreaField('Job Titles', validators=[DataRequired()])
    preferred_locations = TextAreaField('Locations', validators=[DataRequired()])
    work_type = SelectField('Work Type', choices=[
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance')
    ], validators=[DataRequired()])

    min_salary = FloatField('Min Salary (LPA)', validators=[DataRequired(), NumberRange(min=0)])
    max_salary = FloatField('Max Salary (LPA)', validators=[DataRequired(), NumberRange(min=0)])

    required_skills = TextAreaField('Required Skills', validators=[DataRequired()])
    max_applications_per_day = IntegerField('Max Applications/Day',
                                          validators=[DataRequired(), NumberRange(min=1, max=50)])

    submit = SubmitField('Update Preferences')
