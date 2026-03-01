from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils.auth import student_token_required, get_current_student
from app.models.lecture import Lecture
from app.models.news import News
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.models.grade import Grade
from app.models.feedback import Feedback
from app.utils.assignments import (
    get_all_assignments, get_student_submissions, update_submission_status,
    submit_assignment, get_assignment_by_id
)
from app.utils.file_upload import save_assignment_file, get_file_icon
import os

student_bp = Blueprint('student_bp', __name__)

@student_bp.route('/dashboard')
@student_token_required
def dashboard():
    """Student dashboard"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
        
    latest_lectures = Lecture.get_latest_lectures(5)
    latest_news = News.get_latest_news(3)
    
    return render_template(
        'student/dashboard.html',
        student=student,
        lectures=latest_lectures,
        news=latest_news
    )

@student_bp.route('/profile')
@student_token_required
def profile():
    """Student profile"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
        
    return render_template('student/profile.html', student=student)

@student_bp.route('/lectures')
@student_token_required
def lectures():
    """Student lectures"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
        
    # Get all lectures grouped by week
    all_lectures = Lecture.load_all()
    lectures_by_week = {}
    
    for lecture in all_lectures:
        week = lecture.get('week')
        if week not in lectures_by_week:
            lectures_by_week[week] = []
        lectures_by_week[week].append(lecture)
    
    # Sort weeks
    sorted_weeks = sorted(lectures_by_week.keys())
    
    return render_template(
        'student/lectures.html',
        lectures_by_week=lectures_by_week,
        weeks=sorted_weeks
    )

@student_bp.route('/attendance')
@student_token_required
def attendance():
    """Student attendance"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    # Get all subjects
    subjects = Subject.load_all()
    
    # Get attendance records for this student
    attendance_by_subject = {}
    for subject in subjects:
        if subject and 'id' in subject:
            attendance_records = Attendance.get_by_student_and_subject(student['id'], subject['id'])
            attendance_by_subject[subject['id']] = attendance_records
    
    return render_template(
        'student/attendance.html',
        student=student,
        subjects=subjects,
        attendance_by_subject=attendance_by_subject
    )

@student_bp.route('/grades')
@student_token_required
def grades():
    """Student grades"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    # Get all subjects
    subjects = Subject.load_all()
    
    # Get grade records for this student
    grades_by_subject = {}
    for subject in subjects:
        if subject and 'id' in subject:
            grade_records = Grade.get_by_student_and_subject(student['id'], subject['id'])
            grades_by_subject[subject['id']] = grade_records
    
    return render_template(
        'student/grades.html',
        student=student,
        subjects=subjects,
        grades_by_subject=grades_by_subject
    )

@student_bp.route('/feedback', methods=['GET', 'POST'])
@student_token_required
def feedback():
    """Student feedback form"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        feedback_type = request.form.get('type')
        
        # Create feedback record
        feedback_item = Feedback.create({
            'student_id': student['id'],
            'student_name': student.get('name', 'Unknown Student'),
            'subject': subject,
            'message': message,
            'type': feedback_type,
            'status': Feedback.STATUS_NEW,
            'replies': []
        })
        
        flash('Your feedback has been submitted successfully!', 'success')
        return redirect(url_for('student_bp.feedback_history'))
    
    return render_template('student/feedback_form.html', student=student)

@student_bp.route('/feedback/history')
@student_token_required
def feedback_history():
    """Student feedback history"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    # Get feedback records for this student
    feedback_items = Feedback.get_by_student(student['id'])
    
    return render_template(
        'student/feedback_history.html',
        student=student,
        feedback=feedback_items
    )

@student_bp.route('/feedback/<string:feedback_id>')
@student_token_required
def feedback_detail(feedback_id):
    """View feedback detail"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    feedback_item = Feedback.find_by_id(feedback_id)
    if not feedback_item or feedback_item.get('student_id') != student['id']:
        flash('Feedback not found.', 'danger')
        return redirect(url_for('student_bp.feedback_history'))
    
    return render_template('student/feedback_detail.html', feedback=feedback_item)

