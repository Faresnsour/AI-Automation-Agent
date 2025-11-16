"""
Workflow executor for automated email response actions.

This module executes workflows based on AI decisions, including:
- Generating and sending email replies
- Creating tasks in external systems (Notion/Trello/ClickUp)
- Saving attachments
- Logging all actions
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from agent.utils import DatabaseManager, Task, generate_id
from agent.email_processor import EmailProcessor
from agent.decision_engine import DecisionEngine
from agent.exceptions import WorkflowExecutionError


logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes automated workflows based on AI decisions."""
    
    def __init__(
        self, 
        config: Dict[str, Any],
        email_processor: EmailProcessor,
        decision_engine: DecisionEngine,
        db_manager: DatabaseManager
    ):
        """
        Initialize the workflow executor.
        
        Args:
            config: Configuration dictionary
            email_processor: EmailProcessor instance
            decision_engine: DecisionEngine instance
            db_manager: DatabaseManager instance
        """
        self.config = config
        self.email_processor = email_processor
        self.decision_engine = decision_engine
        self.db_manager = db_manager
        self.workflow_config = config.get("workflows", {})
        self.storage_config = config.get("storage", {})
        
        # Ensure attachments directory exists
        attachments_path = self.storage_config.get("attachments_path", "storage/attachments")
        os.makedirs(attachments_path, exist_ok=True)
    
    def execute_workflow(
        self, 
        email: Dict[str, Any], 
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute workflow actions based on decision.
        
        Args:
            email: Email dictionary
            decision: Decision dictionary from DecisionEngine
            
        Returns:
            Dictionary with execution results
        """
        workflow_actions = decision.get("workflow_actions", [])
        execution_results = {
            "email_id": email.get("id"),
            "actions_executed": [],
            "actions_failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Executing workflow for email {email.get('id')}: {workflow_actions}")
        
        # Execute each action
        for action in workflow_actions:
            try:
                if action == "reply" and self.workflow_config.get("auto_reply_enabled", True):
                    result = self._execute_reply(email, decision)
                    execution_results["actions_executed"].append({
                        "action": "reply",
                        "status": "success" if result else "failed",
                        "details": result
                    })
                
                elif action == "create_task" and self.workflow_config.get("auto_task_creation_enabled", True):
                    result = self._execute_create_task(email, decision)
                    execution_results["actions_executed"].append({
                        "action": "create_task",
                        "status": "success" if result else "failed",
                        "details": result
                    })
                
                elif action == "save_attachment" and self.workflow_config.get("save_attachments_enabled", True):
                    result = self._execute_save_attachments(email)
                    execution_results["actions_executed"].append({
                        "action": "save_attachment",
                        "status": "success" if result else "failed",
                        "details": result
                    })
                
                else:
                    logger.info(f"Action '{action}' skipped (disabled or not implemented)")
                    
            except Exception as e:
                logger.error(f"Error executing action '{action}': {e}")
                execution_results["actions_failed"].append({
                    "action": action,
                    "error": str(e)
                })
                self.db_manager.log_workflow_action(
                    email_id=email.get("id", "unknown"),
                    action_type=action,
                    action_details={"error": str(e)},
                    status="failed",
                    error_message=str(e)
                )
        
        return execution_results
    
    def _execute_reply(
        self, 
        email: Dict[str, Any], 
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate and send an email reply.
        
        Args:
            email: Email dictionary
            decision: Decision dictionary
            
        Returns:
            Dictionary with reply execution details
        """
        try:
            # Generate reply using decision engine
            reply_body = self.decision_engine.generate_reply(email, decision)
            
            # Extract recipient from original email
            recipient = self._extract_email_address(email.get("sender", ""))
            if not recipient:
                raise WorkflowExecutionError("Could not extract valid email address from sender")
            
            # Create reply subject
            original_subject = email.get("subject", "")
            reply_subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject
            
            # Send reply
            thread_id = email.get("thread_id")
            success = self.email_processor.send_reply(
                to=recipient,
                subject=reply_subject,
                body=reply_body,
                thread_id=thread_id
            )
            
            if success:
                self.db_manager.log_workflow_action(
                    email_id=email.get("id", "unknown"),
                    action_type="reply",
                    action_details={
                        "recipient": recipient,
                        "subject": reply_subject,
                        "body_preview": reply_body[:100]
                    },
                    status="success"
                )
                logger.info(f"Reply sent successfully to {recipient}")
            
            return {
                "success": success,
                "recipient": recipient,
                "subject": reply_subject,
                "body_preview": reply_body[:100]
            }
            
        except Exception as e:
            logger.error(f"Error executing reply: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _extract_email_address(sender: str) -> Optional[str]:
        """
        Extract email address from sender string.
        Handles formats like "Name <email@example.com>" or "email@example.com".
        
        Args:
            sender: Sender string from email
            
        Returns:
            Extracted email address or None if not found
        """
        if not sender:
            return None
        
        # Try to extract from "Name <email@example.com>" format
        if "<" in sender and ">" in sender:
            match = sender.split("<")[1].split(">")[0]
            return match.strip() if match else None
        
        # Return as-is if it looks like an email
        if "@" in sender:
            return sender.strip()
        
        return None
    
    def _execute_create_task(
        self, 
        email: Dict[str, Any], 
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a task in external system (Notion/Trello/ClickUp).
        
        Args:
            email: Email dictionary
            decision: Decision dictionary
            
        Returns:
            Dictionary with task creation details
        """
        try:
            # Extract task information
            entities = decision.get("entities", {})
            client_name = entities.get("client_name", "Unknown Client")
            request_type = entities.get("request_type", "General Request")
            priority = decision.get("priority", "medium")
            
            # Create task title
            task_title = f"{request_type.replace('_', ' ').title()}: {email.get('subject', 'No Subject')[:50]}"
            
            # Create task description
            task_description = f"""
Email from: {email.get('sender', 'Unknown')}
Subject: {email.get('subject', 'No Subject')}
Priority: {priority.upper()}
Intent: {decision.get('intent', 'unknown')}

Email Body:
{email.get('body', 'No body')[:500]}

Reasoning: {decision.get('reasoning', 'No reasoning provided')}
"""
            
            # Generate task ID
            task_id = generate_id("task_")
            
            # Create task in database
            task = Task(
                task_id=task_id,
                title=task_title,
                description=task_description,
                priority=priority,
                client_name=client_name,
                source_email_id=email.get("id", "unknown"),
                created_at=datetime.now().isoformat(),
                status="pending"
            )
            
            self.db_manager.create_task(task)
            
            # Create task in external system (mock implementation)
            external_task_id = self._create_external_task(task, decision)
            
            self.db_manager.log_workflow_action(
                email_id=email.get("id", "unknown"),
                action_type="create_task",
                action_details={
                    "task_id": task_id,
                    "external_task_id": external_task_id,
                    "title": task_title,
                    "priority": priority
                },
                status="success"
            )
            
            logger.info(f"Task created: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "external_task_id": external_task_id,
                "title": task_title,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_external_task(
        self, 
        task: Task, 
        decision: Dict[str, Any]
    ) -> str:
        """
        Create task in external system (Notion/Trello/ClickUp).
        This is a mock implementation that simulates external API calls.
        
        Args:
            task: Task object
            decision: Decision dictionary
            
        Returns:
            External task ID (mock)
        """
        provider = self.workflow_config.get("task_provider", "notion")
        
        # Mock external task creation
        external_id = f"{provider}_{generate_id()}"
        
        logger.info(f"[MOCK] Created task in {provider}: {external_id}")
        logger.info(f"[MOCK] Task details: {task.title} (Priority: {task.priority})")
        
        # In a real implementation, this would make API calls to:
        # - Notion API: POST /v1/pages
        # - Trello API: POST /1/cards
        # - ClickUp API: POST /v2/list/{list_id}/task
        
        return external_id
    
    def _execute_save_attachments(
        self, 
        email: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save email attachments to local storage.
        
        Args:
            email: Email dictionary
            
        Returns:
            Dictionary with attachment save details
        """
        try:
            attachments = email.get("attachments", [])
            if not attachments:
                return {
                    "success": True,
                    "message": "No attachments to save",
                    "saved_files": []
                }
            
            attachments_path = self.storage_config.get("attachments_path", "storage/attachments")
            saved_files = []
            
            for attachment in attachments:
                try:
                    filename = attachment.get("filename", "unknown")
                    attachment_id = attachment.get("attachment_id")
                    message_id = email.get("id")
                    
                    if attachment_id and message_id:
                        file_path = self.email_processor.download_attachment(
                            message_id=message_id,
                            attachment_id=attachment_id,
                            filename=filename,
                            save_path=attachments_path
                        )
                        
                        if file_path:
                            saved_files.append(file_path)
                            self.db_manager.log_workflow_action(
                                email_id=email.get("id", "unknown"),
                                action_type="save_attachment",
                                action_details={
                                    "filename": filename,
                                    "file_path": file_path
                                },
                                status="success"
                            )
                            logger.info(f"Saved attachment: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error saving attachment {attachment.get('filename', 'unknown')}: {e}")
                    continue
            
            return {
                "success": True,
                "saved_files": saved_files,
                "count": len(saved_files)
            }
            
        except Exception as e:
            logger.error(f"Error executing save attachments: {e}")
            return {"success": False, "error": str(e)}

