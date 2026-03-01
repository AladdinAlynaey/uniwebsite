<div align="center">

# 🎓 University AI Platform

### Multi-Tenant University Management System with AI-Powered Learning

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)](https://elastic.co)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

<br/>

*A production-grade, multi-tenant university management platform with 5-role hierarchy, AI chatbot, Telegram integration, and premium responsive UI.*

**Built by [AI Eng. Alaadin](https://alaadin-alynaey.site)**

</div>

---

## 🏗️ Architecture

```
University (Super Admin)
  └── Faculty (Faculty Head)
       └── Department
            └── Batch (Batch Representative)
                 ├── Teacher (per Subject)
                 └── Student
```

**5 Distinct Roles** — each with scoped data access, dedicated dashboard, and role-specific features.

| Role | Access Level | Dashboard |
|------|-------------|-----------|
| 🟣 **University Manager** | Full system control | `/superadmin/dashboard` |
| 🔵 **Faculty Head** | Faculty-scoped management | `/faculty/dashboard` |
| 🟢 **Teacher** | Subject-scoped teaching tools | `/teacher/dashboard` |
| 🟡 **Batch Representative** | Batch administration | `/admin/dashboard` |
| 🔵 **Student** | Personal academic portal | `/student/dashboard` |

---

## ✨ Key Features

### 🏛️ Multi-Tenant Hierarchy
- **University → Faculty → Department → Batch** organizational structure
- Role-based data scoping — users only see data within their scope
- Hierarchical user management with cascading permissions

### 🤖 AI-Powered Learning
- **Gemini API** integration with intelligent chatbot
- Multi-provider fallback system (Gemini → OpenRouter → Groq)
- Retrieval-Augmented Generation (RAG) using university knowledge base
- Context-aware responses with student-specific data

### 📱 Telegram Bot Integration
- Real-time notifications for lectures, grades, and announcements
- Student verification and linking via Telegram
- Webhook-based architecture for instant delivery

### 📊 Academic Management
- **Attendance tracking** with presence rate analytics
- **Grade management** with component breakdown (homework, midterm, final)
- **Lecture management** with file uploads and material organization
- **Assignment system** with submission tracking and grading
- **Feedback system** with admin replies and status tracking

### 🔒 Security
- **Bcrypt password hashing** (Werkzeug security)
- **Session-based authentication** with role validation
- **CSRF protection** via Flask sessions
- **Input sanitization** on all form inputs
- **Scoped data access** — enforced at every route level
- **Rate limiting** ready architecture
- **Environment variable** based secret management

### 🎨 Premium UI
- **Dark/Light theme** toggle with persistence
- **Responsive design** — works on all devices
- **Modern glassmorphism** effects and gradient accents
- **Animated counters** and micro-interactions
- **Role-colored navigation** — unique identity per role

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.0 |
| **Database** | Elasticsearch 8.x |
| **AI** | Google Gemini API, OpenRouter, Groq |
| **Frontend** | Bootstrap 5, Font Awesome 6, Custom CSS |
| **Fonts** | Inter, Space Grotesk (Google Fonts) |
| **Bot** | Telegram Bot API (Webhook mode) |
| **Auth** | Werkzeug Security, Flask Sessions |
| **Server** | Gunicorn + PM2 (production) |

---

## 📁 Project Structure

```
uniwebsite/
├── app/
│   ├── __init__.py              # App factory, blueprint registration
│   ├── models/
│   │   ├── base_model.py        # Elasticsearch CRUD base class
│   │   ├── user.py              # Unified user model (5 roles)
│   │   ├── faculty.py           # Faculty model
│   │   ├── department.py        # Department model
│   │   ├── batch.py             # Batch model
│   │   ├── teacher_subject.py   # Teacher-Subject linking
│   │   ├── student.py           # Legacy student model
│   │   ├── subject.py           # Subject model
│   │   ├── lecture.py           # Lecture & materials
│   │   ├── attendance.py        # Attendance records
│   │   ├── grade.py             # Grade management
│   │   ├── feedback.py          # Student feedback
│   │   ├── news.py              # University news
│   │   └── telegram_user.py     # Telegram linking
│   ├── routes/
│   │   ├── main.py              # Public pages, unified login
│   │   ├── superadmin.py        # University Manager routes
│   │   ├── faculty_head.py      # Faculty Head routes
│   │   ├── teacher.py           # Teacher routes
│   │   ├── admin.py             # Batch Rep routes (legacy)
│   │   ├── student.py           # Student routes
│   │   └── api.py               # REST API & Telegram webhook
│   ├── templates/
│   │   ├── base.html            # Role-aware navigation
│   │   ├── index.html           # Landing page with 5-role portal
│   │   ├── login.html           # Unified staff login
│   │   ├── student_login.html   # Student login (token + email)
│   │   ├── superadmin/          # 10 Super Admin templates
│   │   ├── faculty/             # 4 Faculty Head templates
│   │   ├── teacher/             # 6 Teacher templates
│   │   ├── admin/               # Batch Rep templates
│   │   └── student/             # Student templates
│   ├── static/
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript
│   │   └── img/                 # Assets
│   └── utils/
│       ├── auth.py              # Role decorators & session management
│       ├── elasticsearch_client.py  # ES connection & data migration
│       └── gemini_ai.py         # AI provider management
├── data/                        # JSON data (legacy, gitignored)
├── .env                         # API keys & secrets (gitignored)
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Elasticsearch 8.x running on `localhost:9200`
- Gemini API key (or OpenRouter/Groq key)

### Installation

```bash
# Clone the repository
git clone https://github.com/AladdinAlynaey/uniwebsite.git
cd uniwebsite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production

# AI API Keys (at least one required)
GEMINI_API_KEY_1=your-gemini-key
OPENROUTER_API_KEY=your-openrouter-key
GROQ_API_KEY=your-groq-key

# Elasticsearch
ES_HOST=http://localhost:9200
```

### Running

```bash
# Development
python run.py

# Production (with Gunicorn + PM2)
pm2 start ecosystem.config.js
```

The app runs on **http://localhost:5006** by default.

### First Login

On first startup, the system automatically creates:
- A default **Faculty** (General Faculty)
- A default **Department** (General Department)  
- A default **Batch** (Batch 2024)
- A **Super Admin** account: `admin@university.edu` / `admin123`

> ⚠️ **Change the default admin password immediately after first login!**

---

## 🔐 Security Features

| Feature | Implementation |
|---------|---------------|
| Password Hashing | Werkzeug `generate_password_hash` (pbkdf2:sha256) |
| Session Security | Flask signed sessions with `SECRET_KEY` |
| Role Enforcement | Decorators: `@super_admin_required`, `@faculty_head_required`, `@teacher_required`, etc. |
| Data Scoping | Every query filtered by user's `faculty_id`, `department_id`, `batch_id` |
| Input Validation | Server-side validation on all forms |
| API Security | Token-based Telegram webhook verification |
| Environment Variables | All secrets in `.env`, never committed to Git |
| CORS | Configured via Flask-CORS |

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/webhook` | POST | Telegram bot webhook |
| `/api/chatbot` | POST | AI chatbot query |
| `/api/lectures` | GET | Public lecture data |
| `/api/news` | GET | Public news feed |
| `/api/student-data` | GET | Student info (authenticated) |
| `/api/test-webhook` | POST | Webhook testing |

---

## 🎨 Screenshots

### Landing Page & Login Portal
The landing page features a 5-role login portal, animated stat counters, and modern hero section.

### Role-Specific Dashboards
Each role gets a dedicated dashboard with relevant stats, quick actions, and management tools.

### Premium Dark/Light Theme
Toggle between themes with persistent preference. All roles have unique color coding.

---

## 👨‍💻 Author

**AI Eng. Alaadin Al-Ynaey**

- 🌐 [Website](https://alaadin-alynaey.site)
- 💼 [LinkedIn](https://linkedin.com/in/alaadin-al-ynaey-179a88342)
- 🐙 [GitHub](https://github.com/AladdinAlynaey)
- 📧 alaadinessam2016@gmail.com

---

## 📄 License

**This software is proprietary and confidential.** See [LICENSE](LICENSE) for full terms.

All rights reserved. No part of this software may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the author.

---

<div align="center">

**Built by AI Eng. Alaadin**

*University AI Platform — Transforming Education Through Technology*

</div>