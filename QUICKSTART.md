# Quick Start Guide

Get the AI Automation Agent up and running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.10+ installed (`python3 --version`)
- [ ] Gmail account with API access
- [ ] OpenAI API key (optional - system works in mock mode without it)

## Step 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure Gmail API (Optional)

If you want to use real Gmail integration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download and save as `config/gmail_credentials.json`

**Note:** The system works in mock mode without Gmail credentials!

## Step 3: Set OpenAI API Key (Optional)

```bash
export OPENAI_API_KEY="your-key-here"
```

**Note:** The system works in mock mode without OpenAI API key!

## Step 4: Start the API Server

```bash
# Option 1: Use the script
./run_api.sh

# Option 2: Direct command
python api/server.py
```

The API will start on `http://localhost:5000`

## Step 5: Start the Dashboard

In a new terminal:

```bash
# Option 1: Use the script
./run_dashboard.sh

# Option 2: Direct command
streamlit run dashboard/dashboard.py
```

The dashboard will open at `http://localhost:8501`

## Step 6: Test the System

### Option A: Use the Dashboard

1. Open `http://localhost:8501`
2. Go to "⚙️ Run Agent" tab
3. Click "Process Custom Email"
4. Enter test email details:
   - Sender: `test@example.com`
   - Subject: `Urgent: Need Help`
   - Body: `Hi, I urgently need assistance with the project.`
5. Click "Process Email"
6. View the AI decision and results!

### Option B: Use the API

```bash
curl -X POST http://localhost:5000/process_email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "client@example.com",
    "subject": "Project Update Request",
    "body": "Hi, I need an update on the project status."
  }'
```

## What's Next?

- Check the [README.md](README.md) for full documentation
- Explore the dashboard features
- Customize `config/settings.json` for your needs
- Set up real Gmail and OpenAI integrations for production use

## Troubleshooting

### API won't start
- Check if port 5000 is available
- Verify Python version is 3.10+
- Check that all dependencies are installed

### Dashboard won't start
- Check if port 8501 is available
- Verify Streamlit is installed: `pip install streamlit`

### Mock Mode
- The system automatically runs in mock mode if Gmail/OpenAI credentials are missing
- This is perfect for testing and development
- Mock mode provides realistic sample data

## Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review API endpoints in the README
- Check logs in the terminal for error messages

Happy automating! 🚀

