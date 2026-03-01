from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.utils.auth import login_required
from app.models.lecture import Lecture
from app.models.news import News
from app.models.student import Student
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.models.grade import Grade
from app.models.feedback import Feedback
from app.utils.telegram_bot import notify_new_lecture, notify_new_news, set_telegram_token, load_telegram_token
from app.utils.n8n_webhook import send_news_webhook, send_assignment_webhook
from app.utils.assignments import (
    get_all_assignments, create_assignment as create_assignment_util, delete_assignment,
    get_all_submissions_for_assignment, grade_assignment,
    get_assignment_by_id, update_assignment
)

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    latest_lectures = Lecture.get_latest_lectures(5)
    latest_news = News.get_latest_news(5)
    new_feedback = Feedback.get_by_status(Feedback.STATUS_NEW)
    all_students = Student.load_all()
    
    return render_template(
        'admin/dashboard.html',
        lectures=latest_lectures,
        news=latest_news,
        feedback=new_feedback,
        students=all_students
    )

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Admin settings"""
    from app.utils.gemini_ai import load_ai_settings, get_available_providers
    
    # Get current Telegram token
    current_token = load_telegram_token() or ""
    
    # Get current Telegram username from config
    current_username = current_app.config.get('TELEGRAM_BOT_USERNAME', "")
    if current_username == "your_bot_username":
        current_username = ""
    
    # Get AI settings
    ai_settings = load_ai_settings()
    ai_providers = get_available_providers()
    
    if request.method == 'POST':
        telegram_token = request.form.get('telegram_token')
        telegram_username = request.form.get('telegram_username')
        
        if telegram_token:
            # Set the new token and username
            set_telegram_token(telegram_token, telegram_username)
            
            # Update the app config
            current_app.config['TELEGRAM_BOT_USERNAME'] = telegram_username
            
            flash('Telegram bot settings updated successfully!', 'success')
        
        return redirect(url_for('admin_bp.settings'))
    
    return render_template('admin/settings.html', 
                           telegram_token=current_token, 
                           telegram_username=current_username,
                           ai_settings=ai_settings,
                           ai_providers=ai_providers)

@admin_bp.route('/settings/ai', methods=['POST'])
@login_required
def save_ai_settings():
    """Save AI provider settings after testing the API"""
    from app.utils.gemini_ai import load_ai_settings, save_ai_settings as save_settings, test_provider
    
    ai_provider = request.form.get('ai_provider', 'gemini')
    skip_test = request.form.get('skip_test', 'false') == 'true'
    
    # Test the provider first (unless skipped)
    if not skip_test:
        test_result = test_provider(ai_provider)
        if not test_result['success']:
            flash(f'Cannot switch to {ai_provider.title()}: {test_result["message"]}', 'danger')
            return redirect(url_for('admin_bp.settings'))
    
    # Load current settings and update
    settings = load_ai_settings()
    settings['provider'] = ai_provider
    
    if save_settings(settings):
        flash(f'AI provider changed to {ai_provider.title()}! API verified successfully.', 'success')
    else:
        flash('Failed to save AI settings.', 'danger')
    
    return redirect(url_for('admin_bp.settings'))

@admin_bp.route('/settings/ai/test', methods=['POST'])
@login_required
def test_ai_provider():
    """Test if an AI provider's API is working (AJAX endpoint)"""
    from app.utils.gemini_ai import test_provider
    
    data = request.get_json()
    provider = data.get('provider', 'gemini') if data else request.form.get('provider', 'gemini')
    
    print(f"Testing AI provider: {provider}")
    result = test_provider(provider)
    print(f"Test result: {result}")
    
    return jsonify(result)


