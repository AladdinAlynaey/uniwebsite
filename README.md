<p align="center">
  <img src="app/static/img/favicon.png" alt="UniWebsite Logo" width="120" height="120">
</p>

<h1 align="center">🎓 University AI Batch — Educational Platform</h1>

<p align="center">
  <strong>A production-grade, AI-powered university management platform</strong><br>
  Built with Flask · Powered by Multi-Provider AI (Gemini, OpenRouter, Groq) · Telegram Bot Integration
</p>

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Features-30%2B-blue?style=for-the-badge" alt="Features"></a>
  <a href="#ai-integration"><img src="https://img.shields.io/badge/AI-Multi--Provider-purple?style=for-the-badge" alt="AI"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/Flask-3.x-green?style=for-the-badge&logo=flask" alt="Flask"></a>
  <a href="#deployment"><img src="https://img.shields.io/badge/Production-Gunicorn%20%2B%20PM2-orange?style=for-the-badge" alt="Production"></a>
  <a href="#telegram"><img src="https://img.shields.io/badge/Telegram-Bot%20Integration-blue?style=for-the-badge&logo=telegram" alt="Telegram"></a>
</p>

---

## 🌟 Overview

**University AI Batch** is a comprehensive educational platform designed for universities and academic institutions. It provides a complete ecosystem for managing lectures, assignments, grades, attendance, news, and student interactions — all enhanced with cutting-edge AI capabilities.

The platform serves **three core user roles**:
- **🛡️ Administrators** — Full control over the academic environment
- **🎓 Students** — Personalized learning dashboard and AI assistance
- **🌐 Public Visitors** — Access to news, subjects, and the AI chatbot

> **Production-Ready**: Deployed with Gunicorn (gevent async workers) + PM2, capable of handling **3,000+ concurrent connections** and **thousands of daily users**.

---

## ✨ Features

### 🛡️ Admin Dashboard
| Feature | Description |
|---------|-------------|
| **Dashboard Overview** | Real-time stats: students, subjects, lectures, recent activity |
| **Lecture Management** | Upload weekly lectures with file attachments, organized by week and type (Practical/Theoretical/Both) |
| **Subject Management** | Create, edit, delete subjects organized by semester |
| **Assignment System** | Create assignments with deadlines, file uploads, and a 0-10 grading scale |
| **Submission Review** | View, download, and grade student assignment submissions |
| **News Management** | Publish news with automatic Telegram bot notifications |
| **Attendance Tracking** | Interactive tables for marking and viewing attendance per lecture |
| **Grade Management** | Enter and manage grades for all students across subjects |
| **Feedback Management** | View, reply to, and update status of student feedback |
| **Student Management** | Add, edit, delete students; generate unique access tokens |
| **AI Settings** | Switch between AI providers (Gemini, OpenRouter, Groq) with live testing |

### 🎓 Student Portal
| Feature | Description |
|---------|-------------|
| **Personal Dashboard** | At-a-glance view of grades, attendance, upcoming tasks |
| **Profile Page** | View personal information and student details |
| **Lecture Browser** | Browse and download lectures organized by subject |
| **Task Manager** | Weekly homework, final projects, and presentations with status tracking (Not Started → In Progress → Done) |
| **Assignment Upload** | Submit assignments with file attachments before deadlines |
| **Grade Viewer** | View grades for all subjects |
| **Attendance History** | Track personal attendance records |
| **Feedback System** | Submit suggestions, inquiries, complaints; view admin replies |
| **AI Chatbot** | Personalized AI assistant with knowledge of your courses and data |

### 🤖 AI Integration
| Feature | Description |
|---------|-------------|
| **Multi-Provider Support** | Seamlessly switch between Gemini, OpenRouter, and Groq |
| **RAG (Retrieval Augmented Generation)** | AI answers enriched with real-time data from lectures, subjects, news, and student records |
| **API Key Rotation** | Up to 10 Gemini API keys with automatic rotation on quota limits |
| **Fallback System** | If one provider fails, automatically tries alternatives |
| **Conversation Memory** | Chat history maintained across sessions |
| **Provider Testing** | Admin can test each provider's API before switching |
| **10+ Free Models** | OpenRouter integration includes Llama 3.3, Qwen 2.5, Mistral, and more |

