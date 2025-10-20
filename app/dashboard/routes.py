'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''


import os
import json
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.dashboard import bp
from app.forms import EditProfileForm, PlatformCredentialsForm, JobPreferencesForm, ResumeFileForm
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.job_preferences import Resume, JobPreferences
from app.utils.resume_handler import ResumeHandler
from datetime import datetime, timedelta
from sqlalchemy import func


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Dashboard main page with statistics and recent applications."""
    
    # Get user statistics
    total_applications = JobApplication.query.filter_by(user_id=current_user.id).count()
    
    # Applications in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_applications = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.application_date >= thirty_days_ago
    ).count()
    
    # Applications by status
    status_counts = db.session.query(
        JobApplication.status,
        func.count(JobApplication.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(JobApplication.status).all()
    
    status_data = {
        'applied': 0,
        'interview': 0,
        'rejected': 0,
        'hired': 0,
        'error': 0
    }
    
    for status, count in status_counts:
        if status in status_data:
            status_data[status] = count
    
    # Applications by platform
    platform_counts = db.session.query(
        JobApplication.platform,
        func.count(JobApplication.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(JobApplication.platform).all()
    
    platform_data = dict(platform_counts)
    
    # Recent applications (last 10)
    recent_apps = JobApplication.query.filter_by(user_id=current_user.id)\
        .order_by(JobApplication.application_date.desc()).limit(10).all()
    
    # Applications today
    today = datetime.utcnow().date()
    applications_today = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        func.date(JobApplication.application_date) == today
    ).count()
    
    return render_template('dashboard/index.html',
                         title='Dashboard',
                         total_applications=total_applications,
                         recent_applications=recent_applications,
                         applications_today=applications_today,
                         status_data=status_data,
                         platform_data=platform_data,
                         recent_apps=recent_apps)


@bp.route('/applications')
@login_required
def applications():
    """View all job applications with filtering and pagination."""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    platform_filter = request.args.get('platform', '')
    
    query = JobApplication.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if platform_filter:
        query = query.filter_by(platform=platform_filter)
    
    applications = query.order_by(JobApplication.application_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    # Get unique statuses and platforms for filters
    statuses = db.session.query(JobApplication.status.distinct())\
        .filter_by(user_id=current_user.id).all()
    statuses = [s[0] for s in statuses if s[0]]
    
    platforms = db.session.query(JobApplication.platform.distinct())\
        .filter_by(user_id=current_user.id).all()
    platforms = [p[0] for p in platforms if p[0]]
    
    return render_template('dashboard/applications.html',
                         title='Applications',
                         applications=applications,
                         statuses=statuses,
                         platforms=platforms,
                         current_status=status_filter,
                         current_platform=platform_filter)


@bp.route('/application/<int:id>')
@login_required
def application_detail(id):
    """View detailed information about a specific application."""
    
    application = JobApplication.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    return render_template('dashboard/application_detail.html',
                         title=f'Application - {application.job_title}',
                         application=application)


@bp.route('/application/<int:id>/update_status', methods=['POST'])
@login_required
def update_application_status(id):
    """Update application status"""
    try:
        application = JobApplication.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        new_status = request.json.get('status')
        valid_statuses = ['applied', 'interview', 'hired', 'rejected', 'error']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        application.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Application status updated to {new_status.title()}',
            'new_status': new_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Edit user profile information."""
    
    form = EditProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        current_user.age = form.age.data
        current_user.phone = form.phone.data
        current_user.location = form.location.data
        current_user.experience_years = form.experience_years.data
        current_user.current_salary = form.current_salary.data
        current_user.expected_salary = form.expected_salary.data
        current_user.skills = form.skills.data
        current_user.education = form.education.data
        current_user.achievements = form.achievements.data
        current_user.daily_application_limit = form.daily_application_limit.data
        
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('dashboard.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.full_name.data = current_user.full_name
        form.age.data = current_user.age
        form.phone.data = current_user.phone
        form.location.data = current_user.location
        form.experience_years.data = current_user.experience_years
        form.current_salary.data = current_user.current_salary
        form.expected_salary.data = current_user.expected_salary
        form.skills.data = current_user.skills
        form.education.data = current_user.education
        form.achievements.data = current_user.achievements
        form.daily_application_limit.data = current_user.daily_application_limit
    
    return render_template('dashboard/profile.html', title='Profile', form=form)


@bp.route('/settings')
@login_required
def settings():
    """Main settings page with navigation to different setting categories."""
    
    return render_template('dashboard/settings.html', title='Settings')


@bp.route('/settings/credentials', methods=['GET', 'POST'])
@login_required
def platform_credentials():
    """Manage platform login credentials."""
    
    form = PlatformCredentialsForm()
    
    if form.validate_on_submit():
        # Update platform credentials
        if form.linkedin_username.data:
            current_user.linkedin_username = form.linkedin_username.data
        if form.linkedin_password.data:
            current_user.set_platform_password('linkedin', form.linkedin_password.data)
            
        if form.indeed_username.data:
            current_user.indeed_username = form.indeed_username.data
        if form.indeed_password.data:
            current_user.set_platform_password('indeed', form.indeed_password.data)
            
        if form.naukri_username.data:
            current_user.naukri_username = form.naukri_username.data
        if form.naukri_password.data:
            current_user.set_platform_password('naukri', form.naukri_password.data)
            
        if form.internshala_username.data:
            current_user.internshala_username = form.internshala_username.data
        if form.internshala_password.data:
            current_user.set_platform_password('internshala', form.internshala_password.data)
        
        db.session.commit()
        flash('Platform credentials have been updated successfully!', 'success')
        return redirect(url_for('dashboard.platform_credentials'))
    
    elif request.method == 'GET':
        # Populate form with existing usernames (not passwords for security)
        form.linkedin_username.data = current_user.linkedin_username
        form.indeed_username.data = current_user.indeed_username
        form.naukri_username.data = current_user.naukri_username
        form.internshala_username.data = current_user.internshala_username
    
    return render_template('dashboard/platform_credentials.html', 
                         title='Platform Credentials', form=form)


@bp.route('/settings/preferences', methods=['GET', 'POST'])
@login_required
def job_preferences():
    """Manage job search preferences and platform priorities."""
    
    form = JobPreferencesForm()
    
    if form.validate_on_submit():
        # Get or create job preferences record
        preferences = JobPreferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = JobPreferences(user_id=current_user.id)
            db.session.add(preferences)
        
        # Update job preferences
        preferences.set_preferred_job_titles([title.strip() for title in form.preferred_job_titles.data.split('\n') if title.strip()])
        preferences.set_preferred_locations([loc.strip() for loc in form.preferred_locations.data.split('\n') if loc.strip()])
        preferences.work_type = form.work_type.data
        preferences.experience_level = form.experience_level.data
        preferences.min_salary = form.min_salary.data if form.min_salary.data else None
        preferences.max_salary = form.max_salary.data if form.max_salary.data else None
        
        # Set platform priorities
        preferences.linkedin_priority = int(form.linkedin_priority.data)
        preferences.indeed_priority = int(form.indeed_priority.data)
        preferences.naukri_priority = int(form.naukri_priority.data)
        preferences.internshala_priority = int(form.internshala_priority.data)
        
        # Update user platform priorities for backward compatibility
        platform_priorities = {
            'linkedin': int(form.linkedin_priority.data),
            'indeed': int(form.indeed_priority.data),
            'naukri': int(form.naukri_priority.data),
            'internshala': int(form.internshala_priority.data)
        }
        current_user.platform_priorities = json.dumps(platform_priorities)
        
        db.session.commit()
        flash('Job preferences have been updated successfully!', 'success')
        return redirect(url_for('dashboard.job_preferences'))
    
    elif request.method == 'GET':
        # Load existing preferences if they exist
        preferences = JobPreferences.query.filter_by(user_id=current_user.id).first()
        if preferences:
            # Load job preferences
            form.preferred_job_titles.data = '\n'.join(preferences.get_preferred_job_titles())
            form.preferred_locations.data = '\n'.join(preferences.get_preferred_locations())
            form.work_type.data = preferences.work_type
            form.experience_level.data = preferences.experience_level
            form.min_salary.data = preferences.min_salary
            form.max_salary.data = preferences.max_salary
            
            # Load platform priorities
            form.linkedin_priority.data = str(preferences.linkedin_priority)
            form.indeed_priority.data = str(preferences.indeed_priority)
            form.naukri_priority.data = str(preferences.naukri_priority)
            form.internshala_priority.data = str(preferences.internshala_priority)
        
        # Fallback to user platform priorities if JobPreferences doesn't exist
        elif current_user.platform_priorities:
            try:
                priorities = json.loads(current_user.platform_priorities)
                form.linkedin_priority.data = str(priorities.get('linkedin', 1))
                form.indeed_priority.data = str(priorities.get('indeed', 2))
                form.naukri_priority.data = str(priorities.get('naukri', 3))
                form.internshala_priority.data = str(priorities.get('internshala', 4))
            except:
                pass  # Use default values if JSON parsing fails
    
    return render_template('dashboard/job_preferences.html', 
                         title='Job Preferences', form=form)


@bp.route('/resume')
@login_required
def resume_management():
    """Manage uploaded resumes."""
    resume_handler = ResumeHandler()
    resumes = resume_handler.get_user_resumes(current_user.id)
    form = ResumeFileForm()
    stats = resume_handler.get_resume_statistics(current_user.id)
    
    return render_template('dashboard/resume_management.html', 
                           title='Resume Management', 
                           resumes=resumes,
                           form=form,
                           stats=stats)


@bp.route('/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    """Upload a new resume"""
    try:
        form = ResumeFileForm()
        resume_handler = ResumeHandler()
        
        current_app.logger.info(f"Resume upload attempt by user {current_user.id}")
        current_app.logger.debug(f"Form data: resume_name={form.resume_name.data}, is_primary={form.is_primary.data}")
        current_app.logger.debug(f"File data: {form.resume.data}")

        if form.validate_on_submit():
            current_app.logger.info("Form validation passed")
            
            # Additional file validation
            if not form.resume.data:
                flash('No file selected. Please choose a resume file to upload.', 'danger')
                return redirect(url_for('dashboard.resume_management'))
            
            result = resume_handler.save_resume(
                user_id=current_user.id,
                file=form.resume.data,
                resume_name=form.resume_name.data,
                is_primary=form.is_primary.data
            )
            
            current_app.logger.info(f"Resume upload result: {result}")

            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(result['message'], 'danger')
        else:
            current_app.logger.warning(f"Form validation failed: {form.errors}")
            # Show more detailed error messages
            if form.resume.errors:
                for error in form.resume.errors:
                    flash(f"File error: {error}", 'danger')
            if form.resume_name.errors:
                for error in form.resume_name.errors:
                    flash(f"Resume name error: {error}", 'danger')
            if form.csrf_token.errors:
                for error in form.csrf_token.errors:
                    flash(f"Security error: {error}", 'danger')
            
            # Fallback generic error message
            if not any([form.resume.errors, form.resume_name.errors, form.csrf_token.errors]):
                flash('There was an error with your form submission. Please try again.', 'danger')

    except Exception as e:
        current_app.logger.error(f"Unexpected error in resume upload: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return redirect(url_for('dashboard.resume_management'))


@bp.route('/resume/<int:id>/delete', methods=['POST'])
@login_required
def delete_resume(id):
    """Delete a resume"""
    resume_handler = ResumeHandler()
    result = resume_handler.delete_resume(user_id=current_user.id, resume_id=id)

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
        
    return redirect(url_for('dashboard.resume_management'))


@bp.route('/resume/<int:id>/set_primary', methods=['POST'])
@login_required
def set_primary_resume(id):
    """Set a resume as primary"""
    resume_handler = ResumeHandler()
    result = resume_handler.set_primary_resume(user_id=current_user.id, resume_id=id)

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')

    return redirect(url_for('dashboard.resume_management'))


@bp.route('/resume/<int:id>/toggle_status', methods=['POST'])
@login_required
def toggle_resume_status(id):
    """Toggle resume active status"""
    resume_handler = ResumeHandler()
    result = resume_handler.toggle_active_status(user_id=current_user.id, resume_id=id)

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')

    return redirect(url_for('dashboard.resume_management'))


@bp.route('/analytics')
@login_required
def analytics():
    """View detailed analytics and reports."""
    
    # Generate analytics data
    # Applications over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_applications = db.session.query(
        func.date(JobApplication.application_date).label('date'),
        func.count(JobApplication.id).label('count')
    ).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.application_date >= thirty_days_ago
    ).group_by(func.date(JobApplication.application_date)).all()
    
    # Success rate by platform
    platform_success = db.session.query(
        JobApplication.platform,
        func.count(JobApplication.id).label('total'),
        func.count(JobApplication.id).filter(
            JobApplication.status.in_(['interview', 'hired'])
        ).label('success')
    ).filter_by(user_id=current_user.id).group_by(JobApplication.platform).all()
    
    return render_template('dashboard/analytics.html',
                         title='Analytics',
                         daily_applications=daily_applications,
                         platform_success=platform_success)


@bp.route('/start_automation', methods=['POST'])
@login_required
def start_automation():
    """Start the job application automation process."""
    
    # This would integrate with your automation system
    # For now, it's a placeholder
    
    flash('Automation process started! You will be notified when applications are submitted.', 'info')
    return redirect(url_for('dashboard.index'))


@bp.route('/stop_automation', methods=['POST'])
@login_required
def stop_automation():
    """Stop the job application automation process."""
    
    # This would integrate with your automation system
    # For now, it's a placeholder
    
    flash('Automation process stopped.', 'info')
    return redirect(url_for('dashboard.index'))


@bp.route('/api/applications')
@login_required
def api_applications():
    """API endpoint to get applications data for charts."""
    
    applications = JobApplication.query.filter_by(user_id=current_user.id).all()
    
    return jsonify([app.to_dict() for app in applications])


@bp.route('/automation/start', methods=['POST'])
@login_required
def start_automation_process():
    """Start the automated job application process"""
    try:
        from app.automation.session_manager import session_manager
        from app.models.job_preferences import JobPreferences
        
        # Check if user has set up preferences and credentials
        preferences = JobPreferences.query.filter_by(user_id=current_user.id).first()
        
        if not preferences:
            return jsonify({
                'success': False,
                'message': 'Please set up your job preferences first before starting automation.',
                'redirect': url_for('dashboard.job_preferences')
            })
        
        # Check if user has platform credentials
        has_credentials = (current_user.linkedin_username and current_user.linkedin_password) or \
                         (current_user.indeed_username and current_user.indeed_password)
        
        if not has_credentials:
            return jsonify({
                'success': False,
                'message': 'Please set up your platform credentials first.',
                'redirect': url_for('dashboard.platform_credentials')
            })
        
        # Start automation session
        success = session_manager.start_session(current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Automation started successfully! Check the status below for real-time updates.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start automation session. Please try again.'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting automation: {str(e)}'
        }), 500


