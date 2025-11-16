# 🤖 AI Email Automation Agent

> **Intelligent email automation system powered by AI that reads, analyzes, and automatically responds to emails**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🎯 Overview

AI Email Automation Agent is a production-ready system that leverages Large Language Models (LLMs) to intelligently process emails, detect intent, extract entities, and automatically execute workflows such as sending replies, creating tasks, and saving attachments.

**Key Features:**
- 🧠 **AI-Powered Analysis**: Uses OpenAI GPT to understand email intent and extract information
- 📧 **Gmail Integration**: Seamlessly fetch and process emails from Gmail
- ⚡ **Automated Workflows**: Auto-reply, task creation, and attachment handling
- 📊 **Web Dashboard**: Beautiful Streamlit interface for monitoring and control
- 🔌 **REST API**: Clean, well-documented API for integration
- 🛡️ **Production-Ready**: Error handling, validation, and comprehensive logging

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (optional - works in mock mode)
- Gmail API credentials (optional - works in mock mode)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-email-automation-agent.git
cd ai-email-automation-agent

# Install dependencies
pip install -r requirements.txt
```

### Running the System

**1. Start the API Server:**
```bash
python api/server.py
```

**2. Start the Web Dashboard:**
```bash
streamlit run dashboard/dashboard.py
```

**3. Open your browser:**
```
http://localhost:8501
```

## 📖 Usage Examples

### Process a Single Email

```bash
curl -X POST http://localhost:5000/process_email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "client@example.com",
    "subject": "Urgent: Need Help",
    "body": "I need assistance with the project immediately."
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:5000/process_email",
    json={
        "sender": "client@example.com",
        "subject": "Project Update Request",
        "body": "Hi, I need an update on the project status."
    }
)

result = response.json()
print(f"Intent: {result['decision']['intent']}")
print(f"Priority: {result['decision']['priority']}")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      Streamlit Web Dashboard            │
└──────────────────┬──────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────┐
│         Flask REST API                  │
└──┬──────────┬──────────┬────────────────┘
   │          │          │
┌──▼──┐  ┌───▼───┐  ┌───▼──────────┐
│Email│  │Decision│  │  Workflow    │
│Proc.│  │ Engine │  │  Executor    │
└──┬──┘  └───┬───┘  └───┬──────────┘
   └──────────┴──────────┘
              │
      ┌───────▼────────┐
      │  SQLite DB     │
      └────────────────┘
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/process_email` | Process a single email |
| `POST` | `/run_agent` | Fetch and process multiple emails |
| `GET` | `/history` | Get email processing history |
| `GET` | `/tasks` | Get created tasks |
| `GET` | `/workflow_logs` | Get workflow execution logs |

## 🛠️ Tech Stack

- **Backend**: Flask, Python 3.10+
- **AI/ML**: OpenAI GPT-4
- **Database**: SQLite
- **Frontend**: Streamlit
- **APIs**: Gmail API, OpenAI API
- **Validation**: Pydantic

## 📁 Project Structure

```
ai-email-automation-agent/
├── agent/              # Core agent modules
│   ├── email_processor.py
│   ├── decision_engine.py
│   ├── workflow_executor.py
│   └── utils.py
├── api/                # REST API
│   └── server.py
├── dashboard/          # Web dashboard
│   └── dashboard.py
├── config/             # Configuration
│   └── settings.json
└── storage/            # Data storage
    └── logs.db
```

## 🎨 Features

### Web Dashboard
- 📊 Real-time analytics and insights
- 📧 Email processing visualization
- ✅ Task management interface
- 📝 Workflow execution logs
- ⚙️ Manual agent controls

### API Features
- ✅ Request/response validation
- ✅ Comprehensive error handling
- ✅ Clean, consistent responses
- ✅ Detailed documentation

### AI Capabilities
- 🧠 Intent detection (reply, summarize, create_task, ignore)
- 📊 Priority classification (low, medium, high, urgent)
- 🔍 Entity extraction (client names, request types, deadlines)
- 💬 AI-generated email replies

## 🔧 Configuration

Edit `config/settings.json` to customize:

```json
{
  "llm": {
    "model": "gpt-4",
    "temperature": 0.3
  },
  "workflows": {
    "auto_reply_enabled": true,
    "auto_task_creation_enabled": true
  }
}
```

## 📝 License

This project is licensed under the MIT License.

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) and [Streamlit](https://streamlit.io/)
- AI powered by [OpenAI](https://openai.com/)
- Gmail integration via [Google API Client](https://github.com/googleapis/google-api-python-client)

---

⭐ **Star this repo if you find it useful!**
