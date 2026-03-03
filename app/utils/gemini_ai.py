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

def get_context_data(student_id=None, user=None):
    """Get context data for RAG — role-aware.
    
    Args:
        student_id: Legacy student token/id  
        user: Full user dict from session (preferred)
    """
    from app.models.grade import Grade
    from app.models.attendance import Attendance
    from app.models.user import User
    
    context = {
        'subjects': Subject.load_all(),
        'news': News.get_latest_news(20)
    }
    
    # Determine role from user dict
    role = None
    if user:
        role = user.get('role')
        context['user_name'] = user.get('name', 'User')
        context['user_role'] = role
    
    # ---- SUPER ADMIN context ----
    if role == 'super_admin':
        from app.models.faculty import Faculty
        from app.models.batch import Batch
        from app.models.department import Department
        context['admin_data'] = {
            'faculties': len(Faculty.load_all()),
            'departments': len(Department.load_all()),
            'batches': len(Batch.load_all()),
            'total_users': len(User.load_all()),
            'total_subjects': len(context['subjects']),
        }
    
    # ---- FACULTY HEAD context ----
    elif role == 'faculty_head' and user.get('faculty_id'):
        from app.models.faculty import Faculty
        from app.models.batch import Batch
        from app.models.department import Department
        from app.models.teacher_subject import TeacherSubject
        fac = Faculty.find_by_id(user['faculty_id'])
        depts = Department.get_by_faculty(user['faculty_id'])
        batches = Batch.get_by_faculty(user['faculty_id'])
        teachers = [u for u in User.get_by_faculty(user['faculty_id']) if u.get('role') == 'teacher']
        context['faculty_data'] = {
            'faculty_name': fac.get('name', '') if fac else '',
            'departments': [d.get('name') for d in depts],
            'batches': [b.get('name') for b in batches],
            'teacher_count': len(teachers),
            'teacher_names': [t.get('name') for t in teachers],
        }
    
    # ---- TEACHER context ----
    elif role == 'teacher':
        from app.models.teacher_subject import TeacherSubject
        links = TeacherSubject.get_by_teacher(user['id'])
        subject_ids = [l.get('subject_id') for l in links]
        my_subjects = [s for s in context['subjects'] if s.get('id') in subject_ids]
        context['teacher_data'] = {
            'name': user.get('name'),
            'subjects': [{'name': s.get('name'), 'code': s.get('code')} for s in my_subjects],
            'subject_count': len(my_subjects),
        }
    
    # ---- BATCH REP context (admin + own student data) ----
    elif role == 'batch_rep':
        from app.models.batch import Batch
        batch = Batch.find_by_id(user.get('batch_id')) if user.get('batch_id') else None
        context['rep_data'] = {
            'batch_name': batch.get('name', '') if batch else '',
        }
        # Also include own student data
        _add_student_data(context, user['id'], user, Grade, Attendance)
    
    # ---- STUDENT context ----
    elif role == 'student' or student_id:
        actual_user = user
        if not actual_user and student_id:
            actual_user = Student.find_by_token(student_id)
            if not actual_user:
                actual_user = Student.find_by_id(student_id)
        if actual_user:
            _add_student_data(context, actual_user.get('id'), actual_user, Grade, Attendance)
    
    return context


def _add_student_data(context, student_id, student, Grade, Attendance):
    """Helper to add student grades/attendance/assignments to context."""
    student_data = {
        'name': student.get('name'),
        'student_id': student.get('student_id', student.get('id')),
        'email': student.get('email')
    }
    
    # Grades
    all_grades = Grade.load_all()
    student_grades = [g for g in all_grades if g.get('student_id') == student_id]
    student_data['grades'] = student_grades
    
    # Attendance
    all_attendance = Attendance.load_all()
    student_attendance = [a for a in all_attendance 
                         if a.get('student_id') == student_id or 
                            a.get('student_name') == student.get('name')]
    student_data['attendance'] = student_attendance
    
    # Assignments
    try:
        from app.utils.assignments import get_student_submissions, get_all_assignments
        student_data['assignments'] = get_student_submissions(student_id)
        student_data['available_assignments'] = get_all_assignments()
    except Exception:
        student_data['assignments'] = {}
        student_data['available_assignments'] = {}
    
    context['student_data'] = student_data

# ============================================
# System Prompt Builder
# ============================================

