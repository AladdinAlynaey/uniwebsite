"""
Teacher Routes — Teacher portal.

Teachers can manage grades, attendance, assignments, and lectures
for the subjects they are assigned to in specific batches.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.utils.auth import teacher_required, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.batch import Batch
from app.models.teacher_subject import TeacherSubject
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.grade import Grade
from app.utils.assignments import (
    get_all_assignments, create_assignment as create_assignment_util,
    delete_assignment, get_all_submissions_for_assignment, grade_assignment,
    get_assignment_by_id
)
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

teacher_bp = Blueprint('teacher_bp', __name__)


@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    """Teacher dashboard showing assigned subjects."""
    user = get_current_user()
    assignments = TeacherSubject.get_teacher_subjects_with_details(user['id'])
    
    stats = {
        'subjects': len(assignments),
        'batches': len(set(a['batch_id'] for a in assignments)),
        'total_students': 0
    }
    
    for assignment in assignments:
        students = User.get_by_batch(assignment['batch_id'])
        assignment['student_count'] = len(students)
        stats['total_students'] += len(students)
    
    return render_template('teacher/dashboard.html', user=user,
                           assignments=assignments, stats=stats)


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>')
@teacher_required
def subject_overview(subject_id, batch_id):
    """Overview of a subject in a specific batch."""
    user = get_current_user()
    
    # Verify teacher is assigned to this subject/batch
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        flash('You are not assigned to this subject.', 'danger')
        return redirect(url_for('teacher_bp.dashboard'))
    
    subject = Subject.find_by_id(subject_id)
    batch = Batch.find_by_id(batch_id)
    students = User.get_by_batch(batch_id)
    
    return render_template('teacher/subject_overview.html', user=user,
                           subject=subject, batch=batch, students=students)


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/attendance')
@teacher_required
def attendance(subject_id, batch_id):
    """Manage attendance for a subject in a batch."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_bp.dashboard'))
    
    subject = Subject.find_by_id(subject_id)
    batch = Batch.find_by_id(batch_id)
    students = User.get_by_batch(batch_id)
    attendance_records = Attendance.get_by_subject(subject_id)
    
    return render_template('teacher/attendance.html', user=user,
                           subject=subject, batch=batch, students=students,
                           attendance=attendance_records)


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/attendance/update', methods=['POST'])
@teacher_required
def update_attendance(subject_id, batch_id):
    """Update attendance for a student."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student_id = request.form.get('student_id')
    lecture_number = request.form.get('lecture_number')
    is_present = request.form.get('is_present') == 'true'
    is_excused = request.form.get('is_excused') == 'true'
    
    try:
        lecture_number = int(lecture_number)
        result = Attendance.mark_attendance(student_id, subject_id, lecture_number, is_present, is_excused)
        
        if result:
            return jsonify({'success': True, 'message': 'Attendance updated', 'data': result})
        return jsonify({'success': False, 'message': 'Failed to update'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/grades')
@teacher_required
def grades(subject_id, batch_id):
    """Manage grades for a subject in a batch."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_bp.dashboard'))
    
    subject = Subject.find_by_id(subject_id)
    batch = Batch.find_by_id(batch_id)
    students = User.get_by_batch(batch_id)
    grade_records = Grade.get_by_subject(subject_id)
    
    return render_template('teacher/grades.html', user=user,
                           subject=subject, batch=batch, students=students,
                           grades=grade_records)


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/grades/update', methods=['POST'])
@teacher_required
def update_grades(subject_id, batch_id):
    """Update a grade for a student."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student_id = request.form.get('student_id')
    grade_type = request.form.get('grade_type')
    grade_value = request.form.get('grade_value')
    
    try:
        result = Grade.set_grade(student_id, subject_id, grade_type, grade_value)
        if result:
            return jsonify({'success': True, 'message': 'Grade updated', 'data': result})
        return jsonify({'success': False, 'message': 'Failed to update'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/lectures', methods=['GET', 'POST'])
@teacher_required
def lectures(subject_id, batch_id):
    """Manage lectures for a subject."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_bp.dashboard'))
    
    subject = Subject.find_by_id(subject_id)
    batch = Batch.find_by_id(batch_id)
    
    if request.method == 'POST':
        week = request.form.get('week', '0')
        lecture_type = request.form.get('lecture_type', 'Theoretical')
        description = request.form.get('description', '')
        
        if 'lecture_file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        file = request.files['lecture_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'lectures')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            
            Lecture.create({
                'subject_id': subject_id,
                'subject_name': subject.get('name', '') if subject else '',
                'batch_id': batch_id,
                'week': int(week),
                'lecture_type': lecture_type,
                'description': description,
                'file_name': filename,
                'file_path': os.path.join('lectures', filename),
                'uploaded_by': user['id']
            })
            
            flash('Lecture uploaded!', 'success')
            return redirect(url_for('teacher_bp.lectures', subject_id=subject_id, batch_id=batch_id))
    
    all_lectures = Lecture.get_lectures_by_subject(subject_id)
    
    return render_template('teacher/lectures.html', user=user,
                           subject=subject, batch=batch, lectures=all_lectures)


@teacher_bp.route('/subject/<subject_id>/batch/<batch_id>/assignments')
@teacher_required
def assignments(subject_id, batch_id):
    """Manage assignments for a subject in a batch."""
    user = get_current_user()
    
    assignment = TeacherSubject.find_assignment(user['id'], subject_id, batch_id)
    if not assignment and user.get('role') != User.ROLE_SUPER_ADMIN:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_bp.dashboard'))
    
    subject = Subject.find_by_id(subject_id)
    batch = Batch.find_by_id(batch_id)
    
    all_assignments = get_all_assignments()
    
    # Filter assignments for this subject
    subject_assignments = {
        'weekly_homework': [a for a in all_assignments.get('weekly_homework', []) if a.get('subject_id') == subject_id],
        'final_projects': [a for a in all_assignments.get('final_projects', []) if a.get('subject_id') == subject_id],
        'presentations': [a for a in all_assignments.get('presentations', []) if a.get('subject_id') == subject_id]
    }
    
    return render_template('teacher/assignments.html', user=user,
                           subject=subject, batch=batch, assignments=subject_assignments)
