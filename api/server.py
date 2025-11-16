"""
Flask REST API server for AI Automation Agent.

This module provides REST API endpoints for:
- Processing emails
- Running the agent
- Retrieving history and tasks
"""

import logging
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any, Tuple
from pydantic import ValidationError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import (
    EmailProcessor,
    DecisionEngine,
    WorkflowExecutor,
    DatabaseManager,
    EmailLog,
    load_config
)
from agent.exceptions import AgentError, DatabaseError
from api.models import (
    ProcessEmailRequest,
    RunAgentRequest,
    HealthResponse,
    APIResponse
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration


class AgentService:
    """Service class to manage agent components."""
    
    def __init__(self):
        """Initialize agent service with all components."""
        self.config: Dict[str, Any] = {}
        self.email_processor: EmailProcessor = None
        self.decision_engine: DecisionEngine = None
        self.db_manager: DatabaseManager = None
        self.workflow_executor: WorkflowExecutor = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all agent components."""
        if self._initialized:
            return
        
        try:
            # Load configuration
            self.config = load_config("config/settings.json")
            
            # Initialize components
            self.email_processor = EmailProcessor(self.config)
            self.decision_engine = DecisionEngine(self.config)
            
            storage_config = self.config.get("storage", {})
            db_path = storage_config.get("database_path", "storage/logs.db")
            self.db_manager = DatabaseManager(db_path)
            
            self.workflow_executor = WorkflowExecutor(
                config=self.config,
                email_processor=self.email_processor,
                decision_engine=self.decision_engine,
                db_manager=self.db_manager
            )
            
            self._initialized = True
            logger.info("Agent components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized


# Global service instance (initialized on startup)
agent_service = AgentService()


def get_agent_service() -> AgentService:
    """
    Get the agent service instance, initializing if needed.
    
    Returns:
        Initialized AgentService instance
        
    Raises:
        AgentError: If initialization fails
    """
    if not agent_service.is_initialized():
        try:
            agent_service.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize agent service: {e}")
            raise AgentError(f"Service initialization failed: {e}") from e
    return agent_service


def create_error_response(error_message: str, status_code: int = 500, details: Any = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional error details
        
    Returns:
        Tuple of (response dict, status code)
    """
    response = {
        "success": False,
        "error": error_message
    }
    if details:
        response["details"] = details
    return jsonify(response), status_code


def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data dictionary
        status_code: HTTP status code
        
    Returns:
        Tuple of (response dict, status code)
    """
    response = {"success": True, **data}
    return jsonify(response), status_code


def validate_limit_parameter(limit_str: str, default: int = 50, max_limit: int = 1000) -> int:
    """
    Validate and sanitize limit query parameter.
    
    Args:
        limit_str: Limit value from query string
        default: Default value if invalid
        max_limit: Maximum allowed value
        
    Returns:
        Validated limit integer
    """
    try:
        limit = int(limit_str)
        if limit < 1:
            return default
        if limit > max_limit:
            return max_limit
        return limit
    except (ValueError, TypeError):
        return default


def process_single_email(email_data: Dict[str, Any], service: AgentService) -> Dict[str, Any]:
    """
    Process a single email through the AI agent.
    
    Args:
        email_data: Email dictionary
        service: AgentService instance
        
    Returns:
        Dictionary with decision and execution results
    """
    # Create email dictionary with defaults
    email = {
        "id": email_data.get("email_id") or f"api_{hash(str(email_data))}",
        "thread_id": email_data.get("thread_id"),
        "sender": email_data.get("sender", "unknown@example.com"),
        "subject": email_data.get("subject", "No Subject"),
        "body": email_data.get("body", ""),
        "attachments": email_data.get("attachments", []),
        "date": email_data.get("date")
    }
    
    # Analyze email
    decision = service.decision_engine.analyze_email(email)
    
    # Execute workflow
    execution_results = service.workflow_executor.execute_workflow(email, decision)
    
    # Log email processing
    email_log = EmailLog(
        email_id=email["id"],
        sender=email["sender"],
        subject=email["subject"],
        intent=decision.get("intent", "ignore"),
        priority=decision.get("priority", "medium"),
        decision=decision.get("reasoning", ""),
        timestamp=decision.get("timestamp"),
        processed=True,
        workflow_actions=execution_results.get("actions_executed", [])
    )
    service.db_manager.log_email(email_log)
    
    return {
        "email_id": email["id"],
        "decision": decision,
        "execution_results": execution_results
    }


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check() -> Tuple[Dict[str, Any], int]:
    """
    Health check endpoint.
    
    Use this to verify the API is running and ready to process requests.
    
    Returns:
        JSON response with service status
    """
    try:
        service = get_agent_service()
        response = HealthResponse(
            success=True,
            status="healthy",
            service="AI Automation Agent API",
            version="1.0.0"
        )
        return jsonify(response.dict()), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_error_response(
            error_message="Service is not healthy",
            status_code=500,
            details=str(e)
        )


@app.route('/process_email', methods=['POST'])
@app.route('/api/process_email', methods=['POST'])
def process_email() -> Tuple[Dict[str, Any], int]:
    """
    Process a single email through the AI agent.
    
    This endpoint analyzes an email, determines its intent and priority,
    and executes appropriate workflows (reply, create task, save attachments).
    
    Request Body (JSON):
        - sender (required): Email address of the sender
        - subject (required): Email subject line
        - body (required): Email body content
        - email_id (optional): Custom email ID
        - attachments (optional): List of attachment metadata
    
    Returns:
        JSON response with:
        - email_id: Unique identifier for the processed email
        - decision: AI analysis results (intent, priority, entities, reasoning)
        - execution_results: Details of actions taken (replies sent, tasks created, etc.)
    
    Example Request:
        {
            "sender": "client@example.com",
            "subject": "Urgent: Need Project Update",
            "body": "Hi, I need an update on the project status."
        }
    """
    try:
        service = get_agent_service()
        
        # Validate request with Pydantic
        try:
            request_data = ProcessEmailRequest(**request.get_json() or {})
        except ValidationError as e:
            return create_error_response(
                error_message="Invalid request data. Please check sender, subject, and body fields.",
                status_code=400,
                details=e.errors()
            )
        
        # Process email
        result = process_single_email(request_data.dict(), service)
        
        return create_success_response(result, status_code=200)
        
    except AgentError as e:
        logger.error(f"Agent error processing email: {e}")
        return create_error_response(
            error_message=f"Failed to process email: {str(e)}",
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error processing email: {e}")
        return create_error_response(
            error_message="An unexpected error occurred while processing the email",
            status_code=500
        )


@app.route('/run_agent', methods=['POST'])
@app.route('/api/run_agent', methods=['POST'])
def run_agent() -> Tuple[Dict[str, Any], int]:
    """
    Automatically fetch and process new emails from your inbox.
    
    This endpoint fetches unread emails from Gmail (or generates mock emails if Gmail
    is not configured), analyzes each one, and executes appropriate workflows.
    
    Request Body (JSON, optional):
        - max_emails (optional): Maximum number of emails to process (default: 10, max: 100)
    
    Returns:
        JSON response with:
        - processed_count: Number of emails processed
        - results: List of processing results for each email
    
    Example Request:
        {
            "max_emails": 5
        }
    
    Note: If Gmail API is not configured, the system will use mock emails for testing.
    """
    try:
        service = get_agent_service()
        
        # Validate request with Pydantic (use defaults if no body provided)
        try:
            request_data = RunAgentRequest(**request.get_json() or {})
        except ValidationError as e:
            return create_error_response(
                error_message="Invalid request. max_emails must be between 1 and 100.",
                status_code=400,
                details=e.errors()
            )
        
        # Fetch emails
        emails = service.email_processor.fetch_emails(max_results=request_data.max_emails)
        
        if not emails:
            return create_success_response({
                "message": "No new emails to process",
                "processed_count": 0,
                "results": []
            })
        
        # Process each email
        results = []
        for email in emails:
            try:
                result = process_single_email(email, service)
                results.append({
                    "email_id": email.get("id", "unknown"),
                    "subject": email.get("subject", "No Subject"),
                    "sender": email.get("sender", "Unknown"),
                    "decision": result.get("decision"),
                    "execution_results": result.get("execution_results")
                })
            except Exception as e:
                logger.error(f"Error processing email {email.get('id', 'unknown')}: {e}")
                results.append({
                    "email_id": email.get("id", "unknown"),
                    "error": str(e),
                    "status": "failed"
                })
        
        return create_success_response({
            "processed_count": len(results),
            "results": results
        })
        
    except AgentError as e:
        logger.error(f"Agent error running agent: {e}")
        return create_error_response(
            error_message=f"Failed to run agent: {str(e)}",
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error running agent: {e}")
        return create_error_response(
            error_message="An unexpected error occurred while running the agent",
            status_code=500
        )


@app.route('/history', methods=['GET'])
@app.route('/api/history', methods=['GET'])
def get_history() -> Tuple[Dict[str, Any], int]:
    """
    Get email processing history.
    
    Retrieve a list of previously processed emails with their AI decisions
    and workflow execution results.
    
    Query Parameters:
        - limit (optional): Maximum number of records to return (default: 50, max: 1000)
    
    Returns:
        JSON response with:
        - count: Number of records returned
        - history: List of email processing records
    
    Example:
        GET /history?limit=20
    """
    try:
        service = get_agent_service()
        
        # Validate and sanitize limit parameter
        limit = validate_limit_parameter(
            request.args.get("limit", "50"),
            default=50,
            max_limit=1000
        )
        
        history = service.db_manager.get_email_history(limit=limit)
        
        return create_success_response({
            "count": len(history),
            "history": history
        })
        
    except DatabaseError as e:
        logger.error(f"Database error retrieving history: {e}")
        return create_error_response(
            error_message="Failed to retrieve email history from database",
            status_code=500
        )
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        return create_error_response(
            error_message="An unexpected error occurred while retrieving history",
            status_code=500
        )


@app.route('/tasks', methods=['GET'])
@app.route('/api/tasks', methods=['GET'])
def get_tasks() -> Tuple[Dict[str, Any], int]:
    """
    Get tasks created by the agent.
    
    Retrieve a list of tasks that were automatically created from processed emails.
    
    Query Parameters:
        - status (optional): Filter tasks by status (e.g., "pending", "completed", "in_progress")
    
    Returns:
        JSON response with:
        - count: Number of tasks returned
        - tasks: List of task records
    
    Example:
        GET /tasks?status=pending
    """
    try:
        service = get_agent_service()
        
        status = request.args.get("status", type=str)
        tasks = service.db_manager.get_tasks(status=status)
        
        return create_success_response({
            "count": len(tasks),
            "tasks": tasks
        })
        
    except DatabaseError as e:
        logger.error(f"Database error retrieving tasks: {e}")
        return create_error_response(
            error_message="Failed to retrieve tasks from database",
            status_code=500
        )
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        return create_error_response(
            error_message="An unexpected error occurred while retrieving tasks",
            status_code=500
        )


@app.route('/workflow_logs', methods=['GET'])
@app.route('/api/workflow_logs', methods=['GET'])
def get_workflow_logs() -> Tuple[Dict[str, Any], int]:
    """
    Get workflow execution logs.
    
    Retrieve detailed logs of all workflow actions executed by the agent
    (email replies sent, tasks created, attachments saved, etc.).
    
    Query Parameters:
        - limit (optional): Maximum number of records to return (default: 100, max: 1000)
    
    Returns:
        JSON response with:
        - count: Number of log entries returned
        - logs: List of workflow execution log entries
    
    Example:
        GET /workflow_logs?limit=50
    """
    try:
        service = get_agent_service()
        
        # Validate and sanitize limit parameter
        limit = validate_limit_parameter(
            request.args.get("limit", "100"),
            default=100,
            max_limit=1000
        )
        
        logs = service.db_manager.get_workflow_logs(limit=limit)
        
        return create_success_response({
            "count": len(logs),
            "logs": logs
        })
        
    except DatabaseError as e:
        logger.error(f"Database error retrieving workflow logs: {e}")
        return create_error_response(
            error_message="Failed to retrieve workflow logs from database",
            status_code=500
        )
    except Exception as e:
        logger.error(f"Error retrieving workflow logs: {e}")
        return create_error_response(
            error_message="An unexpected error occurred while retrieving workflow logs",
            status_code=500
        )


@app.errorhandler(404)
def not_found(error) -> Tuple[Dict[str, Any], int]:
    """
    Handle 404 errors - endpoint not found.
    
    Returns a helpful error message with available endpoints.
    """
    return create_error_response(
        error_message="Endpoint not found",
        status_code=404,
        details={
            "message": "The requested endpoint does not exist",
            "available_endpoints": [
                "GET /health - Check API health",
                "POST /process_email - Process a single email",
                "POST /run_agent - Fetch and process new emails",
                "GET /history - Get email processing history",
                "GET /tasks - Get created tasks",
                "GET /workflow_logs - Get workflow execution logs"
            ]
        }
    )


@app.errorhandler(500)
def internal_error(error) -> Tuple[Dict[str, Any], int]:
    """
    Handle 500 errors - internal server errors.
    
    Returns a generic error message without exposing internal details.
    """
    return create_error_response(
        error_message="Internal server error",
        status_code=500,
        details="An unexpected error occurred. Please try again later or contact support."
    )


if __name__ == '__main__':
    # Initialize agent on startup
    try:
        agent_service.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Get API config
    api_config = agent_service.config.get("api", {}) if agent_service.config else {}
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 5000)
    debug = api_config.get("debug", False)
    
    logger.info(f"Starting AI Automation Agent API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
