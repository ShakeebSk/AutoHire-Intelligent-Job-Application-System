'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''


import os
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.setup import bp
from app.forms import JobSetupForm
from app.models.job_preferences import JobPreferences, Resume
from datetime import datetime


@bp.route('/job-preferences', methods=['GET', 'POST'])
@login_required
def job_preferences():
    """Complete job preferences setup for new users."""
    
    # Check if user already has preferences set up
    existing_preferences = JobPreferences.query.filter_by(user_id=current_user.id).first()
    
    form = JobSetupForm()
    
    if form.validate_on_submit():
        try:
            # Create or update job preferences
            if existing_preferences:
                preferences = existing_preferences
            else:
                preferences = JobPreferences(user_id=current_user.id)
            
            # Process job titles
            job_titles = [title.strip() for title in form.preferred_job_titles.data.split('\n') if title.strip()]
            preferences.set_preferred_job_titles(job_titles)
            
            # Process locations
            locations = [loc.strip() for loc in form.preferred_locations.data.split('\n') if loc.strip()]
            preferences.set_preferred_locations(locations)
            
            # Basic job preferences
            preferences.work_type = form.work_type.data
            preferences.work_mode = form.work_mode.data
            preferences.experience_level = form.experience_level.data
            
            # Process skills
            required_skills = [skill.strip() for skill in form.required_skills.data.split(',') if skill.strip()]
            preferences.set_required_skills(required_skills)
            
            if form.preferred_skills.data:
                preferred_skills = [skill.strip() for skill in form.preferred_skills.data.split(',') if skill.strip()]
                preferences.set_preferred_skills(preferred_skills)
            
            # Salary and benefits
            preferences.min_salary = form.min_salary.data
            preferences.max_salary = form.max_salary.data
            preferences.salary_negotiable = form.salary_negotiable.data
            
            # Industry and company preferences
            preferences.set_preferred_industries([form.preferred_industries.data])
            preferences.company_size_preference = form.company_size_preference.data
            
            # Application settings
            preferences.max_applications_per_day = form.max_applications_per_day.data
            preferences.application_priority = form.application_priority.data
            preferences.auto_apply_enabled = form.auto_apply_consent.data
            
            # Platform priorities
            preferences.linkedin_priority = int(form.linkedin_priority.data)
            preferences.indeed_priority = int(form.indeed_priority.data)
            preferences.naukri_priority = int(form.naukri_priority.data)
            preferences.internshala_priority = int(form.internshala_priority.data)
            
            # Availability
            preferences.notice_period = form.notice_period.data
            
            # Handle resume upload
            if form.resume_file.data:
                file = form.resume_file.data
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_extension = filename.rsplit('.', 1)[1].lower()
                    
                    # Create unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"resume_{current_user.id}_{timestamp}.{file_extension}"
                    
                    # Ensure upload directory exists
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    # Create resume record
                    resume = Resume(
                        user_id=current_user.id,
                        filename=unique_filename,
                        original_filename=filename,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        file_type=file_extension,
                        resume_name=form.resume_name.data,
                        is_primary=True  # First resume is primary
                    )
                    
                    db.session.add(resume)
            
            # Save preferences
            if not existing_preferences:
                db.session.add(preferences)
            
            db.session.commit()
            
            flash('Your job preferences have been saved successfully! AutoHire is now ready to start applying to jobs for you.', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while saving your preferences: {str(e)}', 'error')
    
    # Pre-populate form if user has existing data
    if existing_preferences and request.method == 'GET':
        form.preferred_job_titles.data = '\n'.join(existing_preferences.get_preferred_job_titles())
        form.preferred_locations.data = '\n'.join(existing_preferences.get_preferred_locations())
        form.work_type.data = existing_preferences.work_type
        form.work_mode.data = existing_preferences.work_mode
        form.experience_level.data = existing_preferences.experience_level
        form.required_skills.data = ', '.join(existing_preferences.get_required_skills())
        form.preferred_skills.data = ', '.join(existing_preferences.get_preferred_skills())
        form.min_salary.data = existing_preferences.min_salary
        form.max_salary.data = existing_preferences.max_salary
        form.salary_negotiable.data = existing_preferences.salary_negotiable
        industries = existing_preferences.get_preferred_industries()
        if industries:
            form.preferred_industries.data = industries[0]
        form.company_size_preference.data = existing_preferences.company_size_preference
        form.max_applications_per_day.data = existing_preferences.max_applications_per_day
        form.application_priority.data = existing_preferences.application_priority
        form.linkedin_priority.data = str(existing_preferences.linkedin_priority)
        form.indeed_priority.data = str(existing_preferences.indeed_priority)
        form.naukri_priority.data = str(existing_preferences.naukri_priority)
        form.internshala_priority.data = str(existing_preferences.internshala_priority)
        form.notice_period.data = existing_preferences.notice_period
        form.auto_apply_consent.data = existing_preferences.auto_apply_enabled
    
    return render_template('setup/job_preferences.html', 
                         title='Job Preferences Setup', 
                         form=form,
                         existing_preferences=existing_preferences)


@bp.route('/welcome')
@login_required
def welcome():
    """Welcome page shown after successful registration."""
    return render_template('setup/welcome.html', title='Welcome to AutoHire')


@bp.route('/skip-setup')
@login_required
def skip_setup():
    """Allow users to skip initial setup and go to dashboard."""
    flash('You can set up your job preferences later from the Settings page.', 'info')
    return redirect(url_for('dashboard.index'))


@bp.route('/check-setup')
@login_required
def check_setup():
    """Check if user has completed setup and redirect accordingly."""
    
    # Check if user has job preferences set up
    preferences = JobPreferences.query.filter_by(user_id=current_user.id).first()
    
    if not preferences:
        # User hasn't completed setup
        return redirect(url_for('setup.welcome'))
    
    # Setup is complete, go to dashboard
    return redirect(url_for('dashboard.index'))