### 📱 Telegram Bot
| Feature | Description |
|---------|-------------|
| **Webhook Integration** | Real-time notifications via Telegram |
| **Auto-Notifications** | New lectures and news automatically sent to subscribed students |
| **Student Data API** | Full student data accessible via API for Telegram/n8n workflows |
| **Bot Commands** | Interactive commands for student information retrieval |

### 🎨 UI/UX
| Feature | Description |
|---------|-------------|
| **Dark/Light Themes** | Toggle between themes with persistent preference |
| **Mobile-First Design** | Fully responsive with dedicated mobile navigation |
| **Modern Typography** | Inter and Space Grotesk from Google Fonts |
| **Micro-Animations** | Counter animations, scroll effects, loading states |
| **Bootstrap 5** | Professional UI components and grid system |
| **Font Awesome Icons** | Comprehensive iconography throughout |

---

## 🏗️ Architecture

```
uniwebsite/
├── app/
│   ├── __init__.py          # Flask app factory with CORS, Markdown, filters
│   ├── routes/
│   │   ├── main.py          # Public routes: home, news, subjects, chatbot, auth
│   │   ├── admin.py         # Admin panel: CRUD for all entities (37 routes)
│   │   ├── student.py       # Student portal: dashboard, tasks, submissions (18 routes)
│   │   └── api.py           # REST API: Telegram webhook, chatbot, data endpoints
│   ├── models/
│   │   ├── base_model.py    # JSON-based persistence layer (file storage)
│   │   ├── lecture.py       # Lecture & LectureMaterial models
│   │   ├── student.py       # Student model with token authentication
│   │   ├── subject.py       # Subject model (organized by semester)
│   │   ├── attendance.py    # Attendance tracking model
│   │   ├── grade.py         # Grade management model
│   │   ├── feedback.py      # Student feedback model
│   │   ├── news.py          # News articles model
│   │   └── telegram_user.py # Telegram user<->student mapping
│   ├── utils/
│   │   ├── gemini_ai.py     # Multi-provider AI engine (Gemini/OpenRouter/Groq + RAG)
│   │   ├── auth.py          # Authentication decorators & password verification
│   │   ├── assignments.py   # Assignment management utilities
│   │   ├── file_upload.py   # Secure file upload handling
│   │   ├── n8n_webhook.py   # n8n automation integration
│   │   └── telegram_bot.py  # Telegram bot logic & notifications
│   ├── templates/           # 28 Jinja2 HTML templates
│   │   ├── base.html        # Master layout with navbar, footer, theme toggle
│   │   ├── admin/           # 18 admin templates
│   │   └── student/         # 10 student templates
│   └── static/
│       ├── css/             # Custom stylesheets (desktop + mobile)
│       ├── js/              # Client-side JavaScript
│       ├── img/             # Images and favicon
│       └── uploads/         # User-uploaded files (lectures, assignments)
├── data/                    # JSON data storage (persistence layer)
│   ├── lecture.json         # All lecture records
│   ├── student.json         # Student profiles and tokens
│   ├── subject.json         # Subject definitions by semester
│   ├── attendance.json      # Attendance records
│   ├── grade.json           # Grade records
│   ├── feedback.json        # Feedback entries and replies
│   └── news.json            # News articles
├── run.py                   # Application entry point
├── gunicorn.conf.py         # Production server config (gevent async workers)
├── ecosystem.config.js      # PM2 process manager config
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys, config)
└── .gitignore               # Git ignore rules
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, Flask 3.x, Flask-CORS, Flask-Markdown |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5.3 |
| **AI Engine** | Google Gemini 2.0 Flash, OpenRouter (10+ models), Groq |
| **Data Storage** | JSON file-based persistence (zero-dependency, portable) |
| **Deployment** | Gunicorn (gevent workers) + PM2 process manager |
| **Messaging** | Telegram Bot API, n8n webhooks |
| **Typography** | Google Fonts (Inter, Space Grotesk) |
| **Icons** | Font Awesome 6.0 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js (for PM2)
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/AladdinAlynaey/uniwebsite.git
cd uniwebsite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn gevent
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY_1` through `_10` | Google Gemini API keys (get from [Google AI Studio](https://ai.google.dev/)) |
| `GEMINI_MODEL_NAME` | Model name (default: `gemini-2.0-flash`) |
| `OPENROUTER_API_KEY` | OpenRouter API key (has free models!) |
| `GROQ_API_KEY` | Groq API key (fast and free!) |
| `SECRET_KEY` | Flask secret key for sessions |

### 3. Run (Development)

```bash
python run.py
```

Access at `http://localhost:5006`

### 4. Run (Production)

```bash
# Start with Gunicorn directly
gunicorn --config gunicorn.conf.py run:app

# Or with PM2 for process management
pm2 start ecosystem.config.js
pm2 save
```

---

## 🔐 Default Credentials

| Role | Login Method |
|------|-------------|
| **Admin** | Password: `alaadin123` (via `/login`) |
| **Student** | Unique token generated by admin (via `/student/login`) |

---

## ⚡ Production Deployment

### Gunicorn Configuration

The included `gunicorn.conf.py` is optimized for high concurrency:

| Setting | Value | Purpose |
|---------|-------|---------|
| Worker class | `gevent` (async) | Each worker handles 1000+ concurrent connections |
| Workers | `3` (matches CPU cores) | 3 × 1000 = **3,000 concurrent connections** |
| Timeout | `120s` | Accommodates slow AI API calls |
| Max requests | `2,000` | Auto-recycles workers to prevent memory leaks |
| Preload | `true` | Shares memory across workers, faster startup |

### PM2 Process Manager

The `ecosystem.config.js` provides:
- ✅ **Auto-restart** on crashes
- ✅ **Watch mode** — auto-reload when code changes
- ✅ **Startup persistence** — survives server reboots (`pm2 save`)
- ✅ **Log management** with timestamps
- ✅ **Smart ignore** — doesn't restart on data/upload changes

### Load Test Results

Tested with 200 concurrent users firing 600 requests:

```
✅ Successes:     600/600 (100.0%)
❌ Failures:      0/600 (0.0%)
⏱️ Requests/sec: 348.1
📊 Avg Latency:  79ms
📊 P95 Latency:  150ms
📊 P99 Latency:  177ms

🏆 VERDICT: EXCELLENT — Ready for production!
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/telegram/webhook` | Telegram bot webhook |
| `POST` | `/api/chatbot` | AI chatbot (JSON: `query`, `student_token`) |
| `GET` | `/api/lectures` | Get all lectures (with optional `subject_id` filter) |
| `GET` | `/api/news` | Get all news articles |
| `POST` | `/api/test-n8n-webhook` | Test n8n webhook connection |
| `POST` | `/api/send-test-news-webhook` | Send test news to n8n |
| `GET` | `/api/student-data?token=<TOKEN>` | Full student data (for Telegram/n8n) |

---

## 🤖 AI Setup Guide

### Option 1: Google Gemini (Primary)
1. Get API keys from [Google AI Studio](https://ai.google.dev/)
2. Add up to 10 keys in `.env` (`GEMINI_API_KEY_1` through `_10`)
3. Keys auto-rotate when one hits quota limits

### Option 2: OpenRouter (10+ Free Models)
1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Set `OPENROUTER_API_KEY` in `.env`
3. Auto-fallback through: Gemini Flash → Llama 3.3 70B → Qwen 2.5 72B → Mistral → and more

### Option 3: Groq (Lightning Fast)
1. Get an API key from [Groq](https://console.groq.com/)
2. Set `GROQ_API_KEY` in `.env`
3. Uses Llama 3.3 70B by default

### Switching Providers
Use the **Admin → Settings** page to switch between providers and test each one live.

---

## 📱 Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Set the webhook URL to `https://your-domain/api/telegram/webhook`
3. The bot will automatically send notifications for:
   - New lectures uploaded
   - New news articles published
   - Student data queries

---

## 📝 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**AI Eng. Alaadin Al-Ynaey**

- 🌐 [Personal Website](https://alaadin-alynaey.site)
- 💼 [LinkedIn](https://linkedin.com/in/alaadin-al-ynaey-179a88342)
- 🐙 [GitHub](https://github.com/AladdinAlynaey)
- 📧 alaadinessam2016@gmail.com

---

<p align="center">
  <strong>Built with ❤️ for Education</strong><br>
  <sub>Empowering universities with AI-driven learning management</sub>
</p>