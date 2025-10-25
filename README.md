# Xandy Learning AI Mentor System

A hybrid AI-Human mentor system that provides seamless student support when mentors are offline.

## 🚀 Quick Start

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up environment**
```bash
cp env.example .env
# Add your GEMINI_API_KEY to .env
```

3. **Run the application**
```bash
streamlit run app.py
```

## 📁 Files

- `app.py` - Main application
- `agents.py` - AI agent functions
- `database.py` - Database operations
- `logging_config.py` - Logging system
- `requirements.txt` - Dependencies

## 🔧 How it works

1. **Mentor Online**: Direct responses to students
2. **Mentor Offline**: AI generates responses → Mentor approves → Sent to student
3. **Style Learning**: AI learns mentor's communication style
4. **Session Management**: Persistent chat history

## 📊 Features

- Hybrid AI-Human responses
- Approval workflow for AI responses
- Mentor style learning
- Session management
- Comprehensive logging

## 🛡️ Security

- API keys in environment variables
- Input validation
- Audit logging


