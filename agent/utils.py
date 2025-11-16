"""
Utility functions for the AI Automation Agent.

This module provides helper functions for database operations, logging,
file handling, and common utilities used across the agent system.
"""

import sqlite3
import json
import os
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager

from agent.exceptions import DatabaseError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EmailLog:
    """Data class for email log entries."""
    email_id: str
    sender: str
    subject: str
    intent: str
    priority: str
    decision: str
    timestamp: str
    processed: bool = False
    workflow_actions: Optional[List[str]] = None


@dataclass
class Task:
    """Data class for task entries."""
    task_id: str
    title: str
    description: str
    priority: str
    client_name: Optional[str]
    source_email_id: str
    created_at: str
    status: str = "pending"


class DatabaseManager:
    """Manages SQLite database operations for logs and tasks."""
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
            
        Raises:
            DatabaseError: If database initialization fails
        """
        self.db_path = db_path
        try:
            self._ensure_db_exists()
            self._init_tables()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}") from e
    
    def _ensure_db_exists(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only create directory if path is not just filename
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_tables(self) -> None:
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Email logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE NOT NULL,
                    sender TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    processed BOOLEAN DEFAULT 0,
                    workflow_actions TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT NOT NULL,
                    client_name TEXT,
                    source_email_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Workflow logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            logger.info("Database tables initialized")
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
            
        Raises:
            DatabaseError: If connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()
    
    def log_email(self, email_log: EmailLog) -> None:
        """
        Log an email processing result.
        
        Args:
            email_log: EmailLog instance to save
            
        Raises:
            DatabaseError: If logging fails
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO email_logs 
                    (email_id, sender, subject, intent, priority, decision, timestamp, processed, workflow_actions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    email_log.email_id,
                    email_log.sender,
                    email_log.subject,
                    email_log.intent,
                    email_log.priority,
                    email_log.decision,
                    email_log.timestamp,
                    1 if email_log.processed else 0,
                    json.dumps(email_log.workflow_actions) if email_log.workflow_actions else None
                ))
                conn.commit()
                logger.info(f"Logged email: {email_log.email_id}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Error logging email: {e}")
                raise DatabaseError(f"Failed to log email: {e}") from e
    
    def get_email_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve email processing history.
        
        Args:
            limit: Maximum number of records to return (must be positive)
            
        Returns:
            List of email log dictionaries
            
        Raises:
            DatabaseError: If retrieval fails
            ValueError: If limit is invalid
        """
        if limit < 1:
            raise ValueError("Limit must be a positive integer")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM email_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def create_task(self, task: Task) -> None:
        """
        Create a new task in the database.
        
        Args:
            task: Task instance to save
            
        Raises:
            DatabaseError: If task creation fails
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (task_id, title, description, priority, client_name, source_email_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.task_id,
                    task.title,
                    task.description,
                    task.priority,
                    task.client_name,
                    task.source_email_id,
                    task.status,
                    task.created_at
                ))
                conn.commit()
                logger.info(f"Created task: {task.task_id}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Error creating task: {e}")
                raise DatabaseError(f"Failed to create task: {e}") from e
    
    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve tasks from the database.
        
        Args:
            status: Optional status filter (pending, completed, etc.)
            
        Returns:
            List of task dictionaries
            
        Raises:
            DatabaseError: If retrieval fails
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status = ?
                    ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM tasks 
                    ORDER BY created_at DESC
                ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def log_workflow_action(
        self, 
        email_id: str, 
        action_type: str, 
        action_details: Dict[str, Any], 
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a workflow action execution.
        
        Args:
            email_id: ID of the email that triggered the action
            action_type: Type of action (reply, create_task, save_attachment)
            action_details: Details of the action
            status: Status of the action (success, failed)
            error_message: Optional error message if action failed
            
        Raises:
            DatabaseError: If logging fails
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO workflow_logs 
                    (email_id, action_type, action_details, status, timestamp, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    email_id,
                    action_type,
                    json.dumps(action_details),
                    status,
                    datetime.now().isoformat(),
                    error_message
                ))
                conn.commit()
                logger.info(f"Logged workflow action: {action_type} for {email_id}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Error logging workflow action: {e}")
                raise DatabaseError(f"Failed to log workflow action: {e}") from e
    
    def get_workflow_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve workflow execution logs.
        
        Args:
            limit: Maximum number of records to return (must be positive)
            
        Returns:
            List of workflow log dictionaries
            
        Raises:
            DatabaseError: If retrieval fails
            ValueError: If limit is invalid
        """
        if limit < 1:
            raise ValueError("Limit must be a positive integer")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM workflow_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def load_config(config_path: str = "config/settings.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return {}


def ensure_directory(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"{prefix}{timestamp}{random_suffix}" if prefix else f"{timestamp}{random_suffix}"