@student_bp.route('/feedback/<string:feedback_id>/reply', methods=['POST'])
@student_token_required
def feedback_reply(feedback_id):
    """Reply to feedback"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    feedback_item = Feedback.find_by_id(feedback_id)
    if not feedback_item or feedback_item.get('student_id') != student['id']:
        flash('Feedback not found.', 'danger')
        return redirect(url_for('student_bp.feedback_history'))
    
    reply_text = request.form.get('reply')
    if reply_text:
        Feedback.add_reply(feedback_id, reply_text, is_admin=False)
        flash('Reply added successfully!', 'success')
    
    return redirect(url_for('student_bp.feedback_detail', feedback_id=feedback_id))

@student_bp.route('/assignment/<string:assignment_id>')
@student_token_required
def view_assignment(assignment_id):
    """View assignment details"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    from app.models.lecture import Assignment
    assignment = Assignment.find_by_id(assignment_id)
    
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('student_bp.dashboard'))
    
    # Get the lecture for this assignment
    lecture = Lecture.find_by_id(assignment.lecture_id)
    
    # Get the subject for this lecture
    subject = None
    if lecture:
        subject = Subject.find_by_id(lecture.subject_id)
    
    # For now, redirect to dashboard since the template was deleted
    flash('Assignment view functionality is currently unavailable.', 'warning')
    return redirect(url_for('student_bp.dashboard'))

