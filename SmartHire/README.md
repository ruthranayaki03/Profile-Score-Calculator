# SmartHire - AI-Powered Interview Platform

<p align="center">
  <img src="https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/ML-Scikit--Learn-orange?style=for-the-badge&logo=scikit-learn" alt="ML">
  <img src="https://img.shields.io/badge/AWS-Transcribe-yellow?style=for-the-badge&logo=amazon-aws" alt="AWS">
</p>

## 🚀 Overview

SmartHire is an automated interview platform that uses Machine Learning, Video Analysis, and NLP to streamline the hiring process. It helps HR teams evaluate candidates efficiently with AI-powered insights.

### ✨ Key Features

- **🧠 AI Personality Prediction** - ML-based personality analysis using the Big Five (OCEAN) model
- **📹 Video Interview Recording** - Browser-based video recording with MediaRecorder API
- **🎯 Tone Analysis** - IBM Watson integration for emotional tone detection
- **📄 Resume Parsing** - Automatic extraction of skills, experience, and qualifications
- **📧 One-Click Emails** - Send acceptance/rejection emails instantly
- **🔐 Secure Authentication** - Django's built-in auth with password hashing
- **📊 Analytics Dashboard** - Track interview metrics and candidate status

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 4.2, Python 3.10+ |
| **Database** | SQLite (default) / MySQL / PostgreSQL |
| **ML/AI** | Scikit-learn, NLTK, spaCy |
| **Video Analysis** | OpenCV, FER (Facial Emotion Recognition) |
| **Speech-to-Text** | AWS Transcribe |
| **Tone Analysis** | IBM Watson Tone Analyzer |
| **Task Queue** | Celery + Redis |
| **Frontend** | Bootstrap 5, Font Awesome |

---

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Redis (optional, for Celery async tasks)
- AWS Account (optional, for speech-to-text)
- IBM Watson Account (optional, for tone analysis)

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd SmartHire

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download NLP Models

```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader words stopwords
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux

# Edit .env with your settings
```

### 4. Setup Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Load Initial Data (Optional)

```bash
# Create some interview questions
python manage.py shell
```

```python
from interviews.models import InterviewQuestion, JobPosition

# Add default questions
InterviewQuestion.objects.create(order=1, text="Tell me about yourself.")
InterviewQuestion.objects.create(order=2, text="Why should we hire you?")
InterviewQuestion.objects.create(order=3, text="Where do you see yourself in 5 years?")

# Add a job position
JobPosition.objects.create(
    title="Software Development Engineer",
    department="Engineering",
    description="Full-stack development role"
)
```

### 6. Run the Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## 👤 User Roles

### Candidate
1. Register/Login
2. Complete profile (personal info, resume, personality assessment)
3. Record video responses to interview questions
4. View interview status and results

### HR/Admin
1. Login with company credentials
2. View all candidates and their interviews
3. Watch recorded videos and review analysis
4. Accept/Reject candidates with one-click emails
5. Manage job positions and interview questions

---

## 🔧 Configuration

### Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Update `.env`:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

### AWS Transcribe Setup

1. Create an S3 bucket
2. Create IAM user with `AmazonTranscribeFullAccess` and `AmazonS3FullAccess`
3. Update `.env` with credentials

### IBM Watson Setup

1. Create Tone Analyzer service on [IBM Cloud](https://cloud.ibm.com)
2. Get API key and URL from service credentials
3. Update `.env` with credentials

---

## 📂 Project Structure

```
SmartHire/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── smarthire/              # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── interviews/             # Main app
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Django forms
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   ├── services.py        # Business logic
│   ├── tasks.py           # Celery async tasks
│   └── signals.py         # Django signals
├── templates/              # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── registration/
│   ├── candidate/
│   └── hr/
├── static/                 # Static files
│   ├── css/
│   ├── js/
│   └── data/
└── media/                  # Uploaded files
    ├── resumes/
    ├── videos/
    └── analysis/
```

---

## 🔒 Security Features

- ✅ Password hashing with Django's PBKDF2
- ✅ CSRF protection on all forms
- ✅ Session-based authentication
- ✅ Role-based access control (Candidate/HR/Admin)
- ✅ Secure file uploads with validation
- ✅ XSS protection
- ✅ SQL injection prevention via ORM

---

## 📊 Improvements over Flask Version

| Issue | Flask (Old) | Django (New) |
|-------|-------------|--------------|
| Password Storage | Plain text ❌ | Hashed ✅ |
| Session Management | None ❌ | Built-in ✅ |
| Multiple Candidates | Single JSON file ❌ | Database ✅ |
| Video Processing | Blocking ❌ | Async (Celery) ✅ |
| Candidate List | Hardcoded ❌ | Dynamic ✅ |
| Resume Storage | Public folder ❌ | Protected media ✅ |
| Error Handling | Crashes ❌ | Graceful ✅ |
| Admin Panel | None ❌ | Django Admin ✅ |

---

## 🚀 Running Celery (Optional)

For async video processing:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A smarthire worker -l info

# Terminal 3: Start Django
python manage.py runserver
```

---

## 📝 License

MIT License - feel free to use for personal or commercial projects.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ using Django**


