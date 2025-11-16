"""
Custom exception classes for the AI Automation Agent.

This module defines custom exceptions for better error handling
and more descriptive error messages throughout the application.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass


class ConfigurationError(AgentError):
    """Raised when there's an issue with configuration."""
    pass


class EmailProcessingError(AgentError):
    """Raised when email processing fails."""
    pass


class DecisionEngineError(AgentError):
    """Raised when the decision engine encounters an error."""
    pass


class WorkflowExecutionError(AgentError):
    """Raised when workflow execution fails."""
    pass


class DatabaseError(AgentError):
    """Raised when database operations fail."""
    pass


class LLMAPIError(AgentError):
    """Raised when LLM API calls fail."""
    pass


class GmailAPIError(AgentError):
    """Raised when Gmail API operations fail."""
    pass

