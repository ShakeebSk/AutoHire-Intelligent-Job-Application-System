"""
Resume upload and management utilities for AutoHire
"""

import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import current_app, flash
from app import db
from app.models.job_preferences import Resume


class ResumeHandler:
    """Handles resume file operations and database management"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_file(self, file, resume_name):
        """
        Validate uploaded resume file
        
        Args:
            file: FileStorage object from request.files
            resume_name: Name provided by user
            
        Returns:
            dict: {'valid': bool, 'errors': list}
        """
        errors = []
        
        # Check if file exists
        if not file or file.filename == '':
            errors.append('No file selected')
            
        # Check resume name
        if not resume_name or len(resume_name.strip()) < 3:
            errors.append('Resume name must be at least 3 characters long')
            
        if file and file.filename:
            # Check file extension
            file_extension = self._get_file_extension(file.filename)
            if file_extension not in self.ALLOWED_EXTENSIONS:
                errors.append(f'File type not allowed. Only {", ".join(self.ALLOWED_EXTENSIONS).upper()} files are supported')

            # Check file size by reading its content length
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0, os.SEEK_SET)

            if file_size > self.MAX_FILE_SIZE:
                errors.append(f'File size too large. Maximum size is {self.MAX_FILE_SIZE / (1024*1024):.0f}MB')

            if file_size == 0:
                errors.append('File is empty')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def save_resume(self, user_id, file, resume_name, is_primary=False, is_active=True):
        """
        Save resume file and create database record
        
        Args:
            user_id: ID of the user
            file: FileStorage object
            resume_name: Name for the resume
            is_primary: Whether to set as primary resume
            is_active: Whether resume is active
            
        Returns:
            dict: {'success': bool, 'resume': Resume object or None, 'message': str}
        """
        try:
            # Validate file first
            validation = self.validate_file(file, resume_name)
            if not validation['valid']:
                return {
                    'success': False,
                    'resume': None,
                    'message': '; '.join(validation['errors'])
                }
            
            # Check for duplicate resume names for this user
            existing_resume = Resume.query.filter_by(
                user_id=user_id, 
                resume_name=resume_name.strip()
            ).first()
            
            if existing_resume:
                return {
                    'success': False,
                    'resume': None,
                    'message': f'A resume with the name "{resume_name}" already exists'
                }
            
            # Generate unique filename
            original_filename = file.filename
            file_extension = self._get_file_extension(original_filename)
            secure_name = secure_filename(original_filename)
            unique_filename = f"{uuid.uuid4().hex}_{secure_name}"
            
            # Get file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            # Create upload directory
            upload_dir = self._get_upload_directory()
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            self.logger.info(f"Resume file saved: {file_path}")
            
            # Handle primary resume setting
            if is_primary:
                # Unset other primary resumes for this user
                Resume.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
                db.session.flush()
            
            # Create resume record
            resume = Resume(
                user_id=user_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file.mimetype or f'application/{file_extension}',
                resume_name=resume_name.strip(),
                is_primary=is_primary,
                is_active=is_active
            )
            
            db.session.add(resume)
            db.session.commit()
            
            self.logger.info(f"Resume record created: {resume.id}")
            
            return {
                'success': True,
                'resume': resume,
                'message': f'Resume "{resume_name}" uploaded successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error saving resume: {str(e)}")
            
            # Clean up file if it was saved but database operation failed
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up file after error: {file_path}")
                except OSError as cleanup_error:
                    self.logger.error(f"Failed to cleanup file {file_path}: {cleanup_error}")
            
            return {
                'success': False,
                'resume': None,
                'message': f'Failed to upload resume: {str(e)}'
            }
    
    def delete_resume(self, user_id, resume_id):
        """
        Delete resume file and database record
        
        Args:
            user_id: ID of the user
            resume_id: ID of the resume to delete
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Get resume record
            resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
            
            if not resume:
                return {
                    'success': False,
                    'message': 'Resume not found'
                }
            
            resume_name = resume.resume_name
            file_path = resume.file_path
            
            # Delete physical file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Deleted resume file: {file_path}")
                except OSError as e:
                    self.logger.warning(f"Could not delete file {file_path}: {e}")
                    # Continue with database deletion even if file deletion fails
            
            # Delete database record
            db.session.delete(resume)
            db.session.commit()
            
            self.logger.info(f"Deleted resume record: {resume_id}")
            
            return {
                'success': True,
                'message': f'Resume "{resume_name}" deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting resume: {str(e)}")
            
            return {
                'success': False,
                'message': f'Failed to delete resume: {str(e)}'
            }
    
    def set_primary_resume(self, user_id, resume_id):
        """
        Set a resume as primary for a user
        
        Args:
            user_id: ID of the user
            resume_id: ID of the resume to set as primary
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Verify resume belongs to user
            resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
            
            if not resume:
                return {
                    'success': False,
                    'message': 'Resume not found'
                }
            
            # Unset all other primary resumes for this user
            Resume.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
            
            # Set this resume as primary
            resume.is_primary = True
            db.session.commit()
            
            self.logger.info(f"Set resume {resume_id} as primary for user {user_id}")
            
            return {
                'success': True,
                'message': f'"{resume.resume_name}" set as primary resume'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error setting primary resume: {str(e)}")
            
            return {
                'success': False,
                'message': f'Failed to set primary resume: {str(e)}'
            }
    
    def toggle_active_status(self, user_id, resume_id):
        """
        Toggle active status of a resume
        
        Args:
            user_id: ID of the user
            resume_id: ID of the resume
            
        Returns:
            dict: {'success': bool, 'message': str, 'new_status': bool}
        """
        try:
            # Get resume record
            resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
            
            if not resume:
                return {
                    'success': False,
                    'message': 'Resume not found',
                    'new_status': False
                }
            
            # Toggle status
            resume.is_active = not resume.is_active
            db.session.commit()
            
            status_text = 'activated' if resume.is_active else 'deactivated'
            self.logger.info(f"Resume {resume_id} {status_text} for user {user_id}")
            
            return {
                'success': True,
                'message': f'Resume "{resume.resume_name}" {status_text}',
                'new_status': resume.is_active
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error toggling resume status: {str(e)}")
            
            return {
                'success': False,
                'message': f'Failed to update resume status: {str(e)}',
                'new_status': False
            }
    
    def get_user_resumes(self, user_id, active_only=False):
        """
        Get all resumes for a user
        
        Args:
            user_id: ID of the user
            active_only: If True, only return active resumes
            
        Returns:
            list: List of Resume objects
        """
        query = Resume.query.filter_by(user_id=user_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(Resume.is_primary.desc(), Resume.uploaded_at.desc()).all()
    
    def get_primary_resume(self, user_id):
        """
        Get the primary resume for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Resume object or None
        """
        return Resume.query.filter_by(
            user_id=user_id, 
            is_primary=True, 
            is_active=True
        ).first()
    
    def cleanup_orphaned_files(self):
        """
        Clean up resume files that exist on disk but not in database
        This should be run periodically as a maintenance task
        """
        try:
            upload_dir = self._get_upload_directory()
            
            if not os.path.exists(upload_dir):
                return
            
            # Get all filenames from database
            db_filenames = set()
            resumes = Resume.query.all()
            for resume in resumes:
                if resume.filename:
                    db_filenames.add(resume.filename)
            
            # Check files on disk
            cleaned_count = 0
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # If file not in database, delete it
                if filename not in db_filenames:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up orphaned file: {filename}")
                    except OSError as e:
                        self.logger.error(f"Failed to cleanup file {filename}: {e}")
            
            self.logger.info(f"Cleanup completed. Removed {cleaned_count} orphaned files")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def _get_file_extension(self, filename):
        """Get file extension from filename"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _get_upload_directory(self):
        """Get the upload directory path"""
        return os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
    
    
    def get_resume_statistics(self, user_id):
        """Get resume statistics for a user"""
        resumes = self.get_user_resumes(user_id)
        
        total_resumes = len(resumes)
        active_resumes = len([r for r in resumes if r.is_active])
        primary_resumes = len([r for r in resumes if r.is_primary])
        total_usage = sum(r.times_used or 0 for r in resumes)
        
        # Calculate average success rate
        success_rates = [r.success_rate for r in resumes if r.success_rate is not None]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        return {
            'total_resumes': total_resumes,
            'active_resumes': active_resumes,
            'primary_resumes': primary_resumes,
            'total_usage': total_usage,
            'average_success_rate': avg_success_rate
        }
    
