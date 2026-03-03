from flask import Blueprint, request, jsonify, session
from app.models.student import Student
from app.models.telegram_user import TelegramUser
from app.models.news import News
from app.models.lecture import Lecture
from app.utils.telegram_bot import handle_webhook, handle_news_command, handle_lectures_command
from app.utils.gemini_ai import generate_response
from app.utils.n8n_webhook import test_webhook_connection, send_news_webhook
from app.models.attendance import Attendance
from app.models.grade import Grade
from app.models.feedback import Feedback
from app.models.subject import Subject

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook"""
    data = request.json
    
    # Use the handle_webhook function to process the request
    result = handle_webhook(data)
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Webhook handled successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to process webhook'
        })

@api_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """API endpoint for chatbot with conversation memory"""
    import logging
    logger = logging.getLogger(__name__)
    
    data = request.json
    logger.info(f"Received chatbot request: {data}")
    
    if not data or 'query' not in data:
        logger.error("No query provided in request")
        return jsonify({'status': 'error', 'message': 'No query provided'})
    
    query = data['query']
    student_token = session.get('student_token')  # Get token from session
    logger.info(f"Processing query: {query}")
    
    # Get full user for role-aware context
    from app.utils.auth import get_current_user
    current_user = get_current_user()
    
    # Get existing chat history from session
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    if not isinstance(session['chat_history'], list):
        session['chat_history'] = []
    
    # Limit history to last 10 exchanges to avoid context overflow
    chat_history = session['chat_history'][-10:]
    
    # Generate response with conversation history
    try:
        response = generate_response(query, student_token, chat_history, user=current_user)
        logger.info(f"Generated response: {response[:100]}...")
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        response = f"I apologize, but I encountered an error: {str(e)}"
    
    # Add the new message pair to chat history
    session['chat_history'].append({
        'query': query,
        'response': response,
        'timestamp': 'Just now'
    })
    
    # Keep only last 20 messages in session to prevent bloat
    if len(session['chat_history']) > 20:
        session['chat_history'] = session['chat_history'][-20:]
    
    # Save the updated session
    session.modified = True
    
    logger.info(f"Returning response with status: success")
    return jsonify({
        'status': 'success',
        'response': response
    })

@api_bp.route('/lectures', methods=['GET'])
def get_lectures():
    """API endpoint to get lectures"""
    week = request.args.get('week')
    subject_id = request.args.get('subject_id')
    
    if week:
        try:
            week = int(week)
            lectures = Lecture.get_lectures_by_week(week)
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid week parameter'})
    elif subject_id:
        lectures = Lecture.get_lectures_by_subject(subject_id)
    else:
        lectures = Lecture.load_all()
    
    return jsonify({
        'status': 'success',
        'lectures': lectures
    })

@api_bp.route('/news', methods=['GET'])
def get_news():
    """API endpoint to get news"""
    limit = request.args.get('limit')
    
    if limit:
        try:
            limit = int(limit)
            news_items = News.get_latest_news(limit)
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid limit parameter'})
    else:
        news_items = News.get_latest_news()
    
    return jsonify({
        'status': 'success',
        'news': news_items
    })

@api_bp.route('/webhook/test', methods=['POST'])
def test_n8n_webhook():
    """Test n8n webhook connection"""
    try:
        result = test_webhook_connection()
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Webhook connection test successful'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Webhook connection test failed'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error testing webhook: {str(e)}'
        }), 500

@api_bp.route('/webhook/send-test-news', methods=['POST'])
def send_test_news_webhook():
    """Send a test news webhook to n8n"""
    try:
        # Create a test news item
        test_news = {
            'id': 'test-news-001',
            'title': 'Updated Test News Item',
            'content': 'This is an updated test news item to demonstrate the before/after functionality.',
            'created_at': '2024-01-01T12:00:00',
            'updated_at': '2024-01-01T14:30:00'
        }
        
        # Create original data to simulate an update
        original_test_news = {
            'id': 'test-news-001',
            'title': 'Original Test News Item',
            'content': 'This was the original content before the update.',
            'created_at': '2024-01-01T12:00:00',
            'updated_at': '2024-01-01T12:00:00'
        }
        
        result = send_news_webhook(test_news, action="updated", original_data=original_test_news)
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Test news webhook sent successfully',
                'data': test_news
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test news webhook'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error sending test news webhook: {str(e)}'
        }), 500

@api_bp.route('/student/data', methods=['GET'])
def get_student_data():
    """Get all student data by token for n8n Telegram integration"""
    try:
        # Get token from query parameter
        token = request.args.get('token')
        
        # Validate token exists
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'No token provided',
                'data': None
            }), 400
        
        # Find student by token
        student = Student.find_by_token(token)
        if not student:
            return jsonify({
                'status': 'error',
                'message': 'Invalid token - student not found',
                'data': None
            }), 404
        
        # Get student ID
        student_id = student.get('id')
        
        # Gather all student-related data
        student_data = {
            'student_info': {
                'id': student.get('id'),
                'name': student.get('name'),
                'major': student.get('major'),
                'level': student.get('level'),
                'token': student.get('token'),
                'created_at': student.get('created_at'),
                'updated_at': student.get('updated_at')
            },
            'attendance': [],
            'grades': [],
            'feedback': [],
            'subjects': [],
            'news': [],
            'lectures': []
        }
        
        # Get attendance records
        attendance_records = Attendance.get_by_student(student_id)
        for record in attendance_records:
            # Get subject name for attendance
            subject = Subject.find_by_id(record.get('subject_id'))
            student_data['attendance'].append({
                'id': record.get('id'),
                'subject_id': record.get('subject_id'),
                'subject_name': subject.get('name') if subject else 'Unknown Subject',
                'lecture_number': record.get('lecture_number'),
                'is_present': record.get('is_present'),
                'is_excused': record.get('is_excused'),
                'created_at': record.get('created_at'),
                'updated_at': record.get('updated_at')
            })
        
        # Get grade records
        grade_records = Grade.get_by_student(student_id)
        for record in grade_records:
            # Get subject name for grades
            subject = Subject.find_by_id(record.get('subject_id'))
            student_data['grades'].append({
                'id': record.get('id'),
                'subject_id': record.get('subject_id'),
                'subject_name': subject.get('name') if subject else 'Unknown Subject',
                'grade_type': record.get('grade_type'),
                'grade_value': record.get('grade_value'),
                'created_at': record.get('created_at'),
                'updated_at': record.get('updated_at')
            })
        
        # Get feedback records
        feedback_records = Feedback.get_by_student(student_id)
        for record in feedback_records:
            student_data['feedback'].append({
                'id': record.get('id'),
                'subject': record.get('subject'),
                'message': record.get('message'),
                'type': record.get('type'),
                'status': record.get('status'),
                'replies': record.get('replies', []),
                'created_at': record.get('created_at'),
                'updated_at': record.get('updated_at')
            })
        
        # Get all subjects (for context)
        all_subjects = Subject.load_all()
        for subject in all_subjects:
            student_data['subjects'].append({
                'id': subject.get('id'),
                'code': subject.get('code'),
                'name': subject.get('name'),
                'description': subject.get('description'),
                'semester': subject.get('semester'),
                'instructor': subject.get('instructor'),
                'schedule_days': subject.get('schedule_days'),
                'schedule_time': subject.get('schedule_time'),
                'location': subject.get('location')
            })
        
        # Get latest news (relevant to all students)
        latest_news = News.get_latest_news(10)
        for news in latest_news:
            student_data['news'].append({
                'id': news.get('id'),
                'title': news.get('title'),
                'content': news.get('content'),
                'created_at': news.get('created_at'),
                'updated_at': news.get('updated_at')
            })
        
        # Get latest lectures (relevant to all students)
        latest_lectures = Lecture.load_all()
        # Sort by created_at and limit to 20
        sorted_lectures = sorted(
            latest_lectures, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )[:20]
        
        for lecture in sorted_lectures:
            student_data['lectures'].append({
                'id': lecture.get('id'),
                'subject_id': lecture.get('subject_id'),
                'subject_name': lecture.get('subject_name'),
                'week': lecture.get('week'),
                'lecture_type': lecture.get('lecture_type'),
                'description': lecture.get('description'),
                'file_name': lecture.get('file_name'),
                'file_path': lecture.get('file_path'),
                'created_at': lecture.get('created_at'),
                'updated_at': lecture.get('updated_at')
            })
        
        # Calculate summary statistics
        summary = {
            'total_attendance_records': len(student_data['attendance']),
            'total_grades': len(student_data['grades']),
            'total_feedback': len(student_data['feedback']),
            'attendance_rate': 0,
            'average_grade': 0
        }
        
        # Calculate attendance rate
        if student_data['attendance']:
            present_count = sum(1 for att in student_data['attendance'] if att['is_present'])
            summary['attendance_rate'] = round((present_count / len(student_data['attendance'])) * 100, 2)
        
        # Calculate average grade (only numeric grades)
        numeric_grades = []
        for grade in student_data['grades']:
            try:
                if grade['grade_value'] and grade['grade_value'] != '':
                    numeric_grades.append(float(grade['grade_value']))
            except (ValueError, TypeError):
                continue
        
        if numeric_grades:
            summary['average_grade'] = round(sum(numeric_grades) / len(numeric_grades), 2)
        
        student_data['summary'] = summary
        
        return jsonify({
            'status': 'success',
            'message': f'Student data retrieved successfully for {student.get("name")}',
            'data': student_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving student data: {str(e)}',
            'data': None
        }), 500 