@admin_bp.route('/lectures', methods=['GET', 'POST'])
@login_required
def lectures():
    """Manage lectures"""
    subjects = Subject.load_all()
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        week = request.form.get('week')
        lecture_type = request.form.get('lecture_type')
        description = request.form.get('description')
        
        # Handle file upload
        if 'lecture_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['lecture_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'lectures')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Get subject name for notifications
            subject_name = "Unknown Subject"
            for subject in subjects:
                if subject.get('id') == subject_id:
                    subject_name = subject.get('name')
            
            # Create lecture record
            if week is not None:
                week_num = int(week)
            else:
                week_num = 0
                
            lecture = Lecture.create({
                'subject_id': subject_id,
                'subject_name': subject_name,
                'week': week_num,
                'lecture_type': lecture_type,
                'description': description,
                'file_name': filename,
                'file_path': os.path.join('lectures', filename)
            })
            
            # Send notification
            notify_new_lecture(lecture)
            
            flash('Lecture uploaded successfully!', 'success')
            return redirect(url_for('admin_bp.lectures'))
    
    all_lectures = Lecture.load_all()
    
    # Create a dictionary mapping subject_id to semester for easy lookup in template
    subject_semesters = {}
    for subject in subjects:
        subject_semesters[subject.get('id')] = subject.get('semester')
    
    return render_template('admin/lectures.html', 
                           lectures=all_lectures, 
                           subjects=subjects, 
                           subject_semesters=subject_semesters)

@admin_bp.route('/subjects/<string:subject_id>/add-lecture', methods=['GET', 'POST'])
@login_required
def add_lecture(subject_id):
    """Add lecture to a subject"""
    subject = Subject.find_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_bp.subjects'))
    
    if request.method == 'POST':
        week = request.form.get('week')
        lecture_type = request.form.get('lecture_type')
        description = request.form.get('description')
        
        # Handle file upload
        if 'lecture_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['lecture_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'lectures')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Create lecture record
            if week is not None and week != '':
                week_num = int(week)
            else:
                week_num = 0
                
            lecture = Lecture.create({
                'subject_id': subject_id,
                'subject_name': subject.get('name'),
                'week': week_num,
                'lecture_type': lecture_type,
                'description': description,
                'file_name': filename,
                'file_path': os.path.join('lectures', filename)
            })
            
            # Send notification
            notify_new_lecture(lecture)
            
            flash('Lecture uploaded successfully!', 'success')
            return redirect(url_for('main_bp.subject_detail', subject_id=subject_id))
    
    # GET request - show the form
    return render_template('admin/add_lecture.html', subject=subject)

@admin_bp.route('/lectures/<string:lecture_id>/delete', methods=['POST'])
@login_required
def delete_lecture(lecture_id):
    """Delete lecture"""
    lecture = Lecture.delete(lecture_id)
    if lecture:
        flash('Lecture deleted successfully!', 'success')
    else:
        flash('Lecture not found.', 'danger')
    return redirect(url_for('admin_bp.lectures'))

@admin_bp.route('/lectures/<string:lecture_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lecture(lecture_id):
    """Edit lecture"""
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('admin_bp.lectures'))
    
    subjects = Subject.load_all()
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        week = request.form.get('week')
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Get subject name for reference
        subject_name = "Unknown Subject"
        for subject in subjects:
            if subject.get('id') == subject_id:
                subject_name = subject.get('name')
        
        # Update lecture record
        if week is not None:
            week_num = int(week)
        else:
            week_num = 0
            
        Lecture.update(lecture_id, {
            'subject_id': subject_id,
            'subject_name': subject_name,
            'week': week_num,
            'title': title,
            'description': description
        })
        
        flash('Lecture updated successfully!', 'success')
        return redirect(url_for('admin_bp.lectures'))
    
    # For now, just redirect to lectures page since the template was deleted
    flash('Edit functionality is currently unavailable.', 'warning')
    return redirect(url_for('admin_bp.lectures'))

@admin_bp.route('/lectures/<string:lecture_id>/add-material', methods=['GET', 'POST'])
@login_required
def add_material(lecture_id):
    """Add material to lecture"""
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('admin_bp.lectures'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Handle file upload
        if 'material_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['material_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'lectures')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Create material
            from app.models.lecture import LectureMaterial
            
            material = LectureMaterial(
                lecture_id=lecture_id,
                title=title,
                description=description,
                filename=os.path.join('lectures', filename),
                file_type=file.content_type
            )
            material.save()
            
            flash('Material added successfully!', 'success')
            return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))
    
    # For now, just redirect to lecture detail page since the template was deleted
    flash('Add material functionality is currently unavailable.', 'warning')
    return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))