@student_bp.route('/lecture/<string:lecture_id>/complete', methods=['POST'])
@student_token_required
def mark_lecture_completed(lecture_id):
    """Mark a lecture as completed"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('student_bp.dashboard'))
    
    # In a real app, you would store this in a CompletedLecture model
    # For now, we'll just show a success message
    flash('Lecture marked as completed!', 'success')
    
    return redirect(url_for('student_bp.lectures'))

# ===== TASKS/ASSIGNMENTS ROUTES =====

@student_bp.route('/tasks')
@student_token_required
def tasks():
    """Student tasks page - Weekly Homework, Final Projects, and Presentations"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    # Get all assignments
    all_assignments = get_all_assignments()
    
    # Get student submissions
    student_submissions = get_student_submissions(student['id'])
    if not student_submissions:
        student_submissions = {'final_projects': [], 'weekly_homework': [], 'presentations': []}
    
    # Process weekly homework grouped by subject
    homework_by_subject = {}
    for hw in all_assignments.get('weekly_homework', []):
        subject_id = hw.get('subject_id')
        
        if subject_id not in homework_by_subject:
            homework_by_subject[subject_id] = {
                'subject_name': hw.get('subject_name'),
                'weeks': {}
            }
        
        # Find student's submission for this homework
        student_hw = None
        for sub in student_submissions.get('weekly_homework', []):
            if sub.get('id') == hw.get('id'):
                student_hw = sub
                break
        
        # Merge assignment data with submission data
        hw_data = hw.copy()
        if student_hw:
            hw_data.update({
                'status': student_hw.get('status', 'not_started'),
                'submitted_at': student_hw.get('submitted_at'),
                'files': [
                    {**f, 'icon': get_file_icon(f.get('extension', ''))}
                    for f in student_hw.get('files', [])
                ],
                'grade': student_hw.get('grade'),
                'feedback': student_hw.get('feedback')
            })
        else:
            hw_data['status'] = 'not_started'
            hw_data['files'] = []
        
        # Check if overdue
        try:
            due_date = datetime.fromisoformat(hw.get('due_date', datetime.now().isoformat()))
            hw_data['is_overdue'] = datetime.now() > due_date and hw_data['status'] not in ['done', 'graded']
        except:
            hw_data['is_overdue'] = False
        
        homework_by_subject[subject_id]['weeks'][hw.get('week')] = hw_data
    
    # Process final projects
    final_projects = []
    for proj in all_assignments.get('final_projects', []):
        # Find student's submission
        student_proj = None
        for sub in student_submissions.get('final_projects', []):
            if sub.get('id') == proj.get('id'):
                student_proj = sub
                break
        
        # Merge data
        proj_data = proj.copy()
        if student_proj:
            proj_data.update({
                'status': student_proj.get('status', 'not_started'),
                'submitted_at': student_proj.get('submitted_at'),
                'files': [
                    {**f, 'icon': get_file_icon(f.get('extension', ''))}
                    for f in student_proj.get('files', [])
                ],
                'grade': student_proj.get('grade'),
                'feedback': student_proj.get('feedback')
            })
        else:
            proj_data['status'] = 'not_started'
            proj_data['files'] = []
        
        # Check if overdue
        try:
            due_date = datetime.fromisoformat(proj.get('due_date', datetime.now().isoformat()))
            proj_data['is_overdue'] = datetime.now() > due_date and proj_data['status'] not in ['done', 'graded']
        except:
            proj_data['is_overdue'] = False
        
        final_projects.append(proj_data)
    
    # Process presentations
    presentations = []
    for pres in all_assignments.get('presentations', []):
        # Find student's submission
        student_pres = None
        for sub in student_submissions.get('presentations', []):
            if sub.get('id') == pres.get('id'):
                student_pres = sub
                break
        
        # Merge data
        pres_data = pres.copy()
        if student_pres:
            pres_data.update({
                'status': student_pres.get('status', 'not_started'),
                'submitted_at': student_pres.get('submitted_at'),
                'files': [
                    {**f, 'icon': get_file_icon(f.get('extension', ''))}
                    for f in student_pres.get('files', [])
                ],
                'grade': student_pres.get('grade'),
                'feedback': student_pres.get('feedback')
            })
        else:
            pres_data['status'] = 'not_started'
            pres_data['files'] = []
        
        # Check if overdue
        try:
            due_date = datetime.fromisoformat(pres.get('due_date', datetime.now().isoformat()))
            pres_data['is_overdue'] = datetime.now() > due_date and pres_data['status'] not in ['done', 'graded']
        except:
            pres_data['is_overdue'] = False
        
        presentations.append(pres_data)
    
    # Calculate statistics
    all_tasks = list(homework_by_subject.values())
    total_hw = sum(len(subject['weeks']) for subject in all_tasks)
    total_proj = len(final_projects)
    total_pres = len(presentations)
    
    stats = {
        'total': total_hw + total_proj + total_pres,
        'in_progress': 0,
        'completed': 0,
        'overdue': 0
    }
    
    # Count homework stats
    for subject in all_tasks:
        for hw in subject['weeks'].values():
            if hw.get('status') == 'in_progress':
                stats['in_progress'] += 1
            elif hw.get('status') in ['done', 'graded']:
                stats['completed'] += 1
            if hw.get('is_overdue'):
                stats['overdue'] += 1
    
    # Count project stats
    for proj in final_projects:
        if proj.get('status') == 'in_progress':
            stats['in_progress'] += 1
        elif proj.get('status') in ['done', 'graded']:
            stats['completed'] += 1
        if proj.get('is_overdue'):
            stats['overdue'] += 1
    
    # Count presentation stats
    for pres in presentations:
        if pres.get('status') == 'in_progress':
            stats['in_progress'] += 1
        elif pres.get('status') in ['done', 'graded']:
            stats['completed'] += 1
        if pres.get('is_overdue'):
            stats['overdue'] += 1
    
    return render_template(
        'student/tasks.html',
        student=student,
        homework_by_subject=homework_by_subject,
        final_projects=final_projects,
        presentations=presentations,
        homework_count=total_hw,
        projects_count=total_proj,
        presentations_count=total_pres,
        stats=stats
    )

