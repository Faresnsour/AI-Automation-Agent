"""
AI Automation Agent - Core Agent Module

This package contains the core components of the AI Automation Agent:
- EmailProcessor: Gmail API integration
- DecisionEngine: LLM-powered intent detection
- WorkflowExecutor: Automated workflow execution
- Utils: Database and utility functions
"""

from agent.email_processor import EmailProcessor
from agent.decision_engine import DecisionEngine
from agent.workflow_executor import WorkflowExecutor
from agent.utils import DatabaseManager, EmailLog, Task, load_config
from agent.exceptions import (
    AgentError,
    ConfigurationError,
    EmailProcessingError,
    DecisionEngineError,
    WorkflowExecutionError,
    DatabaseError,
    LLMAPIError,
    GmailAPIError
)

__all__ = [
    "EmailProcessor",
    "DecisionEngine",
    "WorkflowExecutor",
    "DatabaseManager",
    "EmailLog",
    "Task",
    "load_config",
    "AgentError",
    "ConfigurationError",
    "EmailProcessingError",
    "DecisionEngineError",
    "WorkflowExecutionError",
    "DatabaseError",
    "LLMAPIError",
    "GmailAPIError"
]

