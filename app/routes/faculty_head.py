"""
Faculty Head Routes — Faculty management portal.

Controls departments, batches, and teachers within their faculty.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils.auth import faculty_head_required, get_current_user
from app.models.user import User
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.batch import Batch
from app.models.subject import Subject
from app.models.teacher_subject import TeacherSubject

faculty_bp = Blueprint('faculty_bp', __name__)


def _get_faculty_id():
    """Get the current faculty head's faculty ID."""
    user = get_current_user()
    return user.get('faculty_id') if user else None


@faculty_bp.route('/dashboard')
@faculty_head_required
def dashboard():
    """Faculty overview dashboard."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    faculty = Faculty.find_by_id(faculty_id) if faculty_id else None
    
    departments = Department.get_by_faculty(faculty_id) if faculty_id else []
    batches = Batch.get_by_faculty(faculty_id) if faculty_id else []
    teachers = User.get_teachers_by_faculty(faculty_id) if faculty_id else []
    students = []
    for batch in batches:
        students.extend(User.get_by_batch(batch['id']))
    
    stats = {
        'departments': len(departments),
        'batches': len(batches),
        'teachers': len(teachers),
        'students': len(students)
    }
    
    return render_template('faculty/dashboard.html', user=user, faculty=faculty,
                           stats=stats, departments=departments, batches=batches)


# ===== DEPARTMENT MANAGEMENT =====

@faculty_bp.route('/departments')
@faculty_head_required
def departments():
    """Manage departments in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    all_departments = Department.get_with_stats(faculty_id=faculty_id)
    faculty = Faculty.find_by_id(faculty_id) if faculty_id else None
    
    return render_template('faculty/departments.html', user=user,
                           departments=all_departments, faculty=faculty)


@faculty_bp.route('/departments/create', methods=['POST'])
@faculty_head_required
def create_department():
    """Create department in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    faculty = Faculty.find_by_id(faculty_id) if faculty_id else None
    
    name = request.form.get('name')
    code = request.form.get('code', '').upper().strip()
    description = request.form.get('description', '')
    
    if not name or not code:
        flash('Name and code are required.', 'danger')
        return redirect(url_for('faculty_bp.departments'))
    
    Department.create({
        'name': name,
        'code': code,
        'faculty_id': faculty_id,
        'faculty_name': faculty.get('name', '') if faculty else '',
        'description': description
    })
    
    flash(f'Department "{name}" created!', 'success')
    return redirect(url_for('faculty_bp.departments'))


@faculty_bp.route('/departments/<dept_id>/delete', methods=['POST'])
@faculty_head_required
def delete_department(dept_id):
    """Delete a department (must be in this faculty)."""
    user = get_current_user()
    dept = Department.find_by_id(dept_id)
    if not dept or dept.get('faculty_id') != user.get('faculty_id'):
        flash('Department not found or access denied.', 'danger')
        return redirect(url_for('faculty_bp.departments'))
    
    Department.delete(dept_id)
    flash('Department deleted.', 'success')
    return redirect(url_for('faculty_bp.departments'))


# ===== BATCH MANAGEMENT =====

@faculty_bp.route('/batches')
@faculty_head_required
def batches():
    """Manage batches in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    department_id = request.args.get('department_id')
    
    if department_id:
        all_batches = Batch.get_with_stats(department_id=department_id)
    else:
        all_batches = Batch.get_with_stats(faculty_id=faculty_id)
    
    departments = Department.get_by_faculty(faculty_id) if faculty_id else []
    batch_reps = User.get_by_role(User.ROLE_BATCH_REP)
    
    return render_template('faculty/batches.html', user=user,
                           batches=all_batches, departments=departments,
                           batch_reps=batch_reps, selected_department=department_id)


