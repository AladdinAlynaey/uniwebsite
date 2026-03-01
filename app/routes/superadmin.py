"""
Super Admin Routes — University Manager portal.

Full control over the entire university: faculties, departments, batches, users, settings.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.utils.auth import super_admin_required, get_current_user
from app.models.user import User
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.batch import Batch
from app.models.subject import Subject
from app.models.teacher_subject import TeacherSubject

superadmin_bp = Blueprint('superadmin_bp', __name__)


@superadmin_bp.route('/dashboard')
@super_admin_required
def dashboard():
    """University overview dashboard."""
    user = get_current_user()
    
    faculties = Faculty.load_all()
    departments = Department.load_all()
    batches = Batch.load_all()
    all_users = User.load_all()
    
    stats = {
        'faculties': len(faculties),
        'departments': len(departments),
        'batches': len(batches),
        'students': len([u for u in all_users if u.get('role') == User.ROLE_STUDENT]),
        'teachers': len([u for u in all_users if u.get('role') == User.ROLE_TEACHER]),
        'faculty_heads': len([u for u in all_users if u.get('role') == User.ROLE_FACULTY_HEAD]),
        'batch_reps': len([u for u in all_users if u.get('role') == User.ROLE_BATCH_REP]),
        'total_users': len(all_users)
    }
    
    return render_template('superadmin/dashboard.html', user=user, stats=stats,
                           faculties=faculties, departments=departments, batches=batches)


# ===== FACULTY MANAGEMENT =====

@superadmin_bp.route('/faculties')
@super_admin_required
def faculties():
    """Manage faculties."""
    user = get_current_user()
    all_faculties = Faculty.get_with_stats()
    faculty_heads = User.get_by_role(User.ROLE_FACULTY_HEAD)
    return render_template('superadmin/faculties.html', user=user,
                           faculties=all_faculties, faculty_heads=faculty_heads)


@superadmin_bp.route('/faculties/create', methods=['POST'])
@super_admin_required
def create_faculty():
    """Create a new faculty."""
    name = request.form.get('name')
    code = request.form.get('code', '').upper().strip()
    description = request.form.get('description', '')
    head_user_id = request.form.get('head_user_id', '')
    
    if not name or not code:
        flash('Faculty name and code are required.', 'danger')
        return redirect(url_for('superadmin_bp.faculties'))
    
    existing = Faculty.find_by_code(code)
    if existing:
        flash(f'Faculty with code {code} already exists.', 'danger')
        return redirect(url_for('superadmin_bp.faculties'))
    
    faculty = Faculty.create({
        'name': name,
        'code': code,
        'description': description,
        'head_user_id': head_user_id
    })
    
    # Update faculty head's faculty_id
    if head_user_id:
        User.update(head_user_id, {'faculty_id': faculty['id']})
    
    flash(f'Faculty "{name}" created successfully!', 'success')
    return redirect(url_for('superadmin_bp.faculties'))


@superadmin_bp.route('/faculties/<faculty_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_faculty(faculty_id):
    """Edit a faculty."""
    faculty = Faculty.find_by_id(faculty_id)
    if not faculty:
        flash('Faculty not found.', 'danger')
        return redirect(url_for('superadmin_bp.faculties'))
    
    if request.method == 'POST':
        Faculty.update(faculty_id, {
            'name': request.form.get('name', faculty['name']),
            'code': request.form.get('code', faculty.get('code', '')).upper().strip(),
            'description': request.form.get('description', ''),
            'head_user_id': request.form.get('head_user_id', '')
        })
        flash('Faculty updated successfully!', 'success')
        return redirect(url_for('superadmin_bp.faculties'))
    
    user = get_current_user()
    faculty_heads = User.get_by_role(User.ROLE_FACULTY_HEAD)
    return render_template('superadmin/edit_faculty.html', user=user,
                           faculty=faculty, faculty_heads=faculty_heads)


@superadmin_bp.route('/faculties/<faculty_id>/delete', methods=['POST'])
@super_admin_required
def delete_faculty(faculty_id):
    """Delete a faculty."""
    Faculty.delete(faculty_id)
    flash('Faculty deleted.', 'success')
    return redirect(url_for('superadmin_bp.faculties'))


# ===== DEPARTMENT MANAGEMENT =====

@superadmin_bp.route('/departments')
@super_admin_required
def departments():
    """Manage departments."""
    user = get_current_user()
    faculty_id = request.args.get('faculty_id')
    
    if faculty_id:
        all_departments = Department.get_with_stats(faculty_id=faculty_id)
    else:
        all_departments = Department.get_with_stats()
    
    all_faculties = Faculty.load_all()
    return render_template('superadmin/departments.html', user=user,
                           departments=all_departments, faculties=all_faculties,
                           selected_faculty=faculty_id)


@superadmin_bp.route('/departments/create', methods=['POST'])
@super_admin_required
def create_department():
    """Create a new department."""
    name = request.form.get('name')
    code = request.form.get('code', '').upper().strip()
    faculty_id = request.form.get('faculty_id')
    description = request.form.get('description', '')
    
    if not name or not code or not faculty_id:
        flash('Name, code, and faculty are required.', 'danger')
        return redirect(url_for('superadmin_bp.departments'))
    
    faculty = Faculty.find_by_id(faculty_id)
    if not faculty:
        flash('Selected faculty not found.', 'danger')
        return redirect(url_for('superadmin_bp.departments'))
    
    Department.create({
        'name': name,
        'code': code,
        'faculty_id': faculty_id,
        'faculty_name': faculty.get('name', ''),
        'description': description
    })
    
    flash(f'Department "{name}" created!', 'success')
    return redirect(url_for('superadmin_bp.departments'))


@superadmin_bp.route('/departments/<dept_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_department(dept_id):
    """Edit a department."""
    dept = Department.find_by_id(dept_id)
    if not dept:
        flash('Department not found.', 'danger')
        return redirect(url_for('superadmin_bp.departments'))
    
    if request.method == 'POST':
        Department.update(dept_id, {
            'name': request.form.get('name', dept['name']),
            'code': request.form.get('code', dept.get('code', '')).upper().strip(),
            'faculty_id': request.form.get('faculty_id', dept.get('faculty_id')),
            'description': request.form.get('description', '')
        })
        flash('Department updated!', 'success')
        return redirect(url_for('superadmin_bp.departments'))
    
    user = get_current_user()
    faculties = Faculty.load_all()
    return render_template('superadmin/edit_department.html', user=user,
                           department=dept, faculties=faculties)


@superadmin_bp.route('/departments/<dept_id>/delete', methods=['POST'])
@super_admin_required
def delete_department(dept_id):
    """Delete a department."""
    Department.delete(dept_id)
    flash('Department deleted.', 'success')
    return redirect(url_for('superadmin_bp.departments'))


# ===== BATCH MANAGEMENT =====

@superadmin_bp.route('/batches')
@super_admin_required
def batches():
    """Manage batches."""
    user = get_current_user()
    faculty_id = request.args.get('faculty_id')
    department_id = request.args.get('department_id')
    
    if department_id:
        all_batches = Batch.get_with_stats(department_id=department_id)
    elif faculty_id:
        all_batches = Batch.get_with_stats(faculty_id=faculty_id)
    else:
        all_batches = Batch.get_with_stats()
    
    faculties = Faculty.load_all()
    departments = Department.load_all()
    batch_reps = User.get_by_role(User.ROLE_BATCH_REP)
    
    return render_template('superadmin/batches.html', user=user,
                           batches=all_batches, faculties=faculties,
                           departments=departments, batch_reps=batch_reps,
                           selected_faculty=faculty_id, selected_department=department_id)


@superadmin_bp.route('/batches/create', methods=['POST'])
@super_admin_required
def create_batch():
    """Create a new batch."""
    name = request.form.get('name')
    code = request.form.get('code', '').strip()
    department_id = request.form.get('department_id')
    year = request.form.get('year', '')
    rep_user_id = request.form.get('rep_user_id', '')
    
    if not name or not department_id:
        flash('Name and department are required.', 'danger')
        return redirect(url_for('superadmin_bp.batches'))
    
    dept = Department.find_by_id(department_id)
    if not dept:
        flash('Department not found.', 'danger')
        return redirect(url_for('superadmin_bp.batches'))
    
    batch = Batch.create({
        'name': name,
        'code': code,
        'department_id': department_id,
        'department_name': dept.get('name', ''),
        'faculty_id': dept.get('faculty_id', ''),
        'year': year,
        'rep_user_id': rep_user_id
    })
    
    # Update batch rep's batch_id
    if rep_user_id:
        User.update(rep_user_id, {
            'batch_id': batch['id'],
            'department_id': department_id,
            'faculty_id': dept.get('faculty_id', '')
        })
    
    flash(f'Batch "{name}" created!', 'success')
    return redirect(url_for('superadmin_bp.batches'))


@superadmin_bp.route('/batches/<batch_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_batch(batch_id):
    """Edit a batch."""
    batch = Batch.find_by_id(batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('superadmin_bp.batches'))
    
    if request.method == 'POST':
        Batch.update(batch_id, {
            'name': request.form.get('name', batch['name']),
            'code': request.form.get('code', batch.get('code', '')),
            'department_id': request.form.get('department_id', batch.get('department_id')),
            'year': request.form.get('year', batch.get('year', '')),
            'rep_user_id': request.form.get('rep_user_id', batch.get('rep_user_id', ''))
        })
        flash('Batch updated!', 'success')
        return redirect(url_for('superadmin_bp.batches'))
    
    user = get_current_user()
    departments = Department.load_all()
    batch_reps = User.get_by_role(User.ROLE_BATCH_REP)
    return render_template('superadmin/edit_batch.html', user=user,
                           batch=batch, departments=departments, batch_reps=batch_reps)


@superadmin_bp.route('/batches/<batch_id>/delete', methods=['POST'])
@super_admin_required
def delete_batch(batch_id):
    """Delete a batch."""
    Batch.delete(batch_id)
    flash('Batch deleted.', 'success')
    return redirect(url_for('superadmin_bp.batches'))


# ===== USER MANAGEMENT =====

@superadmin_bp.route('/users')
@super_admin_required
def users():
    """Manage all users."""
    user = get_current_user()
    role_filter = request.args.get('role')
    
    if role_filter:
        all_users = User.get_by_role(role_filter)
    else:
        all_users = User.load_all()
    
    faculties = Faculty.load_all()
    departments = Department.load_all()
    batches = Batch.load_all()
    
    return render_template('superadmin/users.html', user=user,
                           users=all_users, roles=User.ALL_ROLES,
                           faculties=faculties, departments=departments,
                           batches=batches, selected_role=role_filter)


@superadmin_bp.route('/users/create', methods=['POST'])
@super_admin_required
def create_user():
    """Create a new user."""
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '')
    role = request.form.get('role', '')
    faculty_id = request.form.get('faculty_id', '')
    department_id = request.form.get('department_id', '')
    batch_id = request.form.get('batch_id', '')
    
    if not email or not password or not name or not role:
        flash('Email, password, name, and role are required.', 'danger')
        return redirect(url_for('superadmin_bp.users'))
    
    if role not in User.ALL_ROLES:
        flash('Invalid role.', 'danger')
        return redirect(url_for('superadmin_bp.users'))
    
    new_user = User.create_user(
        email=email, password=password, name=name, role=role,
        faculty_id=faculty_id or None,
        department_id=department_id or None,
        batch_id=batch_id or None,
        major=request.form.get('major', ''),
        level=request.form.get('level', '')
    )
    
    if not new_user:
        flash('A user with that email already exists.', 'danger')
        return redirect(url_for('superadmin_bp.users'))
    
    flash(f'User "{name}" ({role}) created!', 'success')
    return redirect(url_for('superadmin_bp.users'))


@superadmin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_user(user_id):
    """Edit a user."""
    target_user = User.find_by_id(user_id)
    if not target_user:
        flash('User not found.', 'danger')
        return redirect(url_for('superadmin_bp.users'))
    
    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name', target_user['name']),
            'email': request.form.get('email', target_user['email']).lower().strip(),
            'role': request.form.get('role', target_user['role']),
            'faculty_id': request.form.get('faculty_id', '') or None,
            'department_id': request.form.get('department_id', '') or None,
            'batch_id': request.form.get('batch_id', '') or None,
            'is_active': request.form.get('is_active', 'true') == 'true'
        }
        
        new_password = request.form.get('password', '')
        if new_password:
            from werkzeug.security import generate_password_hash
            update_data['password_hash'] = generate_password_hash(new_password)
        
        User.update(user_id, update_data)
        flash('User updated!', 'success')
        return redirect(url_for('superadmin_bp.users'))
    
    user = get_current_user()
    faculties = Faculty.load_all()
    departments = Department.load_all()
    batches = Batch.load_all()
    return render_template('superadmin/edit_user.html', user=user,
                           target_user=target_user, roles=User.ALL_ROLES,
                           faculties=faculties, departments=departments, batches=batches)


@superadmin_bp.route('/users/<user_id>/delete', methods=['POST'])
@super_admin_required
def delete_user(user_id):
    """Delete a user."""
    User.delete(user_id)
    flash('User deleted.', 'success')
    return redirect(url_for('superadmin_bp.users'))


# ===== SETTINGS =====

@superadmin_bp.route('/settings', methods=['GET', 'POST'])
@super_admin_required
def settings():
    """System settings (AI, Telegram, etc.)."""
    from app.utils.gemini_ai import load_ai_settings, get_available_providers
    from app.utils.telegram_bot import set_telegram_token, load_telegram_token
    
    user = get_current_user()
    current_token = load_telegram_token() or ""
    ai_settings = load_ai_settings()
    ai_providers = get_available_providers()
    
    if request.method == 'POST':
        telegram_token = request.form.get('telegram_token')
        telegram_username = request.form.get('telegram_username')
        
        if telegram_token:
            set_telegram_token(telegram_token, telegram_username)
            flash('Settings updated!', 'success')
        
        return redirect(url_for('superadmin_bp.settings'))
    
    return render_template('superadmin/settings.html', user=user,
                           telegram_token=current_token,
                           ai_settings=ai_settings, ai_providers=ai_providers)
