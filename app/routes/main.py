from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from app.utils.auth import get_current_user, login_user, logout_user
from app.models.user import User
from app.models.news import News
from app.models.subject import Subject
from app.models.lecture import Lecture
from app.models.faculty import Faculty
from app.models.batch import Batch
from app.utils.gemini_ai import generate_response
import os

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    latest_news = News.get_latest_news(5)
    
    # Get real statistics
    subjects_count = len(Subject.load_all())
    lectures_count = len(Lecture.load_all())
    faculties_count = len(Faculty.load_all())
    batches_count = len(Batch.load_all())
    students = User.get_by_role(User.ROLE_STUDENT) if hasattr(User, 'ROLE_STUDENT') else []
    students_count = len(students)
    
    return render_template('index.html', 
                           news=latest_news,
                           subjects_count=subjects_count,
                           lectures_count=lectures_count,
                           students_count=students_count,
                           faculties_count=faculties_count,
                           batches_count=batches_count)

@main_bp.route('/news')
def news():
    """News page"""
    all_news = News.get_latest_news()
    return render_template('news.html', news=all_news)

@main_bp.route('/news/<string:news_id>')
def news_detail(news_id):
    """News detail page"""
    news_item = News.find_by_id(news_id)
    if not news_item:
        flash('News item not found.', 'danger')
        return redirect(url_for('main_bp.news'))
    return render_template('news_detail.html', news=news_item)

@main_bp.route('/subjects')
def subjects():
    """Subjects page"""
    all_subjects = Subject.load_all()
    
    semesters = set()
    for subject in all_subjects:
        if 'semester' in subject:
            semesters.add(subject['semester'])
    
    semesters = sorted(list(semesters))
    
    subjects_by_semester = {}
    for semester in semesters:
        subjects_by_semester[semester] = Subject.get_subjects_by_semester(semester)
    
    return render_template('subjects.html', semesters=semesters, subjects_by_semester=subjects_by_semester)

@main_bp.route('/subjects/<string:subject_id>')
def subject_detail(subject_id):
    """Subject detail page"""
    subject = Subject.find_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('main_bp.subjects'))
    
    lectures = Lecture.get_lectures_by_subject(subject_id)
    
    return render_template('subject_detail.html', subject=subject, lectures=lectures)

@main_bp.route('/lecture/<string:lecture_id>')
def lecture_detail(lecture_id):
    """Lecture detail page"""
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('main_bp.subjects'))
    
    subject = Subject.find_by_id(lecture.subject_id)
    
    return render_template('lecture_detail.html', lecture=lecture, subject=subject)

@main_bp.route('/material/<string:material_id>')
def download_material(material_id):
    """Download lecture material"""
    from app.models.lecture import LectureMaterial
    
    material = LectureMaterial.find_by_id(material_id)
    if not material:
        flash('Material not found.', 'danger')
        return redirect(url_for('main_bp.index'))
    
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    if not os.path.exists(os.path.join(uploads_dir, material.filename)):
        flash('Material file not found.', 'danger')
        return redirect(url_for('main_bp.lecture_detail', lecture_id=material.lecture_id))
    
    return send_from_directory(uploads_dir, material.filename, as_attachment=True)

@main_bp.route('/download-lecture/<string:lecture_id>')
def download_lecture_file(lecture_id):
    """Download lecture file directly"""
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('main_bp.subjects'))
    
    if not hasattr(lecture, 'file_name') or not lecture.file_name or not hasattr(lecture, 'file_path') or not lecture.file_path:
        flash('No file available for this lecture.', 'warning')
        return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))
    
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    file_path = lecture.file_path
    filename = os.path.basename(file_path)
    
    if not os.path.exists(os.path.join(uploads_dir, file_path)):
        flash('Lecture file not found on server.', 'danger')
        return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))
    
    return send_from_directory(os.path.join(uploads_dir, os.path.dirname(file_path)), 
                               filename, 
                               as_attachment=True)


# ===== UNIFIED LOGIN =====

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login page — handles all roles."""
    # If already logged in, redirect to appropriate dashboard
    user = get_current_user()
    if user:
        return _redirect_to_dashboard(user)
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')
        
        # Find user by email
        user = User.find_by_email(email)
        
        if user and User.check_password(user, password):
            if not user.get('is_active', True):
                flash('Your account has been deactivated. Contact an administrator.', 'danger')
                return render_template('login.html')
            
            login_user(user)
            flash(f'Welcome, {user.get("name", "User")}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return _redirect_to_dashboard(user)
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))


@main_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Student login — supports both email/password and legacy token."""
    user = get_current_user()
    if user and user.get('role') == User.ROLE_STUDENT:
        return redirect(url_for('student_bp.dashboard'))
    
    if request.method == 'POST':
        # Try token login first (backward compat)
        token = request.form.get('token', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        found_user = None
        
        if token:
            found_user = User.find_by_token(token)
            if not found_user:
                flash('Invalid student token.', 'danger')
                return render_template('student_login.html')
        elif email and password:
            found_user = User.find_by_email(email)
            if not found_user or not User.check_password(found_user, password):
                flash('Invalid email or password.', 'danger')
                return render_template('student_login.html')
            if found_user.get('role') != User.ROLE_STUDENT:
                flash('This login is for students only. Use the main login page.', 'danger')
                return render_template('student_login.html')
        else:
            flash('Please enter your token or email/password.', 'danger')
            return render_template('student_login.html')
        
        if found_user:
            if not found_user.get('is_active', True):
                flash('Your account has been deactivated.', 'danger')
                return render_template('student_login.html')
            
            login_user(found_user)
            flash(f'Welcome, {found_user.get("name", "Student")}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('student_bp.dashboard'))
    
    return render_template('student_login.html')


@main_bp.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    """Chatbot page"""
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    if not isinstance(session['chat_history'], list):
        session['chat_history'] = []
    
    if request.args.get('clear') == '1':
        session['chat_history'] = []
        session.modified = True
        flash('Chat history cleared.', 'info')
        return redirect(url_for('main_bp.chatbot'))
    
    if request.method == 'POST':
        query = request.form.get('query')
        student_token = session.get('student_token')
        
        if query:
            response = generate_response(query, student_token)
            
            if response is None:
                response = "I'm sorry, I couldn't generate a response at this time."
                
            session['chat_history'].append({
                'query': query,
                'response': response,
                'timestamp': 'Just now'
            })
            session.modified = True
    
    return render_template('chatbot.html', chat_history=session['chat_history']) 


def _redirect_to_dashboard(user):
    """Redirect user to their appropriate dashboard based on role."""
    role = user.get('role')
    
    if role == User.ROLE_SUPER_ADMIN:
        return redirect(url_for('superadmin_bp.dashboard'))
    elif role == User.ROLE_FACULTY_HEAD:
        return redirect(url_for('faculty_bp.dashboard'))
    elif role == User.ROLE_BATCH_REP:
        return redirect(url_for('admin_bp.dashboard'))
    elif role == User.ROLE_TEACHER:
        return redirect(url_for('teacher_bp.dashboard'))
    elif role == User.ROLE_STUDENT:
        return redirect(url_for('student_bp.dashboard'))
    
    return redirect(url_for('main_bp.index'))