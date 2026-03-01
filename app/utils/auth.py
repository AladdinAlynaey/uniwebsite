from functools import wraps
from flask import session, redirect, url_for, request, flash
from app.models.student import Student

# Simple admin password (in a real app, use proper authentication)
ADMIN_PASSWORD = "alaadin123"

def login_required(f):
    """Decorator for views that require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in as admin to access this page.', 'danger')
            return redirect(url_for('main_bp.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def student_token_required(f):
    """Decorator for views that require student token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('student_token')
        if not token:
            flash('Please enter your student token to access this page.', 'danger')
            return redirect(url_for('main_bp.student_login', next=request.url))
            
        student = Student.find_by_token(token)
        if not student:
            flash('Invalid student token.', 'danger')
            session.pop('student_token', None)
            return redirect(url_for('main_bp.student_login', next=request.url))
            
        return f(*args, **kwargs)
    return decorated_function

def verify_admin_password(password):
    """Verify admin password"""
    return password == ADMIN_PASSWORD

def get_current_student():
    """Get the current student from session token"""
    token = session.get('student_token')
    if not token:
        return None
    return Student.find_by_token(token) 