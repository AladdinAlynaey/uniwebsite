"""
Multi-Provider AI Module
Supports: Gemini, OpenRouter, and Groq
"""

import os
import json
import requests
from app.models.subject import Subject
from app.models.news import News
from app.models.student import Student

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables only")

# ============================================
# AI Provider Configuration
# ============================================

# Active AI provider (can be changed via admin settings)
# Options: 'gemini', 'openrouter', 'groq'
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini')

# Provider-specific settings file
AI_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ai_settings.json')

def load_ai_settings():
    """Load AI settings from file"""
    try:
        if os.path.exists(AI_SETTINGS_FILE):
            with open(AI_SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading AI settings: {e}")
    return {
        'provider': 'gemini',
        'gemini_model': 'gemini-2.0-flash',
        'openrouter_model': 'google/gemini-2.0-flash-exp:free',
        'groq_model': 'llama-3.3-70b-versatile'
    }

def save_ai_settings(settings):
    """Save AI settings to file"""
    try:
        os.makedirs(os.path.dirname(AI_SETTINGS_FILE), exist_ok=True)
        with open(AI_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving AI settings: {e}")
        return False

def get_active_provider():
    """Get the currently active AI provider"""
    settings = load_ai_settings()
    return settings.get('provider', 'gemini')

def set_active_provider(provider):
    """Set the active AI provider"""
    settings = load_ai_settings()
    settings['provider'] = provider
    return save_ai_settings(settings)

# ============================================
# Gemini Configuration
# ============================================

GEMINI_MODEL_NAME = os.environ.get('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
GEMINI_FALLBACK_MODELS = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

# Multiple Gemini API keys for fallback
GEMINI_API_KEYS = []
for i in range(1, 11):
    key = os.environ.get(f'GEMINI_API_KEY_{i}', '')
    if key and not key.startswith('your_'):
        GEMINI_API_KEYS.append(key)

if not GEMINI_API_KEYS:
    single_key = os.environ.get('GEMINI_API_KEY', '')
    if single_key and not single_key.startswith('your_'):
        GEMINI_API_KEYS.append(single_key)

print(f"Loaded {len(GEMINI_API_KEYS)} Gemini API key(s)")

# ============================================
# OpenRouter Configuration
# ============================================

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'google/gemini-2.0-flash-exp:free')
# Fallback models for OpenRouter - prioritize smarter models
OPENROUTER_FALLBACK_MODELS = [
    'google/gemini-2.0-flash-exp:free',      # Best free option
    'meta-llama/llama-3.3-70b-instruct:free', # Large, smart model
    'qwen/qwen-2.5-72b-instruct:free',        # Very capable
    'mistralai/mistral-large-2411:free',      # Strong model
    'deepseek/deepseek-chat:free',            # Good for reasoning
    'meta-llama/llama-3.2-3b-instruct:free',  # Fast fallback
]

if OPENROUTER_API_KEY:
    print("OpenRouter API key loaded")
else:
    print("No OpenRouter API key found")

# ============================================
# Groq Configuration
# ============================================

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
# Fallback models for Groq
GROQ_FALLBACK_MODELS = [
    'llama-3.3-70b-versatile',
    'llama-3.1-70b-versatile',
    'llama-3.1-8b-instant',
    'mixtral-8x7b-32768'
]

if GROQ_API_KEY:
    print("Groq API key loaded")
else:
    print("No Groq API key found")

# ============================================
# Gemini API Setup
# ============================================

genai = None
USING_MOCK = True
current_api_key_index = 0

try:
    import google.generativeai as genai_module
    if hasattr(genai_module, 'configure') and hasattr(genai_module, 'GenerativeModel'):
        genai = genai_module
        if GEMINI_API_KEYS:
            configure_func = getattr(genai, 'configure')
            configure_func(api_key=GEMINI_API_KEYS[current_api_key_index])
            USING_MOCK = False
            print(f"Gemini API initialized with key #1")
except Exception as e:
    print(f"Warning: Could not initialize Gemini: {e}")

# ============================================
# Context Data Function
# ============================================

def get_context_data(student_id=None):
    """Get context data from JSON files for RAG"""
    from app.models.grade import Grade
    from app.models.attendance import Attendance
    
    context = {
        'subjects': Subject.load_all(),
        'news': News.get_latest_news(20)
    }
    
    if student_id:
        # First try to find by token (from session)
        student = Student.find_by_token(student_id)
        
        # If not found by token, try by ID
        if not student:
            student = Student.find_by_id(student_id)
        
        if student:
            print(f"Found student: {student.get('name')} (ID: {student.get('id')})")
            
            actual_student_id = student.get('id')
            
            student_data = {
                'name': student.get('name'),
                'student_id': student.get('student_id'),
                'email': student.get('email')
            }
            
            # Get grades - try multiple ID fields
            all_grades = Grade.load_all()
            student_grades = [g for g in all_grades if g.get('student_id') == actual_student_id or g.get('student_id') == student.get('student_id')]
            student_data['grades'] = student_grades
            print(f"Found {len(student_grades)} grades for student")
            
            # Get attendance - try multiple matching methods
            all_attendance = Attendance.load_all()
            student_attendance = []
            for a in all_attendance:
                # Match by various ID fields
                if (a.get('student_id') == actual_student_id or 
                    a.get('student_id') == student.get('student_id') or
                    a.get('student_name') == student.get('name')):
                    student_attendance.append(a)
            student_data['attendance'] = student_attendance
            print(f"Found {len(student_attendance)} attendance records for student")
            
            # Get assignments
            from app.utils.assignments import get_student_submissions, get_all_assignments
            student_assignments = get_student_submissions(actual_student_id)
            all_assignments = get_all_assignments()
            student_data['assignments'] = student_assignments
            student_data['available_assignments'] = all_assignments
            
            context['student_data'] = student_data
        else:
            print(f"Student not found with token/id: {student_id}")
    
    return context

# ============================================
# System Prompt Builder
# ============================================

def build_system_prompt(student_id=None):
    """Build an enhanced system prompt with rich context"""
    context = get_context_data(student_id)
    
    student_greeting = ""
    student_name = "Student"
    if student_id and 'student_data' in context:
        student_name = context['student_data'].get('name', 'Student')
        student_greeting = f"Hello {student_name}! "
    
    # Build subject information in a more readable format
    subjects_info = ""
    for subj in context.get('subjects', []):
        subjects_info += f"""
- **{subj.get('name')}** (Code: `{subj.get('code', 'N/A')}`)
  - Semester: {subj.get('semester', 'N/A')}
  - Description: {subj.get('description', 'No description')}
  - Total Lectures: {subj.get('lectures_count', 0)}
"""
    
    # Build news summary
    news_info = ""
    for news in context.get('news', [])[:5]:
        news_info += f"- [{news.get('date', 'N/A')}] **{news.get('title')}**: {news.get('content', '')[:100]}...\n"
    
    # Build student-specific context
    student_context = ""
    if 'student_data' in context:
        sd = context['student_data']
        student_context = f"""
## 📚 CURRENT STUDENT (This is the student asking questions)
- **Name**: {sd.get('name')}
- **Student ID**: {sd.get('student_id')}
- **Email**: {sd.get('email')}
"""
        
        # Add grades summary
        grades = sd.get('grades', [])
        if grades:
            student_context += "\n### 📊 Grades:\n"
            for g in grades:
                student_context += f"- {g.get('subject_name', 'Unknown')}: **{g.get('grade', 'N/A')}** ({g.get('grade_type', 'exam')})\n"
        else:
            student_context += "\n### 📊 Grades: No grades recorded yet.\n"
        
        # Add detailed attendance per subject
        attendance = sd.get('attendance', [])
        if attendance:
            # Get subjects for name lookup
            subjects = context.get('subjects', [])
            subject_map = {s.get('id'): s.get('name', 'Unknown') for s in subjects}
            
            # Group by subject
            attendance_by_subject = {}
            for a in attendance:
                subject_id = a.get('subject_id', 'unknown')
                subj_name = subject_map.get(subject_id, f"Subject ({subject_id[:8]}...)")
                
                if subj_name not in attendance_by_subject:
                    attendance_by_subject[subj_name] = {'present': 0, 'absent': 0, 'total': 0, 'lectures': []}
                attendance_by_subject[subj_name]['total'] += 1
                
                # Check is_present (boolean) instead of status
                if a.get('is_present', False):
                    attendance_by_subject[subj_name]['present'] += 1
                else:
                    attendance_by_subject[subj_name]['absent'] += 1
                    
                attendance_by_subject[subj_name]['lectures'].append({
                    'lecture': a.get('lecture_number', 'N/A'),
                    'present': a.get('is_present', False),
                    'excused': a.get('is_excused', False)
                })
            
            total_all = len(attendance)
            present_all = sum(1 for a in attendance if a.get('is_present', False))
            student_context += f"\n### 📅 Attendance Summary:\n"
            student_context += f"**Overall: {present_all}/{total_all} sessions ({round(present_all/total_all*100, 1) if total_all > 0 else 0}% present)**\n\n"
            
            student_context += "**By Subject:**\n"
            for subj, data in attendance_by_subject.items():
                pct = round(data['present']/data['total']*100, 1) if data['total'] > 0 else 0
                student_context += f"- **{subj}**: {data['present']}/{data['total']} present ({pct}%), {data['absent']} absent\n"
        else:
            student_context += "\n### 📅 Attendance: No attendance records yet.\n"
        
        # Add assignments
        assignments = sd.get('assignments', {})
        available = sd.get('available_assignments', {})
        
        hw_count = len(available.get('weekly_homework', []))
        proj_count = len(available.get('final_projects', []))
        pres_count = len(available.get('presentations', []))
        
        if hw_count + proj_count + pres_count > 0:
            student_context += f"\n### 📝 Assignments:\n"
            student_context += f"- Weekly Homework: {hw_count} available\n"
            student_context += f"- Final Projects: {proj_count} available\n"
            student_context += f"- Presentations: {pres_count} available\n"
    
    system_prompt = f"""You are **UniBot**, an advanced AI assistant for the University AI Batch educational platform. You are intelligent, helpful, and friendly. You communicate in a warm, professional manner while being concise and informative.

# 🎓 YOUR CAPABILITIES
You can help students with:
1. **Course Information** - Details about subjects, lectures, syllabi
2. **Grades & Performance** - Academic progress, grades analysis
3. **Attendance Tracking** - Attendance records and statistics
4. **Assignments** - Homework, projects, presentations info
5. **News & Announcements** - Latest university updates
6. **General Guidance** - Academic advice and support

# 📖 AVAILABLE SUBJECTS
{subjects_info if subjects_info else "No subjects currently available."}

# 📰 LATEST NEWS & ANNOUNCEMENTS
{news_info if news_info else "No recent news."}

{student_context}

# 🎯 YOUR PERSONALITY & BEHAVIOR
1. **Be Conversational**: Respond naturally, like a helpful friend who happens to know everything about the university.
2. **Be Specific**: When asked about grades, attendance, or assignments, provide exact numbers and details from the data.
3. **Be Proactive**: Suggest related information that might be helpful.
4. **Be Encouraging**: Motivate students and celebrate their achievements.
5. **Use Emojis Sparingly**: Add relevant emojis to make responses friendly (📚 for subjects, ✅ for success, etc.)
6. **Format Beautifully**: Use Markdown for clear, readable responses:
   - **Bold** for emphasis
   - `Code` for course codes
   - Bullet points for lists
   - Tables when comparing data
7. **Language Flexibility**: If the user writes in Arabic or any other language, respond in that same language naturally.

# ⚠️ IMPORTANT RULES
1. Only answer questions based on the data provided above.
2. If information is not available, politely say so and suggest what you CAN help with.
3. Never make up grades, attendance, or other academic data.
4. For personal questions or off-topic queries, politely redirect to academic topics.
5. If asked about the developer/creator: "This platform was developed by **AI Engineer Alaadin** (📧 alaadinessam2016@gmail.com)."

# 💡 EXAMPLE RESPONSES
- When greeted: "Hey there! 👋 How can I help you with your studies today?"
- For grades: "Looking at your records, you scored **85** in Neural Networks! That's great work! 🎉"
- For subjects: "We have **5 subjects** this semester. Would you like details on a specific one?"
- For unknown info: "I don't have that specific information, but I can help you with your grades, attendance, or course details!"

Now respond to the student's query helpfully and naturally.
"""
    return system_prompt, student_greeting

# ============================================
# OpenRouter API Call
# ============================================

def call_openrouter(query, system_prompt, chat_history=None, model=None):
    """Call OpenRouter API with conversation history"""
    if not OPENROUTER_API_KEY:
        raise Exception("OpenRouter API key not configured")
    
    if chat_history is None:
        chat_history = []
    
    models_to_try = [model] if model else [OPENROUTER_MODEL] + OPENROUTER_FALLBACK_MODELS
    
    for try_model in models_to_try:
        try:
            print(f"Trying OpenRouter with model: {try_model}")
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://alaadinuniwebsite.duckdns.org",
                "X-Title": "University AI Batch"
            }
            
            # Build messages with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in chat_history:
                messages.append({"role": "user", "content": msg.get('query', '')})
                messages.append({"role": "assistant", "content": msg.get('response', '')})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            data = {
                "model": try_model,
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.6,
                "top_p": 0.95
            }
            
            response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 429:
                print(f"Rate limited on {try_model}, trying next...")
                continue
            else:
                print(f"OpenRouter error ({response.status_code}): {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"OpenRouter error with {try_model}: {str(e)[:200]}")
            continue
    
    raise Exception("All OpenRouter models exhausted")

# ============================================
# Groq API Call
# ============================================

def call_groq(query, system_prompt, chat_history=None, model=None):
    """Call Groq API with conversation history"""
    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")
    
    if chat_history is None:
        chat_history = []
    
    models_to_try = [model] if model else [GROQ_MODEL] + GROQ_FALLBACK_MODELS
    
    for try_model in models_to_try:
        try:
            print(f"Trying Groq with model: {try_model}")
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Build messages with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in chat_history:
                messages.append({"role": "user", "content": msg.get('query', '')})
                messages.append({"role": "assistant", "content": msg.get('response', '')})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            data = {
                "model": try_model,
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.6,
                "top_p": 0.95
            }
            
            response = requests.post(GROQ_BASE_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 429:
                print(f"Rate limited on {try_model}, trying next...")
                continue
            else:
                print(f"Groq error ({response.status_code}): {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"Groq error with {try_model}: {str(e)[:200]}")
            continue
    
    raise Exception("All Groq models exhausted")

# ============================================
# Gemini API Call
# ============================================

def call_gemini(query, system_prompt, chat_history=None):
    """Call Gemini API with fallback and conversation history"""
    global current_api_key_index
    
    if chat_history is None:
        chat_history = []
    
    if not GEMINI_API_KEYS:
        raise Exception("No Gemini API keys configured")
    
    all_models = [GEMINI_MODEL_NAME] + GEMINI_FALLBACK_MODELS
    
    # Build Gemini history format
    gemini_history = []
    for msg in chat_history:
        gemini_history.append({
            "role": "user",
            "parts": [msg.get('query', '')]
        })
        gemini_history.append({
            "role": "model",
            "parts": [msg.get('response', '')]
        })
    
    for model_name in all_models:
        for attempt in range(len(GEMINI_API_KEYS)):
            try:
                import google.generativeai as genai_module
                configure_func = getattr(genai_module, 'configure')
                configure_func(api_key=GEMINI_API_KEYS[current_api_key_index])
                
                print(f"Trying Gemini model: {model_name}, key #{current_api_key_index + 1}")
                
                GenerativeModel = getattr(genai_module, 'GenerativeModel')
                model = GenerativeModel(model_name)
                
                # Start chat with history
                chat = model.start_chat(history=gemini_history)
                
                # Send message with system prompt on first message or just query
                if len(gemini_history) == 0:
                    response = chat.send_message(f"{system_prompt}\n\nUser query: {query}")
                else:
                    response = chat.send_message(query)
                    
                print(f"Gemini success with {model_name}")
                return response.text
                
            except Exception as e:
                error_str = str(e)
                print(f"Gemini error with {model_name}, key #{current_api_key_index + 1}: {error_str[:100]}")
                
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    current_api_key_index = (current_api_key_index + 1) % len(GEMINI_API_KEYS)
                    continue
                else:
                    break  # Non-quota error, try next model
    
    raise Exception("All Gemini models and keys exhausted")

# ============================================
# Main Generate Response Function
# ============================================

def generate_response(query, student_id=None, chat_history=None):
    """Generate AI response using the active provider with fallbacks and conversation memory"""
    
    if chat_history is None:
        chat_history = []
    
    system_prompt, student_greeting = build_system_prompt(student_id)
    active_provider = get_active_provider()
    
    print(f"Active AI provider: {active_provider}")
    print(f"Chat history length: {len(chat_history)} messages")
    
    # Define provider order based on active provider
    if active_provider == 'gemini':
        providers = ['gemini', 'openrouter', 'groq']
    elif active_provider == 'openrouter':
        providers = ['openrouter', 'groq', 'gemini']
    elif active_provider == 'groq':
        providers = ['groq', 'openrouter', 'gemini']
    else:
        providers = ['gemini', 'openrouter', 'groq']
    
    last_error = None
    
    for provider in providers:
        try:
            if provider == 'gemini' and GEMINI_API_KEYS:
                print(f"Trying Gemini...")
                response = call_gemini(query, system_prompt, chat_history)
                return f"{student_greeting}{response}" if student_greeting else response
                
            elif provider == 'openrouter' and OPENROUTER_API_KEY:
                print(f"Trying OpenRouter...")
                response = call_openrouter(query, system_prompt, chat_history)
                return f"{student_greeting}{response}" if student_greeting else response
                
            elif provider == 'groq' and GROQ_API_KEY:
                print(f"Trying Groq...")
                response = call_groq(query, system_prompt, chat_history)
                return f"{student_greeting}{response}" if student_greeting else response
                
        except Exception as e:
            last_error = str(e)
            print(f"Provider {provider} failed: {last_error[:100]}")
            continue
    
    # All providers failed
    error_msg = "I'm currently experiencing high demand across all AI services. Please try again in a few minutes."
    print(f"All providers failed. Last error: {last_error}")
    return f"{student_greeting}{error_msg}" if student_greeting else error_msg

# ============================================
# Available Providers Info
# ============================================

def get_available_providers():
    """Get list of configured providers with their status"""
    return {
        'gemini': {
            'name': 'Google Gemini',
            'configured': len(GEMINI_API_KEYS) > 0,
            'api_keys_count': len(GEMINI_API_KEYS),
            'models': [GEMINI_MODEL_NAME] + GEMINI_FALLBACK_MODELS
        },
        'openrouter': {
            'name': 'OpenRouter',
            'configured': bool(OPENROUTER_API_KEY),
            'models': [OPENROUTER_MODEL] + OPENROUTER_FALLBACK_MODELS
        },
        'groq': {
            'name': 'Groq',
            'configured': bool(GROQ_API_KEY),
            'models': [GROQ_MODEL] + GROQ_FALLBACK_MODELS
        }
    }

# ============================================
# Test Provider Function
# ============================================

def test_provider(provider):
    """Test if a provider's API is working
    
    Returns:
        dict: {'success': bool, 'message': str, 'response': str (if success)}
    """
    test_query = "Say 'API test successful' in exactly those words."
    
    if provider == 'gemini':
        if not GEMINI_API_KEYS:
            return {'success': False, 'message': 'No Gemini API keys configured. Add GEMINI_API_KEY_1 to your .env file.'}
        
        try:
            import google.generativeai as genai_module
            configure_func = getattr(genai_module, 'configure')
            configure_func(api_key=GEMINI_API_KEYS[0])
            
            GenerativeModel = getattr(genai_module, 'GenerativeModel')
            model = GenerativeModel(GEMINI_MODEL_NAME)
            chat = model.start_chat(history=[])
            response = chat.send_message(test_query)
            
            return {
                'success': True, 
                'message': 'Gemini API is working!',
                'response': response.text[:100]
            }
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                return {'success': False, 'message': 'Gemini quota exceeded. Try again later or use a different provider.'}
            elif 'api_key' in error_str.lower() or 'invalid' in error_str.lower():
                return {'success': False, 'message': 'Invalid Gemini API key. Please check your configuration.'}
            else:
                return {'success': False, 'message': f'Gemini error: {error_str[:100]}'}
    
    elif provider == 'openrouter':
        if not OPENROUTER_API_KEY:
            return {'success': False, 'message': 'No OpenRouter API key configured. Add OPENROUTER_API_KEY to your .env file.'}
        
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://alaadinuniwebsite.duckdns.org",
                "X-Title": "University AI Batch"
            }
            
            data = {
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": test_query}],
                "max_tokens": 50
            }
            
            response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'OpenRouter API is working!',
                    'response': result['choices'][0]['message']['content'][:100]
                }
            elif response.status_code == 401:
                return {'success': False, 'message': 'Invalid OpenRouter API key. Please check your configuration.'}
            elif response.status_code == 429:
                return {'success': False, 'message': 'OpenRouter rate limited. Try again in a moment.'}
            else:
                return {'success': False, 'message': f'OpenRouter error ({response.status_code}): {response.text[:100]}'}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'OpenRouter request timed out. Try again.'}
        except Exception as e:
            return {'success': False, 'message': f'OpenRouter error: {str(e)[:100]}'}
    
    elif provider == 'groq':
        if not GROQ_API_KEY:
            return {'success': False, 'message': 'No Groq API key configured. Add GROQ_API_KEY to your .env file.'}
        
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": test_query}],
                "max_tokens": 50
            }
            
            response = requests.post(GROQ_BASE_URL, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'Groq API is working!',
                    'response': result['choices'][0]['message']['content'][:100]
                }
            elif response.status_code == 401:
                return {'success': False, 'message': 'Invalid Groq API key. Please check your configuration.'}
            elif response.status_code == 429:
                return {'success': False, 'message': 'Groq rate limited. Try again in a moment.'}
            else:
                return {'success': False, 'message': f'Groq error ({response.status_code}): {response.text[:100]}'}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Groq request timed out. Try again.'}
        except Exception as e:
            return {'success': False, 'message': f'Groq error: {str(e)[:100]}'}
    
    else:
        return {'success': False, 'message': f'Unknown provider: {provider}'}