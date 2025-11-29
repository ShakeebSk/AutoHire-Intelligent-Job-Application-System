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
AUTOHIRE/
|-- .vs/
|-- all excels/
|-- all resumes/
|-- app/
|   |-- __pycache__/
|   |-- auth/
|   |-- automation/
|   |-- dashboard/
|   |-- models/
|   |-- setup/
|   |-- static/
|   |-- templates/
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- forms.py
|   |   |-- routes.py
|-- config/
|-- data/
|-- docs/
|-- instance/
|   |-- autohire.db
|-- logs/
|-- migrations/
|-- modules/
|-- myenv/
|-- requirements/
|-- .env
|-- .gitignore
|-- LICENSE
|-- README.md
|-- app.py
|-- demo_automation.py
|-- diagnose_linkedin_ui.py
|-- finalTestScript.py
|-- manual_ui_inspector.py
|-- requirements.txt
|-- run.py
```


---
# ScreenShots
---
# Home Screen
<img width="1919" height="1024" alt="Screenshot2" src="https://github.com/user-attachments/assets/5d69012a-fe55-4609-80f3-caa7743bcc71" />
<img width="2000" height="1016" alt="Screenshot3" src="https://github.com/user-attachments/assets/cb017150-ac48-403e-ab0f-86cc286bfd80" />
<img width="1919" height="1023" alt="Screenshot4" src="https://github.com/user-attachments/assets/42236896-4d95-4b28-9e87-8bf9060770db" />
<img width="1919" he<img width="1919" height="1016" alt="Screenshot 2025-10-13 172034" src="https://github.com/user-attachments/assets/c8f05381-3d9c-4bc9-bd6b-583239aef8a6" />

# Register Page
<img width="1919" height="840" alt="Screenshot 2025-10-13 172137" src="https://github.com/user-attachments/assets/0ce56e3f-9ec5-4014-aad8-ead4532ea2c3" />
<img width="1919" height="715" alt="Screenshot 2025-10-13 172153" src="https://github.com/user-attachments/assets/63460616-0c18-42b5-a36c-b04c2ad9a06d" />

# Login Page
<img width="1918" height="1079" alt="Screenshot 2025-10-13 172237" src="https://github.com/user-attachments/assets/2504d7bf-b6f9-4999-97f1-56fa7077b29c" />

# Welcome and Prefernce Page
<img width="1917" height="1077" alt="Screenshot 2025-10-13 172549" src="https://github.com/user-attachments/assets/f132073f-d0d0-42d0-b1e6-f6c7e4025520" />
<img width="1919" height="704" alt="Screenshot 2025-10-13 172628" src="https://github.com/user-attachments/assets/36428bfb-2d17-4485-a3af-fce1ddd1a5fb" />
<img width="1919" height="888" alt="Screenshot 2025-10-13 172747" src="https://github.com/user-attachments/assets/ad0d1bbf-c483-400a-8d74-513f5f2a9071" />
<img width="1919" height="609" alt="Screenshot 2025-10-13 172805" src="https://github.com/user-attachments/assets/59ce8ad3-fe88-46f1-98d0-856d9900e5bc" />
<img width="1919" height="660" alt="Screenshot 2025-10-13 172829" src="https://github.com/user-attachments/assets/2f6bf842-3607-4ee6-8462-21830af37e86" />
<img width="1919" height="698" alt="Screenshot 2025-10-13 172846" src="https://github.com/user-attachments/assets/0b106d92-33db-4c1b-a558-20c57a1546ea" />
<img width="1919" height="705" alt="Screenshot 2025-10-13 172910" src="https://github.com/user-attachments/assets/928704d0-c453-4db5-a85b-9d558ec852bc" />
<img width="1919" height="657" alt="Screenshot 2025-10-13 172927" src="https://github.com/user-attachments/assets/c5135f31-6fe0-461a-b58d-2c0417e321f6" />

# Befor Applying Index Page

<img width="1919" height="903" alt="Screenshot 2025-10-13 173113" src="https://github.com/user-attachments/assets/2b6d3aaf-4622-4746-bc5f-fc3d2f88cdf6" />
<img width="1919" height="767" alt="Screenshot 2025-10-13 173212" src="https://github.com/user-attachments/assets/1644a1bb-e536-4a29-b1d0-306fbd8f7c88" />

# After Applying Index Page
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205141" src="https://github.com/user-attachments/assets/3878e705-1b6d-40c3-892c-5ab11161f720" />
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205157" src="https://github.com/user-attachments/assets/58b7d291-c6ae-4fe1-bfa0-cf0fc10c0c0f" />
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205203" src="https://github.com/user-attachments/assets/4b9dd7de-42ed-4522-b96d-dfe41b603e77" />


# Befor Application Page
<img width="1919" height="850" alt="Screenshot 2025-10-13 173227" src="https://github.com/user-attachments/assets/1c779e74-e20c-44af-89ab-77f288ecb566" />

# After Application Page
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205217" src="https://github.com/user-attachments/assets/55dd7b59-99b4-4d77-a799-41b7b2d24680" />
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205229" src="https://github.com/user-attachments/assets/b96bd196-f1dc-49e2-9b0f-22fdf6ded934" />
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205250" src="https://github.com/user-attachments/assets/03ef6a0f-5385-4744-8d0f-72e7de1428fb" />

# Job Analytics Page

<img width="1919" height="1079" alt="Screenshot 2025-11-16 205333" src="https://github.com/user-attachments/assets/5fe6a917-4479-4d6d-9290-0a383671e3ee" />
<img width="1919" height="1079" alt="Screenshot 2025-11-16 205346" src="https://github.com/user-attachments/assets/2872335e-00db-4dd4-a4b2-f4d3a362abcc" />

# Setting Page
<img width="1919" height="883" alt="Screenshot 2025-10-13 173257" src="https://github.com/user-attachments/assets/2d4bd210-a7a9-4904-9029-44ec4fe12dcd" />
<img width="1919" height="659" alt="Screenshot 2025-10-13 173351" src="https://github.com/user-attachments/assets/cbb05c4e-d3cd-45dc-b760-73a3572681ca" />

# Setting > Profile Page
<img width="1919" height="1011" alt="Screenshot 2025-10-13 173506" src="https://github.com/user-attachments/assets/1abeb109-aee6-4a98-9b12-3d558c1717f9" />
<img width="1918" height="858" alt="Screenshot 2025-10-13 173540" src="https://github.com/user-attachments/assets/96a03d39-074e-4a28-b8f2-eabb4c3e7453" />

# Setting > Platform Credentials Page
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/1d5cbb19-ddec-459d-ad14-39ab595ab131" />

# Setting > Job Preference Page
<img width="1919" height="1079" alt="Screenshot 2025-11-28 104820" src="https://github.com/user-attachments/assets/6b976bde-2d00-4264-9677-05d7ad1f6459" />
<img width="1918" height="705" alt="Screenshot 2025-11-28 104842" src="https://github.com/user-attachments/assets/c055b5c4-defa-4fc2-bae1-a23f51b38f8b" />

