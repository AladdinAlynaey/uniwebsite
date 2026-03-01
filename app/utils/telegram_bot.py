import os
import requests
import logging
import json
from app.models.telegram_user import TelegramUser
from app.models.student import Student
from app.models.news import News
from app.models.lecture import Lecture

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram bot token (in a real app, use environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8235295033:AAHccW498NXnH0NCMaBcgUfsvHR0N5FkahM')
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def set_telegram_token(token, username=None):
    """Set the Telegram bot token"""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_API_BASE
    TELEGRAM_BOT_TOKEN = token
    TELEGRAM_API_BASE = f"https://api.telegram.org/bot{token}"
    
    # Save the token to a config file
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'telegram_config.json')
    
    config_data = {'token': token}
    
    # Save username if provided
    if username:
        config_data['username'] = username
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    return True

def load_telegram_token():
    """Load the Telegram bot token from config file"""
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    config_path = os.path.join(config_dir, 'telegram_config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            set_telegram_token(config.get('token'), config.get('username'))
            return config.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def send_message(chat_id, text):
    """Send a message to a specific chat"""
    try:
        url = f"{TELEGRAM_API_BASE}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return None

def broadcast_message(message):
    """Send a message to all registered users"""
    chat_ids = TelegramUser.get_all_chat_ids()
    results = []
    for chat_id in chat_ids:
        result = send_message(chat_id, message)
        results.append(result)
    return results

def notify_new_lecture(lecture):
    """Notify all users about a new lecture"""
    subject_name = lecture.get('subject_name', 'Unknown Subject') if isinstance(lecture, dict) else getattr(lecture, 'subject_name', 'Unknown Subject')
    week = lecture.get('week', 'Unknown Week') if isinstance(lecture, dict) else getattr(lecture, 'week', 'Unknown Week')
    lecture_type = lecture.get('lecture_type', 'Unknown Type') if isinstance(lecture, dict) else getattr(lecture, 'lecture_type', 'Unknown Type')
    file_name = lecture.get('file_name', 'Unknown File') if isinstance(lecture, dict) else getattr(lecture, 'file_name', 'Unknown File')
    
    message = f"""<b>🎓 New Lecture Available!</b>
    
<b>Subject:</b> {subject_name}
<b>Week:</b> {week}
<b>Type:</b> {lecture_type}
<b>File:</b> {file_name}

Log in to the platform to access this lecture material."""
    
    return broadcast_message(message)

def notify_new_news(news_item):
    """Notify all users about a new news item"""
    title = news_item.get('title', 'Untitled') if isinstance(news_item, dict) else getattr(news_item, 'title', 'Untitled')
    content = news_item.get('content', '') if isinstance(news_item, dict) else getattr(news_item, 'content', '')
    content_preview = content[:100] + '...' if len(content) > 100 else content
    
    message = f"""<b>📢 New Announcement!</b>
    
<b>{title}</b>

{content_preview}

Log in to the platform to read the full announcement."""
    
    return broadcast_message(message)

def handle_start_command(chat_id, text=None):
    """Handle /start command from a Telegram user"""
    # Check if there's a token in the message
    token = None
    if text and len(text.split()) > 1:
        token = text.split()[1].strip()
    
    if token:
        # Verify the token
        student = Student.find_by_token(token)
        if student:
            # Link chat_id to token
            TelegramUser.link_chat_to_token(chat_id, token)
            
            message = f"""<b>Welcome, {student.get('name')}!</b>

You have successfully registered for notifications from University AI Batch Educational Platform.

You will now receive notifications about:
- New lectures
- News and announcements

Available commands:
/news - Get the latest news
/lectures - Get the latest lectures
/help - Show this help message"""
            
            return send_message(chat_id, message)
        else:
            return send_message(chat_id, "Invalid token. Please check your token and try again.")
    else:
        message = """<b>Welcome to University AI Batch Educational Platform!</b>

To register for notifications, please use the command:
/start YOUR_TOKEN

You can find your token in your student profile page.

If you don't have a token, please contact your administrator."""
        
        return send_message(chat_id, message)

def handle_help_command(chat_id):
    """Handle /help command from a Telegram user"""
    message = """<b>University AI Batch Bot Help</b>

Available commands:
/start YOUR_TOKEN - Register with your student token
/news - Get the latest news
/lectures - Get the latest lectures
/help - Show this help message"""
    
    return send_message(chat_id, message)

def handle_news_command(chat_id):
    """Handle /news command from a Telegram user"""
    latest_news = News.get_latest_news(5)
    
    if not latest_news:
        return send_message(chat_id, "No news available at the moment.")
    
    message = "<b>📢 Latest News</b>\n\n"
    for i, news in enumerate(latest_news, 1):
        title = news.get('title', 'Untitled') if isinstance(news, dict) else getattr(news, 'title', 'Untitled')
        date = news.get('created_at', 'Unknown date') if isinstance(news, dict) else getattr(news, 'created_at', 'Unknown date')
        message += f"{i}. <b>{title}</b> ({date[:10]})\n"
    
    message += "\nLog in to the platform for more details."
    return send_message(chat_id, message)

def handle_lectures_command(chat_id):
    """Handle /lectures command from a Telegram user"""
    latest_lectures = Lecture.get_latest_lectures(5)
    
    if not latest_lectures:
        return send_message(chat_id, "No lectures available at the moment.")
    
    message = "<b>🎓 Latest Lectures</b>\n\n"
    for i, lecture in enumerate(latest_lectures, 1):
        subject = lecture.get('subject_name', 'Unknown Subject') if isinstance(lecture, dict) else getattr(lecture, 'subject_name', 'Unknown Subject')
        week = lecture.get('week', 'Unknown Week') if isinstance(lecture, dict) else getattr(lecture, 'week', 'Unknown Week')
        lecture_type = lecture.get('lecture_type', 'Unknown Type') if isinstance(lecture, dict) else getattr(lecture, 'lecture_type', 'Unknown Type')
        message += f"{i}. <b>{subject}</b> - Week {week} ({lecture_type})\n"
    
    message += "\nLog in to the platform to access lecture materials."
    return send_message(chat_id, message)

def handle_webhook(data):
    """Handle incoming webhook data from Telegram"""
    try:
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return None
        
        # Handle commands
        if text.startswith('/start'):
            return handle_start_command(chat_id, text)
        elif text.startswith('/help'):
            return handle_help_command(chat_id)
        elif text.startswith('/news'):
            return handle_news_command(chat_id)
        elif text.startswith('/lectures'):
            return handle_lectures_command(chat_id)
        else:
            # Default response
            return send_message(chat_id, "I don't understand that command. Try /help for a list of commands.")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return None

# Load token on module import
load_telegram_token()