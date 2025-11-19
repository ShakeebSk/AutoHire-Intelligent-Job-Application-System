<h1 align="center">🚀 AutoHire – Intelligent Job Application System</h1>

<p align="center"><em>AI-Powered Smart Job Application Automation</em></p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/ShakeebSk/AutoHire-Intelligent-Job-Application-System?color=blue&label=Last%20Commit">
  <img src="https://img.shields.io/github/stars/ShakeebSk/AutoHire-Intelligent-Job-Application-System?style=flat&color=yellow">
  <img src="https://img.shields.io/github/forks/ShakeebSk/AutoHire-Intelligent-Job-Application-System?style=flat&color=blue">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Automation-Selenium%2FPlaywright-orange">
</p>

<p align="center">
  Built using the following technologies:<br>
  <img src="https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask">
  <img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-blue?style=for-the-badge">
</p>

---

# 🤖 AutoHire — AI-Assisted Job Application Automation System

**AutoHire** is a fully automated system that applies for jobs on your behalf across multiple platforms like **LinkedIn, Internshala, Indeed, and Naukri**.  
It intelligently uploads resumes, fills forms, answers questions using **AI (Gemini/OpenAI)**, and logs applications automatically.

Designed as a **Final Year Engineering Project**, AutoHire brings real-world automation and AI-driven workflows into one powerful system.

> 🧠 *“Work smarter. Automate the repetitive.”*

---

# 📖 What Is AutoHire?

AutoHire simplifies the job application process by automating:

- Platform login  
- Resume upload  
- Job search  
- Form filling  
- AI-based question answering  
- Submission  
- Logging every job application in Excel  

It’s a complete end-to-end automation and AI system.

---

# ⚙️ Core Components

| Component | Description |
|-----------|-------------|
| 🔐 **Auth System** | Login/Signup, secure credential storage |
| 📄 **Resume Engine** | Upload PDF/DOCX, extract and store user details |
| 🔍 **Job Automation Engine** | Handles Selenium/Playwright-based automation |
| 🧠 **AI Answering System** | Uses Gemini/OpenAI to auto-answer job questions |
| 🗃️ **Logger** | Saves every job application in Excel |
| 🏗️ **Database** | Uses SQLite/MySQL for storing user data |

---

# 🚀 Major Features

| Category | Features |
|----------|----------|
| 💼 **Platform Automation** | LinkedIn, Internshala, Indeed, Naukri |
| 🧠 **AI Integration** | Gemini + OpenAI fallback |
| 📄 **Resume Management** | Upload, edit, parse resume |
| 🔐 **User Accounts** | Login/Signup, session handling |
| 📊 **Excel Logs** | Auto-logs every applied job |
| 🛑 **Fail-Safe Mode** | Stops on unknown forms/questions |
| 🎯 **Daily Applications** | Up to 10 per day |
| 🧭 **Priority Selection** | Order defines automation priority |
| ⚙️ **Full Config Control** | Via `.env` file |

---

# ⚔️ AutoHire vs Manual Job Applications

| Feature | Manual | AutoHire |
|---------|--------|----------|
| Apply to multiple platforms | ❌ | ✅ |
| AI answers forms | ❌ | ✅ |
| Automatic resume submission | ❌ | ✅ |
| Apply 10 jobs daily | ❌ | ✅ |
| Excel logging | ❌ | ✅ |
| Error handling | ❌ | ✅ |

---

# 🎬 AutoHire Demo

> Replace with your YouTube video link.

[![Watch the Demo](assets/thumbnail.png)](YOUTUBE_LINK)

---

# 🧪 Environment Configuration (`.env`)

```ini
# AutoHire Environment Configuration

# Database
DATABASE_URL=sqlite:///autohire.db
SECRET_KEY=your-secret-key-here-change-in-production

# AI Configuration
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key (optional fallback)
OPENAI_API_KEY=your_openai_api_key_here

# AI Service Behavior
AI_QUESTION_ANSWERING_ENABLED=true
AI_DEFAULT_SERVICE=gemini
AI_REQUEST_TIMEOUT=10
AI_MAX_RETRIES=3
AI_FALLBACK_ANSWERS=true

# Application Settings
MAX_DAILY_APPLICATIONS=10
WTF_CSRF_ENABLED=true

```
---
# Installation
---
```ini
git clone https://github.com/ShakeebSk/AutoHire-Intelligent-Job-Application-System

cd AutoHire-Intelligent-Job-Application-System

python -m venv venv

venv/Scripts/activate

pip install -r requirements.txt

python main.py
```

---
# Project Structure
---
```ini




```