@admin_bp.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    """Manage subjects"""
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        description = request.form.get('description')
        semester = request.form.get('semester')
        instructor = request.form.get('instructor')
        schedule_days = request.form.get('schedule_days')
        schedule_time = request.form.get('schedule_time')
        location = request.form.get('location')
        
        # Create subject record
        subject = Subject.create({
            'code': code,
            'name': name,
            'description': description,
            'semester': semester,
            'instructor': instructor,
            'schedule_days': schedule_days,
            'schedule_time': schedule_time,
            'location': location
        })
        
        flash('Subject created successfully!', 'success')
        return redirect(url_for('admin_bp.subjects'))
    
    all_subjects = Subject.load_all()
    
    return render_template('admin/subjects.html', subjects=all_subjects)

@admin_bp.route('/subjects/<string:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    """Edit subject"""
    subject = Subject.find_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_bp.subjects'))
    
    # Get all terms (in a real app, this would come from a Term model)
    terms = [
        {'id': 'fall2023', 'name': 'Fall 2023'},
        {'id': 'spring2024', 'name': 'Spring 2024'},
        {'id': 'summer2024', 'name': 'Summer 2024'},
        {'id': 'fall2024', 'name': 'Fall 2024'}
    ]
    
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        description = request.form.get('description')
        semester = request.form.get('semester')
        instructor = request.form.get('instructor')
        schedule_days = request.form.get('schedule_days')
        schedule_time = request.form.get('schedule_time')
        location = request.form.get('location')
        
        # Update subject record
        Subject.update(subject_id, {
            'code': code,
            'name': name,
            'description': description,
            'semester': semester,
            'instructor': instructor,
            'schedule_days': schedule_days,
            'schedule_time': schedule_time,
            'location': location
        })
        
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('main_bp.subject_detail', subject_id=subject_id))
    
    # For GET requests, render the edit_subject.html template with the subject data
    return render_template('admin/edit_subject.html', subject=subject)

