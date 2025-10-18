'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

import threading
from app.automation.automation_manager import AutomationManager
from app import create_app

class AutomationThread(threading.Thread):
    def __init__(self, user_id, app_context=True):
        super().__init__()
        self.user_id = user_id
        self.automation_manager = None
        self._stop_event = threading.Event()
        self.app_context = app_context
        self.daemon = True  # Allow main thread to exit even if this is running

    def run(self):
        try:
            if self.app_context:
                app = create_app()
                with app.app_context():
                    self.automation_manager = AutomationManager(self.user_id)
                    self.automation_manager.run_full_automation(stop_event=self._stop_event)
            else:
                self.automation_manager = AutomationManager(self.user_id)
                self.automation_manager.run_full_automation(stop_event=self._stop_event)
        except Exception as e:
            # Log the error if possible
            if self.automation_manager:
                self.automation_manager.logger.error(f"Error in automation thread: {str(e)}")
                self.automation_manager.session_stats['status'] = 'error'
                self.automation_manager.session_stats['current_action'] = f'Error: {str(e)}'

    def stop(self):
        self._stop_event.set()