@bp.route('/automation/stop', methods=['POST'])
@login_required
def stop_automation_process():
    """Stop the automated job application process"""
    try:
        from app.automation.session_manager import session_manager
        
        success = session_manager.stop_session(current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Automation stop signal sent. It may take a moment to gracefully stop.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No active automation session to stop.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping automation: {str(e)}'
        }), 500


@bp.route('/automation/status')
@login_required
def automation_status():
    """Get automation status and statistics"""
    from app.automation.session_manager import session_manager
    status = session_manager.get_session_status(current_user.id)
    return jsonify(status)


@bp.route('/automation/test', methods=['POST'])
@login_required
def test_automation():
    """Test automation without actually applying to jobs"""
    try:
        from app.automation.automation_manager import AutomationManager
        
        # Create automation manager
        automation_manager = AutomationManager(current_user.id)
        
        # Get user search criteria
        search_criteria = automation_manager.get_user_search_criteria()
        
        if not search_criteria:
            return jsonify({
                'success': False,
                'message': 'No job preferences found. Please set up your preferences first.'
            })
        
        # Return test results
        test_results = {
            'success': True,
            'message': 'Automation test completed successfully',
            'search_criteria': search_criteria,
            'platform_priorities': automation_manager.get_platform_priorities(),
            'daily_limit_status': automation_manager.check_daily_limit(),
            'credentials_status': {
                'linkedin': bool(current_user.linkedin_username and current_user.linkedin_password),
                'indeed': bool(current_user.indeed_username and current_user.indeed_password),
                'naukri': bool(current_user.naukri_username and current_user.naukri_password),
                'internshala': bool(current_user.internshala_username and current_user.internshala_password)
            }
        }
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test failed: {str(e)}'
        }), 500
