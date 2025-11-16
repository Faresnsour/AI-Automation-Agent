"""
Modern Web Dashboard for AI Automation Agent.

A beautiful, user-friendly interface for managing email automation.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import load_config


# Page configuration
st.set_page_config(
    page_title="AI Automation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Load configuration
config = load_config("config/settings.json")
api_config = config.get("api", {}) if config else {}
API_BASE_URL = f"http://{api_config.get('host', 'localhost')}:{api_config.get('port', 5000)}"


def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def fetch_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch email processing history from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/history", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json().get("history", [])
        return []
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []


def fetch_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch tasks from API."""
    try:
        params = {"status": status} if status else {}
        response = requests.get(f"{API_BASE_URL}/tasks", params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get("tasks", [])
        return []
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")
        return []


def fetch_workflow_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch workflow logs from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/workflow_logs", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json().get("logs", [])
        return []
    except Exception as e:
        st.error(f"Error fetching workflow logs: {e}")
        return []


def run_agent(max_emails: int = 10) -> Dict[str, Any]:
    """Trigger agent execution via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/run_agent",
            json={"max_emails": max_emails},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_custom_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a custom email via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/process_email",
            json=email_data,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Main dashboard
def main():
    """Main dashboard function."""
    
    # Header
    st.markdown('<div class="main-header">🤖 AI Automation Agent</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Control Panel")
        
        # API status
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ **API Connected**")
        else:
            st.error("❌ **API Disconnected**")
            st.warning("⚠️ Please start the API server:\n\n`python api/server.py`")
            st.stop()
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📑 Navigation")
        
        # Initialize session state for page navigation
        if "page" not in st.session_state:
            st.session_state.page = "🏠 Home"
        
        page = st.radio(
            "Go to:",
            ["🏠 Home", "📧 Process Email", "🔄 Run Agent", "📊 Analytics", "✅ Tasks", "📝 Logs"],
            index=["🏠 Home", "📧 Process Email", "🔄 Run Agent", "📊 Analytics", "✅ Tasks", "📝 Logs"].index(st.session_state.page) if st.session_state.page in ["🏠 Home", "📧 Process Email", "🔄 Run Agent", "📊 Analytics", "✅ Tasks", "📝 Logs"] else 0,
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        # Update session state when radio changes
        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        history = fetch_history(limit=10)
        if history:
            total = len(history)
            urgent = sum(1 for h in history if h.get("priority") == "urgent")
            st.metric("Recent Emails", total)
            if urgent > 0:
                st.metric("Urgent", urgent, delta="⚠️")
        
        st.markdown("---")
        st.caption("💡 Tip: Use the Run Agent page to automatically process emails from your inbox.")
    
    # Main content area - use session state page
    current_page = st.session_state.get("page", "🏠 Home")
    
    if current_page == "🏠 Home":
        render_home_page()
    elif current_page == "📧 Process Email":
        render_process_email_page()
    elif current_page == "🔄 Run Agent":
        render_run_agent_page()
    elif current_page == "📊 Analytics":
        render_analytics_page()
    elif current_page == "✅ Tasks":
        render_tasks_page()
    elif current_page == "📝 Logs":
        render_logs_page()


def render_home_page():
    """Render the home/dashboard page."""
    st.header("🏠 Dashboard")
    st.markdown("Welcome to AI Automation Agent! Get started by processing an email or running the agent.")
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📧 Process Email")
        st.markdown("Manually process a single email through the AI agent.")
        if st.button("Go to Process Email →", use_container_width=True, type="primary", key="btn_process"):
            st.session_state.page = "📧 Process Email"
            st.rerun()
    
    with col2:
        st.markdown("### 🔄 Run Agent")
        st.markdown("Automatically fetch and process emails from your inbox.")
        if st.button("Go to Run Agent →", use_container_width=True, type="primary", key="btn_run"):
            st.session_state.page = "🔄 Run Agent"
            st.rerun()
    
    with col3:
        st.markdown("### 📊 View Analytics")
        st.markdown("See insights and statistics about processed emails.")
        if st.button("Go to Analytics →", use_container_width=True, type="primary", key="btn_analytics"):
            st.session_state.page = "📊 Analytics"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    history = fetch_history(limit=5)
    
    if not history:
        st.info("👋 No emails processed yet. Start by processing an email or running the agent!")
        return
    
    for email in history:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{email.get('subject', 'No Subject')}**")
                st.caption(f"From: {email.get('sender', 'Unknown')}")
            
            with col2:
                priority = email.get('priority', 'medium')
                if priority == 'urgent':
                    st.error("🔴 URGENT")
                elif priority == 'high':
                    st.warning("🟠 HIGH")
                elif priority == 'medium':
                    st.info("🟡 MEDIUM")
                else:
                    st.success("🟢 LOW")
            
            with col3:
                intent = email.get('intent', 'ignore')
                if intent == 'reply':
                    st.success("💬 REPLY")
                elif intent == 'create_task':
                    st.info("📋 TASK")
                elif intent == 'summarize':
                    st.warning("📄 SUMMARIZE")
                else:
                    st.write("⏭️ IGNORE")
            
            st.markdown("---")


def render_process_email_page():
    """Render the process email page."""
    st.header("📧 Process Email")
    st.markdown("Enter email details below to process it through the AI agent.")
    
    # Email input form
    with st.form("email_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            sender = st.text_input(
                "Sender Email *",
                placeholder="client@example.com",
                help="Email address of the sender"
            )
            subject = st.text_input(
                "Subject *",
                placeholder="Project Update Request",
                help="Email subject line"
            )
        
        with col2:
            email_id = st.text_input(
                "Email ID (Optional)",
                placeholder="Leave empty for auto-generated",
                help="Custom email identifier"
            )
            thread_id = st.text_input(
                "Thread ID (Optional)",
                placeholder="For email threading",
                help="Gmail thread ID if replying"
            )
        
        body = st.text_area(
            "Email Body *",
            placeholder="Enter the email content here...",
            height=200,
            help="The main content of the email"
        )
        
        submitted = st.form_submit_button("🚀 Process Email", type="primary", use_container_width=True)
        
        if submitted:
            if not sender or not subject or not body:
                st.error("❌ Please fill in all required fields (marked with *)")
            else:
                with st.spinner("🤖 Processing email with AI..."):
                    email_data = {
                        "sender": sender,
                        "subject": subject,
                        "body": body
                    }
                    if email_id:
                        email_data["email_id"] = email_id
                    if thread_id:
                        email_data["thread_id"] = thread_id
                    
                    result = process_custom_email(email_data)
                    
                    if result.get("success"):
                        st.success("✅ Email processed successfully!")
                        
                        # Display results
                        decision = result.get("decision", {})
                        execution = result.get("execution_results", {})
                        
                        # Decision summary
                        st.markdown("### 📊 AI Decision")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            intent = decision.get("intent", "unknown").upper()
                            st.metric("Intent", intent)
                        
                        with col2:
                            priority = decision.get("priority", "medium").upper()
                            st.metric("Priority", priority)
                        
                        with col3:
                            confidence = decision.get("confidence", 0) * 100
                            st.metric("Confidence", f"{confidence:.1f}%")
                        
                        with col4:
                            actions = len(execution.get("actions_executed", []))
                            st.metric("Actions", actions)
                        
                        # Reasoning
                        st.markdown("**Reasoning:**")
                        st.info(decision.get("reasoning", "No reasoning provided"))
                        
                        # Entities
                        entities = decision.get("entities", {})
                        if entities:
                            st.markdown("**Extracted Information:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"👤 Client: {entities.get('client_name', 'N/A')}")
                                st.write(f"📋 Request Type: {entities.get('request_type', 'N/A')}")
                            with col2:
                                urgency = entities.get('urgency_indicators', [])
                                if urgency:
                                    st.write(f"⚡ Urgency: {', '.join(urgency)}")
                        
                        # Actions executed
                        if execution.get("actions_executed"):
                            st.markdown("### ⚙️ Actions Executed")
                            for action in execution.get("actions_executed", []):
                                action_type = action.get("action", "unknown")
                                status = action.get("status", "unknown")
                                if status == "success":
                                    st.success(f"✅ {action_type.replace('_', ' ').title()}")
                                else:
                                    st.error(f"❌ {action_type.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")


def render_run_agent_page():
    """Render the run agent page."""
    st.header("🔄 Run Agent")
    st.markdown("Automatically fetch and process emails from your inbox.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **How it works:**
        1. Fetches unread emails from Gmail (or uses mock emails if Gmail is not configured)
        2. Analyzes each email with AI
        3. Executes appropriate workflows (replies, tasks, attachments)
        4. Logs all actions for review
        """)
    
    with col2:
        max_emails = st.number_input(
            "Max Emails",
            min_value=1,
            max_value=100,
            value=10,
            help="Maximum number of emails to process"
        )
    
    st.markdown("---")
    
    if st.button("🚀 Run Agent Now", type="primary", use_container_width=True):
        with st.spinner("🔄 Processing emails..."):
            result = run_agent(max_emails=max_emails)
            
            if result.get("success"):
                processed_count = result.get("processed_count", 0)
                results = result.get("results", [])
                
                if processed_count == 0:
                    st.info("ℹ️ No new emails to process.")
                else:
                    st.success(f"✅ Successfully processed {processed_count} email(s)!")
                    
                    # Show results
                    st.markdown("### 📋 Processing Results")
                    for i, email_result in enumerate(results, 1):
                        with st.expander(f"Email {i}: {email_result.get('subject', 'No Subject')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**From:** {email_result.get('sender', 'Unknown')}")
                                st.write(f"**Subject:** {email_result.get('subject', 'No Subject')}")
                            
                            with col2:
                                decision = email_result.get("decision", {})
                                if decision:
                                    st.write(f"**Intent:** {decision.get('intent', 'N/A').upper()}")
                                    st.write(f"**Priority:** {decision.get('priority', 'N/A').upper()}")
                            
                            if email_result.get("error"):
                                st.error(f"❌ Error: {email_result.get('error')}")
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")