def build_system_prompt(student_id=None, user=None):
    """Build an enhanced system prompt with rich, role-aware context."""
    context = get_context_data(student_id, user)
    
    greeting = ""
    user_name = "User"
    role = context.get('user_role', 'student')
    
    if user:
        user_name = user.get('name', 'User')
        greeting = f"Hello {user_name}! "
    elif student_id and 'student_data' in context:
        user_name = context['student_data'].get('name', 'Student')
        greeting = f"Hello {user_name}! "
    
    # Build subject information
    subjects_info = ""
    for subj in context.get('subjects', []):
        subjects_info += f"\n- **{subj.get('name')}** (Code: `{subj.get('code', 'N/A')}`) — Semester: {subj.get('semester', 'N/A')}\n"
    
    # Build news summary
    news_info = ""
    for news in context.get('news', [])[:5]:
        source = f" [{news.get('faculty_name', '')}]" if news.get('faculty_name') else ""
        news_info += f"- **{news.get('title')}**{source}: {news.get('content', '')[:100]}...\n"
    
    # ---- Role-specific context ----
    role_context = ""
    
    if 'admin_data' in context:
        ad = context['admin_data']
        role_context = f"""## 🔑 CURRENT USER: Super Admin
- **Name**: {user_name}
- **System Stats**: {ad['faculties']} faculties, {ad['departments']} departments, {ad['batches']} batches, {ad['total_users']} users, {ad['total_subjects']} subjects
"""
    
    elif 'faculty_data' in context:
        fd = context['faculty_data']
        role_context = f"""## 🏛️ CURRENT USER: Faculty Head
- **Name**: {user_name}
- **Faculty**: {fd['faculty_name']}
- **Departments**: {', '.join(fd['departments'])}
- **Batches**: {', '.join(fd['batches'])}
- **Teachers** ({fd['teacher_count']}): {', '.join(fd['teacher_names'])}
"""
    
    elif 'teacher_data' in context:
        td = context['teacher_data']
        subj_list = ', '.join([f"{s['name']} ({s['code']})" for s in td['subjects']]) if td['subjects'] else 'None assigned'
        role_context = f"""## 👨‍🏫 CURRENT USER: Teacher
- **Name**: {td['name']}
- **Assigned Subjects** ({td['subject_count']}): {subj_list}
"""
    
    elif 'rep_data' in context:
        rd = context['rep_data']
        role_context = f"""## ⭐ CURRENT USER: Batch Representative
- **Name**: {user_name}
- **Managing Batch**: {rd['batch_name']}
- **Note**: This user is both a batch admin AND a student.
"""
    
    # Add student data for student/batch_rep
    if 'student_data' in context:
        sd = context['student_data']
        if not role_context:  # Pure student
            role_context = f"""## 📚 CURRENT USER: Student
- **Name**: {sd.get('name')}
- **Email**: {sd.get('email')}
"""
        
        # Grades
        grades = sd.get('grades', [])
        if grades:
            role_context += "\n### 📊 Grades:\n"
            for g in grades:
                role_context += f"- {g.get('subject_name', 'Unknown')}: **{g.get('grade', 'N/A')}** ({g.get('grade_type', 'exam')})\n"
        else:
            role_context += "\n### 📊 Grades: No grades recorded yet.\n"
        
        # Attendance summary
        attendance = sd.get('attendance', [])
        if attendance:
            subjects = context.get('subjects', [])
            subject_map = {s.get('id'): s.get('name', 'Unknown') for s in subjects}
            attendance_by_subject = {}
            for a in attendance:
                subj_name = subject_map.get(a.get('subject_id', ''), 'Unknown')
                if subj_name not in attendance_by_subject:
                    attendance_by_subject[subj_name] = {'present': 0, 'total': 0}
                attendance_by_subject[subj_name]['total'] += 1
                if a.get('is_present', False):
                    attendance_by_subject[subj_name]['present'] += 1
            
            total_all = len(attendance)
            present_all = sum(1 for a in attendance if a.get('is_present', False))
            role_context += f"\n### 📅 Attendance: {present_all}/{total_all} overall\n"
            for subj, data in attendance_by_subject.items():
                pct = round(data['present']/data['total']*100, 1) if data['total'] > 0 else 0
                role_context += f"- {subj}: {data['present']}/{data['total']} ({pct}%)\n"
        else:
            role_context += "\n### 📅 Attendance: No records yet.\n"
    
    # Map role to capability description
    role_caps = {
        'super_admin': 'system administration, all faculties, all users, all data',
        'faculty_head': 'faculty management, departments, batches, and teachers in your faculty',
        'teacher': 'your assigned subjects, lectures, grades, and attendance',
        'batch_rep': 'batch management AND your own student grades/attendance',
        'student': 'your grades, attendance, lectures, and assignments',
    }
    caps = role_caps.get(role, 'general university information')
    
    system_prompt = f"""You are **UniBot**, the AI assistant for University AI Batch. You are intelligent, helpful, and friendly.

# 🎓 CONTEXT
The user is a **{role or 'visitor'}**. You can help with: {caps}.

# 📖 SUBJECTS
{subjects_info or 'No subjects available.'}

# 📰 NEWS
{news_info or 'No recent news.'}

{role_context}

# 🎯 RULES
1. Only answer from the data above — never invent data.
2. Be concise but specific with numbers and details.
3. Use Markdown formatting and relevant emojis.
4. Match the user's language (Arabic/English).
5. Redirect off-topic questions politely.
6. Creator: **AI Engineer Alaadin** (📧 alaadinessam2016@gmail.com)

Respond helpfully and naturally.
"""
    return system_prompt, greeting

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

def generate_response(query, student_id=None, chat_history=None, user=None):
    """Generate AI response using the active provider with fallbacks and conversation memory"""
    
    if chat_history is None:
        chat_history = []
    
    system_prompt, greeting = build_system_prompt(student_id, user=user)
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
                return f"{greeting}{response}" if greeting else response
                
            elif provider == 'openrouter' and OPENROUTER_API_KEY:
                print(f"Trying OpenRouter...")
                response = call_openrouter(query, system_prompt, chat_history)
                return f"{greeting}{response}" if greeting else response
                
            elif provider == 'groq' and GROQ_API_KEY:
                print(f"Trying Groq...")
                response = call_groq(query, system_prompt, chat_history)
                return f"{greeting}{response}" if greeting else response
                
        except Exception as e:
            last_error = str(e)
            print(f"Provider {provider} failed: {last_error[:100]}")
            continue
    
    # All providers failed
    error_msg = "I'm currently experiencing high demand across all AI services. Please try again in a few minutes."
    print(f"All providers failed. Last error: {last_error}")
    return f"{greeting}{error_msg}" if greeting else error_msg

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