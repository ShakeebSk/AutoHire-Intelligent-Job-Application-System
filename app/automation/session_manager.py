"""
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

Automation Session Manager - Tracks and manages active automation sessions
"""

from threading import Lock
from datetime import datetime
from app.automation.automation_thread import AutomationThread

class AutomationSessionManager:
    """Manages active automation sessions for users"""
    
    def __init__(self):
        self.active_sessions = {}  # user_id -> session_data
        self.lock = Lock()
    
    def start_session(self, user_id):
        """Start a new automation session for a user"""
        with self.lock: 
            # Stop existing session if any
            if user_id in self.active_sessions:
                self.stop_session(user_id)
            
            # Create new session
            thread = AutomationThread(user_id)
            session_data = {
                'thread': thread,
                'start_time': datetime.utcnow(),
                'status': 'starting',
                'current_action': 'Initializing automation...',
                'applications_made': 0,
                'errors': [],
                'platforms_processed': []
            }
            
            self.active_sessions[user_id] = session_data
            thread.start()
            
            return True
    
    def stop_session(self, user_id):
        """Stop an active automation session"""
        with self.lock:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                thread = session['thread']
                
                if thread.is_alive():
                    thread.stop()
                    thread.join(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                
                # Update session status
                session['status'] = 'stopped'
                session['current_action'] = 'Automation stopped by user'
                
                # Remove from active sessions after a delay to allow status check
                return True
            
            return False
    
    def get_session_status(self, user_id):
        """Get current status of user's automation session"""
        with self.lock:
            if user_id not in self.active_sessions:
                return {
                    'active': False,
                    'status': 'inactive',
                    'message': 'No active automation session'
                }
            
            session = self.active_sessions[user_id]
            thread = session['thread']
            
            # Check if thread is still running
            if not thread.is_alive() and session['status'] != 'stopped':
                session['status'] = 'completed'
                session['current_action'] = 'Automation completed'
            
            # Get automation manager stats if available
            stats = {}
            if thread.automation_manager:
                stats = thread.automation_manager.session_stats
            
            return {
                'active': thread.is_alive(),
                'status': session['status'],
                'current_action': session['current_action'],
                'start_time': session['start_time'].isoformat(),
                'applications_made': stats.get('successful_applications', 0),
                'total_searched': stats.get('total_searched', 0),
                'failed_applications': stats.get('failed_applications', 0),
                'errors': stats.get('errors', [])[-3:],  # Last 3 errors
                'platforms_processed': session.get('platforms_processed', [])
            }
    
    def cleanup_completed_sessions(self):
        """Clean up completed sessions older than 1 hour"""
        with self.lock:
            current_time = datetime.utcnow()
            users_to_remove = []
            
            for user_id, session in self.active_sessions.items():
                thread = session['thread']
                if not thread.is_alive():
                    # Remove sessions older than 1 hour
                    elapsed = current_time - session['start_time']
                    if elapsed.total_seconds() > 3600:  # 1 hour
                        users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del self.active_sessions[user_id]

# Global session manager instance
session_manager = AutomationSessionManager()
