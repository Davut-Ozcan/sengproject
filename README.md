# 📚 ZenithAI
## AI-Powered Online Language Assessment Platform

## 📌 Overview

ZenithAI is a web-based, AI-powered language assessment platform designed to evaluate users’ English proficiency through comprehensive and interactive testing modules.

The system focuses on assessing the four fundamental language skills: **Reading, Listening, Speaking, and Writing**. Each module is designed to reflect real-life language usage scenarios while ensuring objective and consistent evaluation.

Unlike traditional online language tests, ZenithAI integrates **artificial intelligence services**, including AI-based text evaluation, speech-to-text, and text-to-speech technologies. These integrations allow the system to provide a more dynamic, intelligent, and scalable assessment experience.

User authentication, test sessions, module scores, and CEFR-based proficiency levels are securely stored and managed using a **PostgreSQL-backed backend architecture**. ZenithAI aims to demonstrate the practical application of **software engineering principles, AI-supported language technologies, and modern web development practices** within an academic project context.

---

## 🎯 Project Goals

- Provide a complete online English proficiency test
- Assess four core language skills (Reading, Listening, Speaking, Writing)
- Store and manage user test sessions securely
- Integrate AI-supported evaluation mechanisms
- Generate CEFR-based overall proficiency levels
- Build a modular and scalable assessment platform

---

## 🧠 System Architecture

### Backend

- Python (FastAPI)
- SQLAlchemy (Async)
- PostgreSQL
- JWT-based Authentication
- RESTful API Architecture

### Frontend

- HTML5
- CSS3 (Custom Styling)
- JavaScript (Vanilla)
- Fetch API for backend communication

### AI & Speech Technologies

- Google Gemini API (AI evaluation)
- SpeechRecognition (Speech-to-Text)
- gTTS (Text-to-Speech)

---

## 🖼️ Application Screenshots

Below are screenshots from the ZenithAI application showcasing key pages and modules.

## 🔐 Authentication

Login Page

<p align="center">
  <img src="images/login.png" width="700"/>
</p>

Register Page

<p align="center">
  <img src="images/register.png" width="700"/>
</p>

---

## 📊 Dashboard

The dashboard allows users to access test modules and track their progress.

<p align="center">
  <img src="images/dashboard.png" width="700"/>
  <img src="images/dashboard2.png" width="700"/>
</p>

---

## 🧪 Test Modules

### 📖 Reading Module

<p align="center">
  <img src="images/reading.png" width="700"/>
  <img src="images/reading.png" width="700"/>
</p>

### 🎧 Listening Module

<p align="center">
  <img src="images/listening1.png" width="700"/>
  <img src="images/listening2.png" width="700"/>
</p>

### 🗣️ Speaking Module

<p align="center">
  <img src="images/speaking.png" width="700"/>
  <img src="images/speaking2.png" width="700"/>
  <img src="images/speaking3.png" width="700"/>
</p>

### ✍️ Writing Module

<p align="center">
  <img src="images/writing.png" width="700"/>
  <img src="images/writing2.png" width="700"/>
</p>

### ⚙️ Admin Panel

<p align="center">
  <img src="images/backend.jpeg" width="700"/>
  <img src="images/backend2.jpeg" width="700"/>
</p>

## 🤖 AI-Based Evaluation

ZenithAI integrates artificial intelligence services to support:

- Automated text evaluation
- CEFR level estimation
- Speech-to-text analysis for speaking modules
- Text-to-speech prompts for listening modules

These AI-driven components enhance objectivity, consistency, and scalability in language assessment.

---

## 🗄️ Database Design

### Main Tables

- users
- test_sessions
- module_scores

### Sample Fields

- user_id
- session_id
- module_name
- score
- cefr_level
- created_at

📌 **init.sql file is included in the project**,  
however **user-related tables must be created manually** using SQL.

---

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Davut-Ozcan/sengproject.git
cd sengproject
git checkout backend
```

### 2️⃣ Virtual Environment Setup
### Create a virtual environment:
```bash
python -m venv venv
```
### Activate the virtual environment:
Windows
```bash
venv\Scripts\activate
```
Linux / Mac
```bash
source venv/bin/activate
```

### 3️⃣ Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ PostgreSQL Database Setup
### Create the database using pgAdmin or terminal:
```bash
CREATE DATABASE virtuatest;
```
📌 Database tables are provided in the init.sql file.
⚠️ User-related tables must be created manually if not initialized automatically.

### 5️⃣ Environment Variables (.env)
### Create a .env file inside the virtualtest-backend directory:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:SIFREN@localhost:5432/virtuatest
SECRET_KEY=supersecretkey123456789
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX
```

⚠️ Notes
Replace SIFREN with your PostgreSQL password
GEMINI_API_KEY must be generated from:
https://aistudio.google.com/app/apikey
Do NOT commit the .env file to GitHub

---

### 🌐 Ports & Services

| Service      | URL |
|-------------|-----|
| Frontend    | http://localhost:5500 |
| Backend API | http://localhost:8000 |

### ▶️ Running the Application
⚠️ Virtual environment must be active before running the commands.

### ▶️ Frontend
```bash
cd .\virtualtest-frontend\
python -m http.server 5500
```
Open in browser:
👉 http://localhost:5500

### ▶️ Backend
```bash
cd .\virtualtest-backend\
uvicorn app.main:app --reload --port 8000
```

---

## 📁 Project Structure
```text
sengproject/
├── images/
│   ├── auth/
│   ├── dashboard/
│   ├── modules/
│   └── total/
│
├── virtualtest-backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── main.py
│   ├── static/
│   │   └── audio/
│   ├── .env
│   └── requirements.txt
│
└── virtualtest-frontend/
    ├── index.html
    ├── login.html
    ├── reading.html
    ├── listening.html
    ├── speaking.html
    ├── writing.html
    ├── total.html
    └── style.css
```

---
## ⭐ Conclusion

ZenithAI exemplifies the seamless integration of modern software engineering practices, advanced AI-driven language processing, and robust database-backed backend design.
The platform stands as a premier academic model for creating intelligent, modular, and scalable online language assessment systems, demonstrating how cutting-edge technologies can be applied to real-world educational challenges.








