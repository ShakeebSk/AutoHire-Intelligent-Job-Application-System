'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm
from app.models.user import User
from datetime import datetime


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in automatically after registration
        login_user(user)
        
        flash('Welcome to AutoHire! Let\'s set up your job preferences to get started.', 'success')
        return redirect(url_for('setup.welcome'))
    
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('dashboard.settings'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)


@bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    try:
        user_id = current_user.id
        username = current_user.username
        
        # Delete all associated job applications
        from app.models.job_application import JobApplication
        JobApplication.query.filter_by(user_id=user_id).delete()
        
        # Delete job preferences if they exist
        try:
            from app.models.job_preferences import JobPreferences, Resume
            JobPreferences.query.filter_by(user_id=user_id).delete()
            Resume.query.filter_by(user_id=user_id).delete()
        except ImportError:
            pass  # Models may not exist yet
        
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        # Logout the user
        logout_user()
        
        flash(f"Account for {username} has been permanently deleted. We're sorry to see you go!", 'info')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account. Please try again or contact support.', 'error')
        return redirect(url_for('dashboard.settings'))