@student_bp.route('/tasks/update-status', methods=['POST'])
@student_token_required
def update_assignment_status():
    """Update assignment status (not_started, in_progress, done)"""
    student = get_current_student()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 401
    
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    status = data.get('status')
    assignment_type = data.get('assignment_type', 'weekly_homework')
    
    if not assignment_id or not status:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Update status
    success = update_submission_status(student['id'], assignment_id, status, assignment_type)
    
    if success:
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update status'}), 500

@student_bp.route('/tasks/upload/<assignment_id>')
@student_token_required
def upload_assignment_page(assignment_id):
    """Show upload assignment page"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    assignment_type = request.args.get('type', 'weekly_homework')
    
    # Get assignment details
    assignment = get_assignment_by_id(assignment_id, assignment_type)
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('student_bp.tasks'))
    
    # Get student's submission
    student_submissions = get_student_submissions(student['id'])
    if not student_submissions:
        student_submissions = {'final_projects': [], 'weekly_homework': []}
    
    # Find this assignment's submission
    submission = None
    for sub in student_submissions.get(assignment_type, []):
        if sub.get('id') == assignment_id:
            submission = sub
            break
    
    # Merge assignment with submission data
    assignment_data = assignment.copy()
    if submission:
        assignment_data.update({
            'status': submission.get('status', 'not_started'),
            'files': [
                {**f, 'icon': get_file_icon(f.get('extension', ''))}
                for f in submission.get('files', [])
            ],
            'grade': submission.get('grade'),
            'feedback': submission.get('feedback')
        })
    else:
        assignment_data['status'] = 'not_started'
        assignment_data['files'] = []
    
    return render_template(
        'student/upload_assignment.html',
        assignment=assignment_data,
        assignment_type=assignment_type
    )

@student_bp.route('/tasks/submit', methods=['POST'])
@student_token_required
def submit_assignment():
    """Submit assignment with files"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    assignment_id = request.form.get('assignment_id')
    assignment_type = request.form.get('assignment_type', 'weekly_homework')
    
    if not assignment_id:
        flash('Assignment ID is required.', 'danger')
        return redirect(url_for('student_bp.tasks'))
    
    # Get uploaded files
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        flash('Please select at least one file to upload.', 'warning')
        return redirect(url_for('student_bp.tasks'))
    
    # Save files
    files_data = []
    total_size = 0
    
    for file in files:
        if file and file.filename:
            file_info = save_assignment_file(file, student['id'], assignment_id)
            
            if file_info:
                file_info['icon'] = get_file_icon(file_info.get('extension', ''))
                files_data.append(file_info)
                total_size += file_info.get('size', 0)
            else:
                flash('One or more files failed validation. Please check file size and type.', 'danger')
                return redirect(url_for('student_bp.tasks'))
    
    # Check total size
    if total_size > 5 * 1024 * 1024:
        flash('Total file size exceeds 5MB limit.', 'danger')
        return redirect(url_for('student_bp.tasks'))
    
    # Submit assignment
    from app.utils.assignments import submit_assignment as submit_assignment_util
    success = submit_assignment_util(student['id'], assignment_id, files_data, assignment_type)
    
    if success:
        flash('Assignment submitted successfully!', 'success')
    else:
        flash('Failed to submit assignment. Please try again.', 'danger')
    
    return redirect(url_for('student_bp.tasks'))

@student_bp.route('/tasks/download/<path:filepath>')
@student_token_required
def download_submission(filepath):
    """Download submitted file"""
    student = get_current_student()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main_bp.student_login'))
    
    # Security check: ensure the file belongs to this student
    if not filepath.startswith(f'assignments/{student["id"]}/'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('student_bp.tasks'))
    
    file_path = os.path.join('app/static/uploads', filepath)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('student_bp.tasks'))
    
    return send_file(file_path, as_attachment=True)