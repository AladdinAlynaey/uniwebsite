from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from app.utils.auth import verify_admin_password
from app.models.news import News
from app.models.subject import Subject
from app.models.lecture import Lecture
from app.models.student import Student
from app.utils.gemini_ai import generate_response
import os

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    # Get latest news
    latest_news = News.get_latest_news(5)
    
    # Get real statistics
    subjects_count = len(Subject.load_all())
    lectures_count = len(Lecture.load_all())
    students_count = len(Student.load_all())
    
    # Pass statistics to the template
    return render_template('index.html', 
                           news=latest_news,
                           subjects_count=subjects_count,
                           lectures_count=lectures_count,
                           students_count=students_count)

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
    # Get all subjects grouped by semester
    all_subjects = Subject.load_all()
    
    # Get unique semesters from subjects
    semesters = set()
    for subject in all_subjects:
        if 'semester' in subject:
            semesters.add(subject['semester'])
    
    # Convert to sorted list
    semesters = sorted(list(semesters))
    
    # Organize subjects by semester
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
    
    # Get lectures for this subject
    lectures = Lecture.get_lectures_by_subject(subject_id)
    
    return render_template('subject_detail.html', subject=subject, lectures=lectures)

@main_bp.route('/lecture/<string:lecture_id>')
def lecture_detail(lecture_id):
    """Lecture detail page"""
    lecture = Lecture.find_by_id(lecture_id)
    if not lecture:
        flash('Lecture not found.', 'danger')
        return redirect(url_for('main_bp.subjects'))
    
    # Get the subject for this lecture
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
    
    # Check if the material file exists
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
    
    # Check if the lecture has a file
    if not hasattr(lecture, 'file_name') or not lecture.file_name or not hasattr(lecture, 'file_path') or not lecture.file_path:
        flash('No file available for this lecture.', 'warning')
        return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))
    
    # Get the file path
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    file_path = lecture.file_path
    
    # Extract just the filename from the path
    filename = os.path.basename(file_path)
    
    # Determine the directory containing the file
    file_dir = os.path.dirname(os.path.join(uploads_dir, file_path))
    
    if not os.path.exists(os.path.join(uploads_dir, file_path)):
        flash('Lecture file not found on server.', 'danger')
        return redirect(url_for('main_bp.lecture_detail', lecture_id=lecture_id))
    
    return send_from_directory(os.path.join(uploads_dir, os.path.dirname(file_path)), 
                               filename, 
                               as_attachment=True)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        
        if verify_admin_password(password):
            session['is_admin'] = True
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('admin_bp.dashboard'))
        else:
            flash('Invalid password.', 'danger')
    
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))

@main_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Student login page"""
    from app.models.student import Student
    
    if request.method == 'POST':
        token = request.form.get('token')
        student = Student.find_by_token(token)
        
        if student:
            session['student_token'] = token
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('student_bp.dashboard'))
        else:
            flash('Invalid student token.', 'danger')
    
    return render_template('student_login.html')

@main_bp.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    """Chatbot page"""
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Ensure chat_history is a list
    if not isinstance(session['chat_history'], list):
        session['chat_history'] = []
    
    # Check if clear chat action was requested
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
            
            # Add the new message pair to chat history
            # Ensure response is a string
            if response is None:
                response = "I'm sorry, I couldn't generate a response at this time."
                
            session['chat_history'].append({
                'query': query,
                'response': response,
                'timestamp': 'Just now'
            })
            # Save the updated session
            session.modified = True
    
    return render_template('chatbot.html', chat_history=session['chat_history']) 