def render_analytics_page():
    """Render the analytics page."""
    st.header("📊 Analytics Dashboard")
    
    history = fetch_history(limit=200)
    
    if not history:
        st.info("📊 No data available yet. Process some emails first!")
        return
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(history)
    high_priority = sum(1 for h in history if h.get("priority") in ["high", "urgent"])
    replied = sum(1 for h in history if h.get("workflow_actions") and "reply" in str(h.get("workflow_actions")))
    tasks_created = sum(1 for h in history if h.get("workflow_actions") and "create_task" in str(h.get("workflow_actions")))
    
    with col1:
        st.metric("Total Emails", total)
    with col2:
        st.metric("High Priority", high_priority)
    with col3:
        st.metric("Replied", replied)
    with col4:
        st.metric("Tasks Created", tasks_created)
    
    st.markdown("---")
    
    # Convert to DataFrame
    df = pd.DataFrame(history)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Intent Distribution")
        if 'intent' in df.columns:
            intent_counts = df['intent'].value_counts()
            st.bar_chart(intent_counts)
    
    with col2:
        st.subheader("📊 Priority Distribution")
        if 'priority' in df.columns:
            priority_counts = df['priority'].value_counts()
            st.bar_chart(priority_counts)
    
    # Time series
    st.subheader("📅 Processing Timeline")
    if 'timestamp' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['timestamp'], errors='coerce')
            daily_counts = df.groupby(df['date'].dt.date).size()
            st.line_chart(daily_counts)
        except:
            st.info("Unable to generate timeline chart")
    
    # Top senders
    st.subheader("👥 Top Senders")
    if 'sender' in df.columns:
        sender_counts = df['sender'].value_counts().head(10)
        st.bar_chart(sender_counts)


