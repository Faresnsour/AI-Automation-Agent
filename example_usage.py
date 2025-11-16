"""
Example usage script for AI Automation Agent.

This script demonstrates how to use the agent programmatically.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import (
    EmailProcessor,
    DecisionEngine,
    WorkflowExecutor,
    DatabaseManager,
    EmailLog,
    load_config
)


def main():
    """Example usage of the AI Automation Agent."""
    
    print("🤖 AI Automation Agent - Example Usage\n")
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config("config/settings.json")
    
    # Initialize components
    print("🔧 Initializing components...")
    email_processor = EmailProcessor(config)
    decision_engine = DecisionEngine(config)
    
    storage_config = config.get("storage", {})
    db_path = storage_config.get("database_path", "storage/logs.db")
    db_manager = DatabaseManager(db_path)
    
    workflow_executor = WorkflowExecutor(
        config=config,
        email_processor=email_processor,
        decision_engine=decision_engine,
        db_manager=db_manager
    )
    
    print("✅ Components initialized!\n")
    
    # Example 1: Process a custom email
    print("=" * 60)
    print("Example 1: Processing a Custom Email")
    print("=" * 60)
    
    test_email = {
        "id": "example_001",
        "thread_id": "thread_001",
        "sender": "client@example.com",
        "subject": "Urgent: Need Project Update",
        "body": "Hi, I urgently need an update on the project status. Can you provide a summary by end of day?",
        "attachments": [],
        "date": "2024-01-15T10:00:00"
    }
    
    print(f"\n📧 Email Details:")
    print(f"   From: {test_email['sender']}")
    print(f"   Subject: {test_email['subject']}")
    print(f"   Body: {test_email['body'][:50]}...")
    
    # Analyze email
    print("\n🧠 Analyzing email with AI...")
    decision = decision_engine.analyze_email(test_email)
    
    print(f"\n✅ Decision Results:")
    print(f"   Intent: {decision['intent'].upper()}")
    print(f"   Priority: {decision['priority'].upper()}")
    print(f"   Confidence: {decision.get('confidence', 0) * 100:.1f}%")
    print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
    print(f"   Workflow Actions: {decision.get('workflow_actions', [])}")
    
    if decision.get('entities'):
        print(f"\n📊 Extracted Entities:")
        entities = decision['entities']
        print(f"   Client Name: {entities.get('client_name', 'N/A')}")
        print(f"   Request Type: {entities.get('request_type', 'N/A')}")
        print(f"   Urgency Indicators: {entities.get('urgency_indicators', [])}")
    
    # Execute workflow
    print("\n⚙️ Executing workflow...")
    execution_results = workflow_executor.execute_workflow(test_email, decision)
    
    print(f"\n✅ Execution Results:")
    print(f"   Actions Executed: {len(execution_results.get('actions_executed', []))}")
    print(f"   Actions Failed: {len(execution_results.get('actions_failed', []))}")
    
    for action in execution_results.get('actions_executed', []):
        print(f"   - {action.get('action', 'unknown')}: {action.get('status', 'unknown')}")
    
    # Log email
    email_log = EmailLog(
        email_id=test_email["id"],
        sender=test_email["sender"],
        subject=test_email["subject"],
        intent=decision.get("intent", "ignore"),
        priority=decision.get("priority", "medium"),
        decision=decision.get("reasoning", ""),
        timestamp=decision.get("timestamp"),
        processed=True,
        workflow_actions=execution_results.get("actions_executed", [])
    )
    db_manager.log_email(email_log)
    print("\n💾 Email logged to database")
    
    # Example 2: View history
    print("\n" + "=" * 60)
    print("Example 2: Viewing Email History")
    print("=" * 60)
    
    history = db_manager.get_email_history(limit=5)
    print(f"\n📜 Found {len(history)} email(s) in history:")
    for email in history:
        print(f"   - {email.get('subject', 'No Subject')} ({email.get('intent', 'unknown')})")
    
    # Example 3: View tasks
    print("\n" + "=" * 60)
    print("Example 3: Viewing Created Tasks")
    print("=" * 60)
    
    tasks = db_manager.get_tasks()
    print(f"\n✅ Found {len(tasks)} task(s):")
    for task in tasks:
        print(f"   - {task.get('title', 'No Title')} (Priority: {task.get('priority', 'N/A')})")
    
    print("\n" + "=" * 60)
    print("✨ Example completed successfully!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Start the API server: python api/server.py")
    print("   2. Start the dashboard: streamlit run dashboard/dashboard.py")
    print("   3. Check the README.md for more information")


if __name__ == "__main__":
    main()

