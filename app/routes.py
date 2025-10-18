'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from flask import render_template, current_app
from app import db


def init_routes(app):
    """Initialize main application routes."""
    
    @app.route('/')
    @app.route('/index')
    def index():
        """Home page."""
        return render_template('index.html', title='AutoHire - Automated Job Applications')
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