def render_tasks_page():
    """Render the tasks page."""
    st.header("✅ Tasks")
    st.markdown("View and manage tasks created by the agent.")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "completed", "in_progress"],
            help="Filter tasks by their status"
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Fetch tasks
    status = None if status_filter == "All" else status_filter
    tasks = fetch_tasks(status=status)
    
    if not tasks:
        st.info("📋 No tasks found.")
        return
    
    st.markdown(f"**Found {len(tasks)} task(s)**")
    st.markdown("---")
    
    # Display tasks
    for task in tasks:
        with st.expander(f"📋 {task.get('title', 'No Title')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:**")
                st.write(task.get('description', 'N/A')[:300] + "..." if len(task.get('description', '')) > 300 else task.get('description', 'N/A'))
                st.markdown(f"**Client:** {task.get('client_name', 'Unknown')}")
                st.markdown(f"**Created:** {task.get('created_at', 'N/A')}")
            
            with col2:
                priority = task.get('priority', 'medium')
                if priority == 'urgent':
                    st.error("🔴 URGENT")
                elif priority == 'high':
                    st.warning("🟠 HIGH")
                elif priority == 'medium':
                    st.info("🟡 MEDIUM")
                else:
                    st.success("🟢 LOW")
                
                status = task.get('status', 'pending')
                st.markdown(f"**Status:** {status.upper()}")


def render_logs_page():
    """Render the logs page."""
    st.header("📝 Workflow Logs")
    st.markdown("View detailed logs of all workflow actions executed by the agent.")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    logs = fetch_workflow_logs(limit=200)
    
    if not logs:
        st.info("📝 No workflow logs found.")
        return
    
    st.markdown(f"**Found {len(logs)} log entry(ies)**")
    st.markdown("---")
    
    # Display logs
    for log in logs:
        status = log.get('status', 'unknown')
        action_type = log.get('action_type', 'unknown')
        timestamp = log.get('timestamp', 'N/A')
        
        if status == 'success':
            st.success(f"✅ [{timestamp}] **{action_type}** - {log.get('email_id', 'N/A')}")
        else:
            st.error(f"❌ [{timestamp}] **{action_type}** - {log.get('error_message', 'Unknown error')}")
        
        # Show details in expander
        with st.expander("View Details"):
            st.json(log)


if __name__ == "__main__":
    main()
