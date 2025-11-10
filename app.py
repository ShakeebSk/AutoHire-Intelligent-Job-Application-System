'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

from app import create_app, db
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.job_preferences import JobPreferences, Resume

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'JobApplication': JobApplication,
        'JobPreferences': JobPreferences,
        'Resume': Resume
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
