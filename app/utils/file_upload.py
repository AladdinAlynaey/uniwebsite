"""
File Upload Utility for Assignment Submissions
Handles file validation, storage, and management
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'zip', 'jpg', 'jpeg', 'png', 'txt', 'py', 'ipynb'}

# Maximum file size in bytes (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file):
    """Validate file size (max 5MB)"""
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    return file_size <= MAX_FILE_SIZE


def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    return file_size


def format_file_size(size_bytes):
    """Format file size to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def save_assignment_file(file, student_id, assignment_id):
    """
    Save uploaded assignment file
    
    Args:
        file: FileStorage object from Flask request
        student_id: ID of the student
        assignment_id: ID of the assignment
        
    Returns:
        dict: File information including filename, filepath, and size
        None: If validation fails
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    if not validate_file_size(file):
        return None
    
    # Create secure filename
    original_filename = secure_filename(file.filename)
    file_extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex[:8]}_{original_filename}"
    
    # Create directory structure
    upload_dir = os.path.join(
        current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        'assignments',
        str(student_id),
        str(assignment_id)
    )
    
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    
    # Get file size
    file_size = os.path.getsize(filepath)
    
    # Return file information
    return {
        'filename': original_filename,
        'stored_filename': unique_filename,
        'filepath': filepath,
        'relative_path': os.path.join('assignments', str(student_id), str(assignment_id), unique_filename),
        'size': file_size,
        'size_formatted': format_file_size(file_size),
        'extension': file_extension,
        'uploaded_at': datetime.now().isoformat()
    }


def delete_assignment_file(filepath):
    """
    Delete an assignment file
    
    Args:
        filepath: Path to the file to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def get_total_files_size(files_list):
    """
    Calculate total size of multiple files
    
    Args:
        files_list: List of file dictionaries with 'size' key
        
    Returns:
        int: Total size in bytes
    """
    return sum(file.get('size', 0) for file in files_list)


def validate_total_size(existing_files, new_files):
    """
    Validate that total size of all files doesn't exceed limit
    
    Args:
        existing_files: List of already uploaded files
        new_files: List of new files to upload
        
    Returns:
        bool: True if within limit, False otherwise
    """
    existing_size = get_total_files_size(existing_files)
    
    new_size = 0
    for file in new_files:
        if file and file.filename:
            new_size += get_file_size(file)
    
    total_size = existing_size + new_size
    return total_size <= MAX_FILE_SIZE


def get_file_icon(extension):
    """Get Font Awesome icon class for file type"""
    icons = {
        'pdf': 'fa-file-pdf text-danger',
        'doc': 'fa-file-word text-primary',
        'docx': 'fa-file-word text-primary',
        'zip': 'fa-file-archive text-warning',
        'jpg': 'fa-file-image text-info',
        'jpeg': 'fa-file-image text-info',
        'png': 'fa-file-image text-info',
        'txt': 'fa-file-alt text-secondary',
        'py': 'fa-file-code text-success',
        'ipynb': 'fa-file-code text-success'
    }
    return icons.get(extension.lower(), 'fa-file text-secondary')
