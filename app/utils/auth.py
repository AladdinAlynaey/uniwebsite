"""
Auth utilities — Role-based authentication and authorization.

Provides decorators for route access control and utility functions
for the unified user system.
"""

from functools import wraps
from flask import session, redirect, url_for, request, flash, g
from app.models.user import User


def get_current_user():
    """Get the currently logged-in user from session.
    
    Returns:
        dict or None: User record
    """
    user_id = session.get('user_id')
    if not user_id:
        # Legacy student token support
        token = session.get('student_token')
        if token:
            user = User.find_by_token(token)
            if user:
                # Upgrade session to new format
                session['user_id'] = user['id']
                session['user_role'] = user.get('role', User.ROLE_STUDENT)
                return user
        return None
    
    # Check if user is cached in g for this request
    if hasattr(g, '_current_user') and g._current_user:
        return g._current_user
    
    user = User.find_by_id(user_id)
    if user and user.get('is_active', True):
        g._current_user = user
        return user
    
    # Invalid session, clear it
    session.pop('user_id', None)
    session.pop('user_role', None)
    return None


def login_user(user):
    """Set session data for a logged-in user.
    
    Args:
        user: User dict
    """
    session['user_id'] = user['id']
    session['user_role'] = user.get('role', User.ROLE_STUDENT)
    session['user_name'] = user.get('name', '')
    
    # For backward compat with student routes
    if user.get('role') == User.ROLE_STUDENT and user.get('token'):
        session['student_token'] = user['token']
    
    # For backward compat with admin routes
    if user.get('role') in [User.ROLE_SUPER_ADMIN, User.ROLE_FACULTY_HEAD, User.ROLE_BATCH_REP]:
        session['is_admin'] = True


def logout_user():
    """Clear all session data."""
    session.clear()


def role_required(*roles):
    """Decorator: require the user to have one of the specified roles.
    
    Usage:
        @role_required(User.ROLE_SUPER_ADMIN)
        @role_required(User.ROLE_BATCH_REP, User.ROLE_FACULTY_HEAD, User.ROLE_SUPER_ADMIN)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('main_bp.login', next=request.url))
            
            user_role = user.get('role')
            
            # Super admin can access everything
            if user_role == User.ROLE_SUPER_ADMIN:
                return f(*args, **kwargs)
            
            if user_role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main_bp.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required(f):
    """Decorator for views that require any admin-level login.
    Backward compatible — allows super_admin, faculty_head, and batch_rep.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main_bp.login', next=request.url))
        
        user_role = user.get('role')
        if user_role not in [User.ROLE_SUPER_ADMIN, User.ROLE_FACULTY_HEAD, User.ROLE_BATCH_REP]:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main_bp.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def student_token_required(f):
    """Decorator for views that require student login.
    Supports both new user system and legacy token.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main_bp.student_login', next=request.url))
        
        if user.get('role') != User.ROLE_STUDENT:
            flash('Student access required.', 'danger')
            return redirect(url_for('main_bp.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """Decorator for views that require teacher login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main_bp.login', next=request.url))
        
        user_role = user.get('role')
        if user_role not in [User.ROLE_TEACHER, User.ROLE_SUPER_ADMIN]:
            flash('Teacher access required.', 'danger')
            return redirect(url_for('main_bp.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """Decorator for views that require super admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main_bp.login', next=request.url))
        
        if user.get('role') != User.ROLE_SUPER_ADMIN:
            flash('Super admin access required.', 'danger')
            return redirect(url_for('main_bp.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def faculty_head_required(f):
    """Decorator for views that require faculty head or above."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main_bp.login', next=request.url))
        
        user_role = user.get('role')
        if user_role not in [User.ROLE_FACULTY_HEAD, User.ROLE_SUPER_ADMIN]:
            flash('Faculty head access required.', 'danger')
            return redirect(url_for('main_bp.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def get_user_scope(user):
    """Get the data scope for a user based on their role.
    
    Returns:
        dict: {scope_type, faculty_id, department_id, batch_id}
    """
    role = user.get('role')
    
    if role == User.ROLE_SUPER_ADMIN:
        return {'scope_type': 'university', 'faculty_id': None, 'department_id': None, 'batch_id': None}
    elif role == User.ROLE_FACULTY_HEAD:
        return {'scope_type': 'faculty', 'faculty_id': user.get('faculty_id'), 'department_id': None, 'batch_id': None}
    elif role == User.ROLE_BATCH_REP:
        return {'scope_type': 'batch', 'faculty_id': user.get('faculty_id'), 'department_id': user.get('department_id'), 'batch_id': user.get('batch_id')}
    elif role == User.ROLE_TEACHER:
        return {'scope_type': 'teacher', 'faculty_id': user.get('faculty_id'), 'department_id': None, 'batch_id': None}
    elif role == User.ROLE_STUDENT:
        return {'scope_type': 'batch', 'faculty_id': user.get('faculty_id'), 'department_id': user.get('department_id'), 'batch_id': user.get('batch_id')}
    
    return {'scope_type': None, 'faculty_id': None, 'department_id': None, 'batch_id': None}


# Legacy compatibility
def verify_admin_password(password):
    """Legacy: verify admin password. Now checks against User model."""
    # Try to find any super_admin user
    admins = User.get_by_role(User.ROLE_SUPER_ADMIN)
    for admin in admins:
        if User.check_password(admin, password):
            return admin
    return None


# Legacy compatibility - still used by some student routes
def get_current_student():
    """Get the current student user. Backward compatible."""
    user = get_current_user()
    if user and user.get('role') == User.ROLE_STUDENT:
        return user
    return None