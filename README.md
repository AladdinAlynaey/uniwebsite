<div align="center">

# 🎓 University AI Platform

### Enterprise-Grade Multi-Tenant University Management System with AI-Powered Learning

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)](https://elastic.co)
[![Google Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

<br/>

*A production-grade, multi-tenant university management platform featuring a 5-role hierarchical access system, multi-provider AI chatbot with role-aware context, Telegram bot integration, faculty-scoped news, 60+ premium templates, and a fully responsive dark/light UI.*

**Built by [AI Eng. Alaadin Al-Ynaey](https://alaadin-alynaey.site)** • 📧 alaadinessam2016@gmail.com

---

**39 Users** · **2 Faculties** · **14 Subjects** · **8 Teachers** · **60 Templates** · **328 Tests Passed**

</div>

---

## 📖 Table of Contents

- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Role-Based Access Control](#-role-based-access-control)
- [AI Chatbot System](#-ai-chatbot-system)
- [Faculty-Scoped News System](#-faculty-scoped-news-system)
- [Telegram Bot Integration](#-telegram-bot-integration)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Screenshots](#-screenshots)
- [Author](#-author)
- [License](#-license)

---

## 🏗️ Architecture

```
University (Super Admin)
  └── Faculty (Faculty Head)
       └── Department
            └── Batch (Batch Representative ⭐)
                 ├── Teacher (per Subject)
                 └── Student ✋
```

**5 Distinct Roles** — each with scoped data access, dedicated dashboard, and role-specific capabilities:

| Role | Users | Access Scope | Dashboard | AI Context |
|------|:-----:|-------------|-----------|------------|
| 🟣 **University Manager** | 1 | Full system control | `/superadmin/dashboard` | System-wide stats |
| 🔵 **Faculty Head** | 2 | Faculty-scoped management | `/faculty/dashboard` | Faculty departments, teachers, batches |
| 🟢 **Teacher** | 8 | Subject-scoped teaching tools | `/teacher/dashboard` | Assigned subjects |
| 🟡 **Batch Representative** | 3 | Batch admin + own student data ⭐ | `/admin/dashboard` | Batch stats + own grades/attendance |
| 🔵 **Student** | 25 | Personal academic portal | `/student/dashboard` | Own grades, attendance, assignments |

### Multi-Tenancy Model

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIVERSITY (Super Admin)                  │
├────────────────────────┬────────────────────────────────────┤
│  Faculty: AIIT         │  Faculty: Engineering              │
│  ├── Dept: AI          │  └── Dept: Computer Engineering    │
│  │   ├── Alaadin's     │      └── CE Batch 2025            │
│  │   │   Batch (17)    │          ├── Dr. Nabil Saleh       │
│  │   │   ├── 6 Teachers│          ├── Dr. Layla Hassan      │
│  │   │   └── ⭐ Alaadin│          ├── 3 Students             │
│  │   └── Test Batch    │          └── ⭐ Ali Mohammed        │
│  │       2025 (5)      │                                    │
│  │       └── ⭐ Ahmed   │                                    │
│  └── Head: Prof. Al-Q. │  └── Head: Prof. Al-Amin           │
└────────────────────────┴────────────────────────────────────┘
```

Data isolation is enforced at every level — users **never** see data outside their organizational scope.

---

## ✨ Key Features

### 🏛️ Multi-Tenant Hierarchy
- **University → Faculty → Department → Batch** 4-level organizational structure
- Role-based data scoping — queries automatically filtered by user's faculty/batch
- Hierarchical user management with cascading permissions
- 5 distinct auth decorators enforcing access at the route level

### 🤖 Role-Aware AI Chatbot
- **Multi-provider** fallback system: Google Gemini → OpenRouter → Groq
- **Role-aware context** — AI receives different data per user role:
  - 🔑 Super Admin → system-wide statistics (faculties, users, departments)
  - 🏛️ Faculty Head → faculty departments, batches, teacher lists
  - 👨‍🏫 Teacher → assigned subjects and codes
  - ⭐ Batch Rep → batch management + own student grades/attendance
  - 📚 Student → personal grades, attendance, assignments
- Retrieval-Augmented Generation (RAG) using live university data
- Conversation memory with session persistence
- Bilingual support (Arabic/English — auto-detects language)
- Configurable via `.env` — switch providers instantly

### 📰 Faculty-Scoped News
- News items tagged with **faculty_id** and **batch_id** at creation time
- **Source badges** on news cards: `🏛️ AIIT → Alaadin's Batch`
- Logged-in users see news **filtered to their faculty** only
- Anonymous visitors see all news
- Batch reps create news scoped to their batch automatically
- Spotlight and grid cards both display faculty→batch origin

### ⭐ Batch Representative = Student
- Batch representatives have **dual role**: admin + student
- Dedicated **My Grades** and **My Attendance** views in admin panel
- **⭐ Star icon** next to batch rep's name in student lists
- **✋ Hand icon** next to regular students
- AI chatbot receives both batch admin context and student data

### 📱 Telegram Bot Integration
- Real-time notifications for lectures, grades, and announcements
- Student verification and linking via Telegram
- Webhook-based architecture for instant delivery
- n8n webhook integration for automation workflows

### 📊 Academic Management
- **Attendance tracking** with presence rate analytics and per-subject breakdown
- **Grade management** with component breakdown (homework, midterm, final)
- **Lecture management** with file uploads and material organization
- **Assignment system** with weekly homework, projects, presentations
- **Feedback system** with admin replies and status tracking
- **50+ pre-loaded lectures** across 14 subjects

### 🎨 Premium UI (60 Templates)
- **Dark/Light theme** toggle with persistent preference
- **Responsive design** — mobile-first, works on all devices
- **Modern glassmorphism** effects and gradient accents
- **Animated counters** and micro-interactions
- **Role-colored navigation** — unique identity per role
- **Google Fonts** (Inter, Space Grotesk) — no browser defaults
- Premium login/registration forms with animated backgrounds

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.10+, Flask 3.0 | Application framework |
| **Database** | Elasticsearch 8.x | Document store with full-text search |
| **AI Providers** | Google Gemini, OpenRouter, Groq | Multi-provider AI with automatic fallback |
| **Frontend** | Bootstrap 5, Font Awesome 6, Custom CSS | Responsive UI framework |
| **Typography** | Inter, Space Grotesk (Google Fonts) | Premium typography |
| **Bot** | Telegram Bot API (Webhook mode) | Real-time notifications |
| **Auth** | Werkzeug Security, Flask Sessions | Password hashing & session management |
| **Server** | Gunicorn + PM2 (production) | Process management & auto-restart |
| **Async** | gevent | Concurrent request handling |

---

## 📁 Project Structure

```
uniwebsite/
├── app/
│   ├── __init__.py                  # App factory, blueprint registration
│   ├── models/                      # 13 Elasticsearch models
│   │   ├── base_model.py            # ES CRUD base class
│   │   ├── user.py                  # Unified user model (5 roles)
│   │   ├── faculty.py               # Faculty model
│   │   ├── department.py            # Department model
│   │   ├── batch.py                 # Batch model (with rep_id)
│   │   ├── teacher_subject.py       # Teacher ↔ Subject linking
│   │   ├── student.py               # Legacy student model
│   │   ├── subject.py               # Subject model
│   │   ├── lecture.py               # Lecture & materials
│   │   ├── attendance.py            # Attendance records
│   │   ├── grade.py                 # Grade management
│   │   ├── feedback.py              # Student feedback
│   │   ├── news.py                  # Faculty-scoped news
│   │   └── telegram_user.py         # Telegram linking
│   ├── routes/                      # 7 route blueprints
│   │   ├── main.py                  # Public pages, login, chatbot
│   │   ├── superadmin.py            # Super Admin routes (10 views)
│   │   ├── faculty_head.py          # Faculty Head routes (4 views)
│   │   ├── teacher.py               # Teacher routes (6 views)
│   │   ├── admin.py                 # Batch Rep routes + My Grades/Attendance
│   │   ├── student.py               # Student routes
│   │   └── api.py                   # REST API & webhooks
│   ├── templates/                   # 60 Jinja2 templates
│   │   ├── base.html                # Role-aware navigation + theme toggle
│   │   ├── index.html               # Landing page with 5-role portal
│   │   ├── login.html               # Premium staff login (glassmorphism)
│   │   ├── student_login.html       # Student login (token + email)
│   │   ├── chatbot.html             # AI chatbot interface
│   │   ├── news.html                # News with faculty→batch badges
│   │   ├── news_detail.html         # News detail with source badge
│   │   ├── superadmin/              # 10 Super Admin templates
│   │   ├── faculty/                 # 4 Faculty Head templates
│   │   ├── teacher/                 # 6 Teacher templates
│   │   ├── admin/                   # Batch Rep templates
│   │   └── student/                 # Student templates
│   ├── static/
│   │   ├── css/                     # Stylesheets (dark/light themes)
│   │   ├── js/                      # JavaScript
│   │   └── img/                     # Assets & icons
│   └── utils/
│       ├── auth.py                  # 5 role decorators & session mgmt
│       ├── elasticsearch_client.py  # ES connection, migration, indexing
│       ├── gemini_ai.py             # Multi-provider AI (role-aware)
│       └── assignments.py           # Assignment management
├── data/                            # JSON seed data (gitignored)
├── .env                             # API keys & secrets (gitignored)
├── .env.example                     # Template for .env setup
├── requirements.txt                 # Python dependencies
├── ecosystem.config.js              # PM2 production config
├── run.py                           # Application entry point
├── TEST_GUIDE.md                    # 328-test comprehensive audit
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Elasticsearch 8.x** running on `localhost:9200`
- At least one AI API key (Gemini, OpenRouter, or Groq)

### Installation

```bash
# Clone the repository
git clone https://github.com/AladdinAlynaey/uniwebsite.git
cd uniwebsite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your keys:

```env
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production

# AI API Keys (at least one required)
GEMINI_API_KEY_1=your-gemini-key
GEMINI_API_KEY_2=your-backup-gemini-key     # optional
GEMINI_API_KEY_3=your-third-gemini-key      # optional
GEMINI_API_KEY_4=your-fourth-gemini-key     # optional
OPENROUTER_API_KEY=your-openrouter-key      # fallback
GROQ_API_KEY=your-groq-key                  # fallback

# Active AI Provider (gemini, openrouter, or groq)
ACTIVE_AI_PROVIDER=gemini

# Elasticsearch
ES_HOST=http://localhost:9200

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/webhook

# n8n Webhook (optional)
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/...
```

### Running

```bash
# Development
python run.py

# Production (Gunicorn + PM2)
pm2 start ecosystem.config.js
```

The app runs on **http://localhost:5006** by default.

### First Login

On first startup, the system automatically seeds:
- 2 Faculties (AIIT, Engineering)
- 2 Departments
- 3 Batches with assigned batch representatives
- 8 Teachers with subject assignments
- 25 Students across 3 batches
- 14 Subjects (10 AIIT + 4 Engineering)
- 50 Lectures
- A **Super Admin**: `admin@university.edu` / `admin123`

> ⚠️ **Change the default admin password immediately after first login!**

---

## 🔐 Role-Based Access Control

### Auth Decorator Architecture

Five decorators enforce access at the route level:

```python
@super_admin_required    # Only super_admin
@faculty_head_required   # faculty_head + super_admin
@teacher_required        # teacher + super_admin
@login_required          # super_admin + faculty_head + batch_rep
@student_token_required  # Only student
```

### Detailed Access Matrix

| Route Group | Decorator | 🟣 SA | 🔵 FH | 🟢 TC | 🟡 BR | 🔵 ST |
|-------------|-----------|:-----:|:-----:|:-----:|:-----:|:-----:|
| `/superadmin/*` | `super_admin_required` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/faculty/*` | `faculty_head_required` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/teacher/*` | `teacher_required` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/admin/*` | `login_required` | ✅ | ✅ | ❌ | ✅ | ❌ |
| `/student/*` | `student_token_required` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `/profile` | any logged in | ✅ | ✅ | ✅ | ✅ | ✅ |
| Public pages | none | ✅ | ✅ | ✅ | ✅ | ✅ |

### Data Scoping (Vertical Isolation)

Even when a user CAN access a route, they only see data within their organizational scope:

| User | Sees |
|------|------|
| Super Admin | All faculties, all batches, all users |
| AIIT Head | Only AIIT departments, batches, teachers |
| ENG Head | Only ENG departments, batches, teachers |
| Batch Rep | Only own batch's students, lectures, grades |
| Student | Only own grades, attendance, assignments |

---

## 🤖 AI Chatbot System

### Architecture

```
User Query → Session Context → Role Detection → Context Builder → System Prompt
     ↓              ↓               ↓                ↓                ↓
  "What are   user role,       super_admin?     Load system     Build prompt
   my grades?" faculty_id,     teacher?         stats, faculty  with role
               batch_id        student?         data, or        context
                                                student data
                                                     ↓
                                              Provider Chain
                                         Gemini → OpenRouter → Groq
                                                     ↓
                                              AI Response → User
```

### Role-Aware Context

| Role | Context Injected into AI |
|------|------------------------|
| 🔑 Super Admin | Faculty count, department count, user count, batch count |
| 🏛️ Faculty Head | Faculty name, departments, batches, teacher list |
| 👨‍🏫 Teacher | Assigned subject names and codes |
| ⭐ Batch Rep | Batch name + own grades, attendance (dual context) |
| 📚 Student | Name, email, grades per subject, attendance per subject |

### Multi-Provider Fallback

```
Primary Provider (configurable via .env)
     │
     ├── Try primary → Success? Return response
     │
     ├── Fail? Try provider #2
     │        │
     │        ├── Success? Return response
     │        │
     │        └── Fail? Try provider #3
     │                 │
     │                 ├── Success? Return response
     │                 │
     │                 └── All failed → Graceful error message
```

---

## 📰 Faculty-Scoped News System

### How It Works

1. **Creation**: When a batch rep creates news, `faculty_id` and `batch_id` are automatically attached
2. **Display**: News cards show a source badge: `🏛️ AIIT → Alaadin's Batch`
3. **Filtering**: Logged-in users see only news from their faculty; anonymous users see all
4. **Scoping**: Batch reps see batch-specific news; faculty heads see faculty-wide news

### Source Badge Examples

```
┌──────────────────────────────────────┐
│ 🏛 AIIT → Alaadin's Batch           │
│ ┌──────────────────────────────────┐ │
│ │ New Assignment Due This Week     │ │
│ │ Please submit your project by... │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🏛 Engineering → CE Batch 2025      │
│ ┌──────────────────────────────────┐ │
│ │ Lab Hours Changed               │ │
│ │ Starting next week, the lab...  │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

---

## 📱 Telegram Bot Integration

| Feature | Description |
|---------|-------------|
| Student Linking | Students verify identity via Telegram |
| Lecture Notifications | Automatic alerts when new lectures are posted |
| Grade Notifications | Students notified when grades are recorded |
| News Broadcasts | University announcements sent to linked students |
| Webhook Architecture | Real-time delivery via Telegram Webhook API |

---

## 📡 API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/chatbot` | POST | Session | AI chatbot query (role-aware) |
| `/api/webhook` | POST | Token | Telegram bot webhook |
| `/api/lectures` | GET | Public | Lecture data feed |
| `/api/news` | GET | Public | News feed |
| `/api/student-data` | GET | Session | Student information |
| `/api/test-webhook` | POST | Session | Webhook testing |

### Chatbot API Example

```bash
curl -X POST http://localhost:5006/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my grades?"}'
```

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| **Password Hashing** | Werkzeug `generate_password_hash` (pbkdf2:sha256) |
| **Session Security** | Flask signed sessions with `SECRET_KEY` |
| **Role Enforcement** | 5 decorators: `super_admin_required`, `faculty_head_required`, `teacher_required`, `login_required`, `student_token_required` |
| **Data Scoping** | Every query filtered by user's `faculty_id`, `department_id`, `batch_id` |
| **Input Validation** | Server-side validation on all forms |
| **API Security** | Token-based Telegram webhook verification |
| **Secrets** | All API keys in `.env`, never committed to Git |
| **CORS** | Configured via Flask-CORS |

---

## 🧪 Testing

### Test Coverage

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║   TOTAL TESTS:     328                           ║
║   PASSED:          328  ✅                        ║
║   FAILED:            0  ❌                        ║
║   PASS RATE:      100%  🏆                        ║
║                                                  ║
║   USERS TESTED:     22  (all named users)        ║
║   ENDPOINTS:        17  (all routes)             ║
║   FEATURES:          4  (latest release)         ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

### What's Tested

| Category | Tests | Result |
|----------|:-----:|:------:|
| Public Pages | 6 | ✅ |
| Super Admin Access | 14 | ✅ |
| Faculty Head Access (×2) | 28 | ✅ |
| Teacher Access (×8) | 96 | ✅ |
| Batch Rep Access (×3) | 42 | ✅ |
| Student Access (×8) | 104 | ✅ |
| AI Context per Role | 22 | ✅ |
| Faculty-Scoped News | 16 | ✅ |
| **Total** | **328** | **✅ 100%** |

> 📋 Full test report: [`TEST_GUIDE.md`](TEST_GUIDE.md)

### Running Tests

```bash
# Automated access control test
python test_access.py
```

---

## 🚀 Deployment

### Production with Gunicorn + PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start the application
pm2 start ecosystem.config.js

# Auto-restart on server reboot
pm2 startup
pm2 save

# Monitor
pm2 monit
```

### PM2 Configuration

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'uniwebsite',
    script: 'venv/bin/gunicorn',
    args: '-w 4 -b 0.0.0.0:5006 --timeout 120 "app:create_app()"',
    cwd: '/path/to/uniwebsite',
    env: {
      FLASK_ENV: 'production'
    }
  }]
};
```

---

## 🎨 Screenshots

### Landing Page & Login Portal
The landing page features a 5-role login portal, animated stat counters, and a modern hero section with gradient accents.

### Role-Specific Dashboards
Each role gets a dedicated dashboard with relevant stats, quick actions, management tools, and role-colored navigation.

### Premium Dark/Light Theme
Toggle between themes with persistent preference. All 5 roles have unique color coding — purple for super admin, blue for faculty head, green for teacher, yellow for batch rep, and blue for student.

### AI Chatbot
Role-aware AI chatbot with conversation history, markdown rendering, and multi-language support.

### Faculty-Scoped News
News cards with faculty→batch source badges, spotlight sections, and scoped visibility.

---

## 👨‍💻 Author

**AI Eng. Alaadin Al-Ynaey**

- 🌐 [Portfolio](https://alaadin-alynaey.site)
- 💼 [LinkedIn](https://linkedin.com/in/alaadin-al-ynaey-179a88342)
- 🐙 [GitHub](https://github.com/AladdinAlynaey)
- 📧 alaadinessam2016@gmail.com

---

## 📄 License

**This software is proprietary and confidential.** See [LICENSE](LICENSE) for full terms.

All rights reserved. No part of this software may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the author.

---

<div align="center">

**Built with ❤️ by AI Eng. Alaadin**

*University AI Platform — Transforming Education Through Intelligent Technology*

**39 Users · 5 Roles · 3 AI Providers · 60 Templates · 328 Tests Passed · 0 Failures**

</div>