@admin_bp.route('/subjects/<string:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """Delete subject"""
    subject = Subject.delete(subject_id)
    if subject:
        flash('Subject deleted successfully!', 'success')
    else:
        flash('Subject not found.', 'danger')
    return redirect(url_for('admin_bp.subjects'))

@admin_bp.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    """Manage news"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Create news record
        news_item = News.create({
            'title': title,
            'content': content
        })
        
        # Send Telegram notification
        notify_new_news(news_item)
        
        # Send n8n webhook
        send_news_webhook(news_item, action="created")
        
        flash('News item created successfully!', 'success')
        return redirect(url_for('admin_bp.news'))
    
    all_news = News.load_all()
    return render_template('admin/news.html', news=all_news)

@admin_bp.route('/news/<string:news_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    """Edit news item"""
    news_item = News.find_by_id(news_id)
    if not news_item:
        flash('News item not found.', 'danger')
        return redirect(url_for('admin_bp.news'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Store original data before update
        original_news = News.find_by_id(news_id)
        
        # Update news record
        updated_news = News.update(news_id, {
            'title': title,
            'content': content
        })
        
        # Send n8n webhook for update with original data
        if updated_news and original_news:
            send_news_webhook(updated_news, action="updated", original_data=original_news)
        
        flash('News item updated successfully!', 'success')
        return redirect(url_for('admin_bp.news'))
    
    return render_template('admin/edit_news.html', news=news_item)

@admin_bp.route('/news/<string:news_id>/delete', methods=['POST'])
@login_required
def delete_news(news_id):
    """Delete news item"""
    # Get the news item before deletion for webhook
    news_item = News.find_by_id(news_id)
    
    # Delete the news item
    deleted_news = News.delete(news_id)
    if deleted_news:
        # Send n8n webhook for deletion
        send_news_webhook(news_item, action="deleted")
        flash('News item deleted successfully!', 'success')
    else:
        flash('News item not found.', 'danger')
    return redirect(url_for('admin_bp.news'))

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    """Manage students"""
    if request.method == 'POST':
        name = request.form.get('name')
        major = request.form.get('major')
        level = request.form.get('level')
        
        # Generate token for student
        token = Student.generate_token()
        
        # Create student record
        student = Student.create({
            'name': name,
            'major': major,
            'level': level,
            'token': token
        })
        
        flash(f'Student created successfully! Token: {token}', 'success')
        return redirect(url_for('admin_bp.students'))
    
    all_students = Student.load_all()
    return render_template('admin/students.html', students=all_students)


@admin_bp.route('/students/<string:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    """Edit student"""
    student = Student.find_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_bp.students'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        major = request.form.get('major')
        level = request.form.get('level')
        
        # Update student record
        Student.update(student_id, {
            'name': name,
            'major': major,
            'level': level
        })
        
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin_bp.students'))
    
    # For GET requests, render the edit_student.html template with the student data
    return render_template('admin/edit_student.html', student=student)


@admin_bp.route('/students/<string:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    """Delete student"""
    student = Student.find_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_bp.students'))
    
    # Delete student record
    Student.delete(student_id)
    
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('admin_bp.students'))

@admin_bp.route('/attendance')
@login_required
def attendance():
    """Manage attendance"""
    subjects = Subject.load_all()
    students = Student.load_all()
    
    # Get selected subject
    subject_id = request.args.get('subject_id')
    if subject_id:
        # Get attendance records for this subject
        attendance_records = Attendance.get_by_subject(subject_id)
    else:
        attendance_records = []
    
    return render_template(
        'admin/attendance.html',
        subjects=subjects,
        students=students,
        attendance=attendance_records,
        selected_subject=subject_id
    )

@admin_bp.route('/attendance/update', methods=['POST'])
@login_required
def update_attendance():
    """Update attendance with improved error handling"""
    try:
        # Get required parameters
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        lecture_number_str = request.form.get('lecture_number')
        
        # Validate required parameters
        if not student_id or not subject_id or lecture_number_str is None:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400
            
        # Validate student_id and subject_id
        if student_id == "null" or subject_id == "null":
            return jsonify({
                'success': False,
                'message': 'Invalid student or subject ID'
            }), 400
        
        # Ensure lecture_number is an integer
        try:
            lecture_number = int(lecture_number_str)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid lecture number format'
            }), 400
            
        is_present = request.form.get('is_present') == 'true'
        is_excused = request.form.get('is_excused') == 'true'
        
        # Update attendance
        result = Attendance.mark_attendance(student_id, subject_id, lecture_number, is_present, is_excused)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Attendance updated successfully',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update attendance'
            }), 500
    except Exception as e:
        print(f"Error in update_attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@admin_bp.route('/grades')
@login_required
def grades():
    """Manage grades"""
    subjects = Subject.load_all()
    students = Student.load_all()
    
    # Get selected subject
    subject_id = request.args.get('subject_id')
    if subject_id:
        # Get grade records for this subject
        grade_records = Grade.get_by_subject(subject_id)
    else:
        grade_records = []
    
    return render_template(
        'admin/grades.html',
        subjects=subjects,
        students=students,
        grades=grade_records,
        selected_subject=subject_id
    )

@admin_bp.route('/grades/update', methods=['POST'])
@login_required
def update_grades():
    """Update grades with improved error handling"""
    try:
        # Get required parameters
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        grade_type = request.form.get('grade_type')
        grade_value = request.form.get('grade_value')
        
        # Validate required parameters
        if not student_id or not subject_id or not grade_type:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400
            
        # Validate student_id and subject_id
        if student_id == "null" or subject_id == "null":
            return jsonify({
                'success': False,
                'message': 'Invalid student or subject ID'
            }), 400
        
        # Update grade
        result = Grade.set_grade(student_id, subject_id, grade_type, grade_value)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Grade updated successfully',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update grade'
            }), 500
    except Exception as e:
        print(f"Error in update_grades: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@admin_bp.route('/feedback')
@login_required
def feedback():
    """Manage feedback"""
    status = request.args.get('status', Feedback.STATUS_NEW)
    feedback_items = Feedback.get_by_status(status)
    
    return render_template(
        'admin/feedback.html',
        feedback=feedback_items,
        current_status=status
    )

@admin_bp.route('/feedback/<string:feedback_id>')
@login_required
def feedback_detail(feedback_id):
    """View feedback detail"""
    feedback_item = Feedback.find_by_id(feedback_id)
    if not feedback_item:
        flash('Feedback not found.', 'danger')
        return redirect(url_for('admin_bp.feedback'))
    
    return render_template('admin/feedback_detail.html', feedback=feedback_item)

@admin_bp.route('/feedback/<string:feedback_id>/reply', methods=['POST'])
@login_required
def feedback_reply(feedback_id):
    """Reply to feedback"""
    feedback_item = Feedback.find_by_id(feedback_id)
    if not feedback_item:
        flash('Feedback not found.', 'danger')
        return redirect(url_for('admin_bp.feedback'))
    
    reply_text = request.form.get('reply')
    if reply_text:
        Feedback.add_reply(feedback_id, reply_text, is_admin=True)
        flash('Reply added successfully!', 'success')
    
    return redirect(url_for('admin_bp.feedback_detail', feedback_id=feedback_id))

@admin_bp.route('/feedback/<string:feedback_id>/status', methods=['POST'])
@login_required
def feedback_status(feedback_id):
    """Update feedback status"""
    feedback_item = Feedback.find_by_id(feedback_id)
    if not feedback_item:
        flash('Feedback not found.', 'danger')
        return redirect(url_for('admin_bp.feedback'))
    
    status = request.form.get('status')
    if status:
        Feedback.update_status(feedback_id, status)
        flash('Status updated successfully!', 'success')
    
    return redirect(url_for('admin_bp.feedback_detail', feedback_id=feedback_id))

# ===== ASSIGNMENTS ROUTES =====

@admin_bp.route('/assignments')
@login_required
def assignments():
    """Admin assignments management page"""
    # Get all assignments
    all_assignments = get_all_assignments()
    homework = all_assignments.get('weekly_homework', [])
    projects = all_assignments.get('final_projects', [])
    presentations = all_assignments.get('presentations', [])
    
    # Get all subjects
    subjects = Subject.load_all()
    
    # Get all students for counting
    all_students = Student.load_all()
    total_students = len(all_students)
    
    # Add submission counts to each assignment
    for hw in homework:
        submissions = get_all_submissions_for_assignment(hw['id'], 'weekly_homework')
        hw['submitted_count'] = len([s for s in submissions if s['submission'].get('status') in ['done', 'graded']])
        hw['total_students'] = total_students
    
    for proj in projects:
        submissions = get_all_submissions_for_assignment(proj['id'], 'final_projects')
        proj['submitted_count'] = len([s for s in submissions if s['submission'].get('status') in ['done', 'graded']])
        proj['total_students'] = total_students
    
    for pres in presentations:
        submissions = get_all_submissions_for_assignment(pres['id'], 'presentations')
        pres['submitted_count'] = len([s for s in submissions if s['submission'].get('status') in ['done', 'graded']])
        pres['total_students'] = total_students
    
    # Calculate statistics
    stats = {
        'total_homework': len(homework),
        'total_projects': len(projects),
        'total_presentations': len(presentations),
        'pending_submissions': 0,
        'to_grade': 0
    }
    
    # Count pending and to grade
    for student in all_students:
        student_assignments = student.get('assignments', {})
        for hw in student_assignments.get('weekly_homework', []):
            if hw.get('status') == 'in_progress':
                stats['pending_submissions'] += 1
            elif hw.get('status') == 'done':
                stats['to_grade'] += 1
        for proj in student_assignments.get('final_projects', []):
            if proj.get('status') == 'in_progress':
                stats['pending_submissions'] += 1
            elif proj.get('status') == 'done':
                stats['to_grade'] += 1
        for pres in student_assignments.get('presentations', []):
            if pres.get('status') == 'in_progress':
                stats['pending_submissions'] += 1
            elif pres.get('status') == 'done':
                stats['to_grade'] += 1
    
    return render_template(
        'admin/assignments.html',
        homework=homework,
        projects=projects,
        presentations=presentations,
        subjects=subjects,
        stats=stats,
        submissions_count=stats['to_grade']
    )

@admin_bp.route('/assignments/create/new')
@login_required
def create_assignment_page():
    """Show create assignment page"""
    assignment_type = request.args.get('type', 'weekly_homework')
    subjects = Subject.load_all()
    
    return render_template(
        'admin/create_assignment.html',
        assignment_type=assignment_type,
        subjects=subjects
    )

@admin_bp.route('/assignments/create', methods=['POST'])
@login_required
def create_assignment():
    """Create new assignment"""
    assignment_type = request.form.get('assignment_type')
    subject_id = request.form.get('subject_id')
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    week = request.form.get('week')
    degree = request.form.get('degree', 10)  # Default to 10 points
    
    # Convert degree to integer
    try:
        degree = int(degree)
    except (ValueError, TypeError):
        degree = 10
    
    # Get subject name
    subject = Subject.find_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_bp.assignments'))
    
    # Create assignment data
    assignment_data = {
        'id': f"{assignment_type[:4]}_{subject_id}_{uuid.uuid4().hex[:8]}",
        'subject_id': subject_id,
        'subject_name': subject.get('name'),
        'title': title,
        'description': description,
        'due_date': due_date,
        'degree': degree,
        'max_file_size_mb': 5,
        'created_by': 'admin',
        'created_at': datetime.now().isoformat()
    }
    
    # Add week for homework
    if assignment_type == 'weekly_homework' and week:
        assignment_data['week'] = int(week)
    
    # Create assignment
    result = create_assignment_util(assignment_type, assignment_data)
    
    # Determine type label for flash message
    type_labels = {
        'weekly_homework': 'Homework',
        'final_projects': 'Project',
        'presentations': 'Presentation'
    }
    type_label = type_labels.get(assignment_type, 'Assignment')
    
    if result:
        # Send webhook notification for new assignment
        send_assignment_webhook(assignment_data, assignment_type, action="created")
        flash(f'{type_label} "{title}" created successfully!', 'success')
    else:
        flash(f'Failed to create {type_label.lower()}.', 'danger')
    
    return redirect(url_for('admin_bp.assignments'))

@admin_bp.route('/assignments/<assignment_id>/edit')
@login_required
def edit_assignment(assignment_id):
    """Edit assignment page"""
    assignment_type = request.args.get('type', 'weekly_homework')
    
    # Get assignment details
    assignment = get_assignment_by_id(assignment_id, assignment_type)
    
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('admin_bp.assignments'))
    
    # Get all subjects
    subjects = Subject.load_all()
    
    return render_template(
        'admin/edit_assignment.html',
        assignment=assignment,
        assignment_type=assignment_type,
        subjects=subjects
    )

@admin_bp.route('/assignments/<assignment_id>/update', methods=['POST'])
@login_required
def update_assignment_route(assignment_id):
    """Update assignment"""
    assignment_type = request.form.get('assignment_type', 'weekly_homework')
    subject_id = request.form.get('subject_id')
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    week = request.form.get('week')
    degree = request.form.get('degree', 10)
    
    # Convert degree to integer
    try:
        degree = int(degree)
    except (ValueError, TypeError):
        degree = 10
    
    # Get subject name
    subject = Subject.find_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_bp.assignments'))
    
    # Update assignment data
    updated_data = {
        'subject_id': subject_id,
        'subject_name': subject.get('name'),
        'title': title,
        'description': description,
        'due_date': due_date,
        'degree': degree
    }
    
    # Add week for homework
    if assignment_type == 'weekly_homework' and week:
        updated_data['week'] = int(week)
    
    # Update assignment
    result = update_assignment(assignment_id, assignment_type, updated_data)
    
    # Determine type label
    type_labels = {
        'weekly_homework': 'Homework',
        'final_projects': 'Project',
        'presentations': 'Presentation'
    }
    type_label = type_labels.get(assignment_type, 'Assignment')
    
    if result:
        flash(f'{type_label} "{title}" updated successfully!', 'success')
    else:
        flash('Failed to update assignment.', 'danger')
    
    return redirect(url_for('admin_bp.assignments'))

@admin_bp.route('/assignments/<assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment_route(assignment_id):
    """Delete assignment"""
    data = request.get_json()
    assignment_type = data.get('assignment_type', 'weekly_homework')
    
    success = delete_assignment(assignment_id, assignment_type)
    
    if success:
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to delete assignment'}), 500

@admin_bp.route('/assignments/<assignment_id>/submissions')
@login_required
def view_submissions(assignment_id):
    """View all submissions for an assignment"""
    assignment_type = request.args.get('type', 'weekly_homework')
    
    # Get assignment details
    from app.utils.assignments import get_assignment_by_id
    assignment = get_assignment_by_id(assignment_id, assignment_type)
    
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('admin_bp.assignments'))
    
    # Get all submissions
    submissions = get_all_submissions_for_assignment(assignment_id, assignment_type)
    
    return render_template(
        'admin/assignment_submissions.html',
        assignment=assignment,
        assignment_type=assignment_type,
        submissions=submissions
    )

@admin_bp.route('/assignments/<assignment_id>/grade', methods=['POST'])
@login_required
def grade_assignment_route(assignment_id):
    """Grade a student's assignment (0-10 scale)"""
    student_id = request.form.get('student_id')
    grade = request.form.get('grade')
    feedback = request.form.get('feedback', '')
    assignment_type = request.form.get('assignment_type', 'weekly_homework')
    
    try:
        grade = float(grade)
        # Enforce 0-10 limit
        if grade < 0:
            grade = 0
        elif grade > 10:
            grade = 10
    except (ValueError, TypeError):
        flash('Invalid grade value.', 'danger')
        return redirect(url_for('admin_bp.view_submissions', assignment_id=assignment_id, type=assignment_type))
    
    # Grade the assignment
    success = grade_assignment(student_id, assignment_id, grade, feedback, assignment_type)
    
    if not success:
        flash('Failed to grade assignment. Student or assignment not found.', 'danger')
        return redirect(url_for('admin_bp.view_submissions', assignment_id=assignment_id, type=assignment_type))
    
    # Get assignment details to find subject
    assignment = get_assignment_by_id(assignment_id, assignment_type)
    if assignment:
        subject_id = assignment.get('subject_id')
        
        # Update student's grades in the grades system
        student = Student.find_by_id(student_id)
        if student:
            # Get existing grades for this subject
            existing_grades = Grade.get_by_student_and_subject(student_id, subject_id)
            
            if existing_grades:
                # Update homework grade
                grade_record = existing_grades[0]
                Grade.update_homework_grade(grade_record['id'], grade)
            else:
                # Create new grade record with homework grade
                Grade.create({
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'homework': grade,
                    'midterm': 0,
                    'final': 0,
                    'total': grade  # Only homework for now
                })
    
    flash(f'✓ Assignment graded successfully! Grade: {grade}/10', 'success')
    return redirect(url_for('admin_bp.view_submissions', assignment_id=assignment_id, type=assignment_type))

@admin_bp.route('/assignments/download/<path:filepath>')
@login_required
def download_assignment_file(filepath):
    """Download student submission file (admin access)"""
    import os
    from flask import send_file
    
    file_path = os.path.join('app/static/uploads', filepath)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('admin_bp.assignments'))
    
    return send_file(file_path, as_attachment=True) 