@faculty_bp.route('/batches/create', methods=['POST'])
@faculty_head_required
def create_batch():
    """Create a batch in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    
    name = request.form.get('name')
    code = request.form.get('code', '').strip()
    department_id = request.form.get('department_id')
    year = request.form.get('year', '')
    rep_user_id = request.form.get('rep_user_id', '')
    
    if not name or not department_id:
        flash('Name and department are required.', 'danger')
        return redirect(url_for('faculty_bp.batches'))
    
    # Verify department is in this faculty
    dept = Department.find_by_id(department_id)
    if not dept or dept.get('faculty_id') != faculty_id:
        flash('Invalid department.', 'danger')
        return redirect(url_for('faculty_bp.batches'))
    
    batch = Batch.create({
        'name': name,
        'code': code,
        'department_id': department_id,
        'department_name': dept.get('name', ''),
        'faculty_id': faculty_id,
        'year': year,
        'rep_user_id': rep_user_id
    })
    
    if rep_user_id:
        User.update(rep_user_id, {
            'batch_id': batch['id'],
            'department_id': department_id,
            'faculty_id': faculty_id
        })
    
    flash(f'Batch "{name}" created!', 'success')
    return redirect(url_for('faculty_bp.batches'))


@faculty_bp.route('/batches/<batch_id>/delete', methods=['POST'])
@faculty_head_required
def delete_batch(batch_id):
    """Delete a batch in this faculty."""
    user = get_current_user()
    batch = Batch.find_by_id(batch_id)
    if not batch or batch.get('faculty_id') != user.get('faculty_id'):
        flash('Batch not found or access denied.', 'danger')
        return redirect(url_for('faculty_bp.batches'))
    
    Batch.delete(batch_id)
    flash('Batch deleted.', 'success')
    return redirect(url_for('faculty_bp.batches'))


# ===== TEACHER MANAGEMENT =====

@faculty_bp.route('/teachers')
@faculty_head_required
def teachers():
    """Manage teachers in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    all_teachers = User.get_teachers_by_faculty(faculty_id) if faculty_id else []
    
    # Enrich with subject assignments
    for teacher in all_teachers:
        assignments = TeacherSubject.get_by_teacher(teacher['id'])
        teacher['subject_count'] = len(assignments)
    
    subjects = Subject.get_by_faculty(faculty_id) if faculty_id else []
    batches = Batch.get_by_faculty(faculty_id) if faculty_id else []
    
    return render_template('faculty/teachers.html', user=user,
                           teachers=all_teachers, subjects=subjects, batches=batches)


@faculty_bp.route('/teachers/create', methods=['POST'])
@faculty_head_required
def create_teacher():
    """Create a teacher in this faculty."""
    user = get_current_user()
    faculty_id = user.get('faculty_id')
    
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '')
    
    if not email or not password or not name:
        flash('Email, password, and name are required.', 'danger')
        return redirect(url_for('faculty_bp.teachers'))
    
    new_teacher = User.create_user(
        email=email, password=password, name=name,
        role=User.ROLE_TEACHER, faculty_id=faculty_id
    )
    
    if not new_teacher:
        flash('A user with that email already exists.', 'danger')
        return redirect(url_for('faculty_bp.teachers'))
    
    flash(f'Teacher "{name}" created!', 'success')
    return redirect(url_for('faculty_bp.teachers'))


@faculty_bp.route('/teachers/<teacher_id>/assign', methods=['POST'])
@faculty_head_required
def assign_teacher_subject(teacher_id):
    """Assign a teacher to a subject in a batch."""
    subject_id = request.form.get('subject_id')
    batch_id = request.form.get('batch_id')
    
    if not subject_id or not batch_id:
        flash('Subject and batch are required.', 'danger')
        return redirect(url_for('faculty_bp.teachers'))
    
    TeacherSubject.assign(teacher_id, subject_id, batch_id)
    flash('Teacher assigned to subject!', 'success')
    return redirect(url_for('faculty_bp.teachers'))


@faculty_bp.route('/teachers/<teacher_id>/delete', methods=['POST'])
@faculty_head_required
def delete_teacher(teacher_id):
    """Delete a teacher."""
    user = get_current_user()
    teacher = User.find_by_id(teacher_id)
    if not teacher or teacher.get('faculty_id') != user.get('faculty_id'):
        flash('Teacher not found or access denied.', 'danger')
        return redirect(url_for('faculty_bp.teachers'))
    
    User.delete(teacher_id)
    flash('Teacher deleted.', 'success')
    return redirect(url_for('faculty_bp.teachers'))
