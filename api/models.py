"""
Pydantic models for API request/response validation.

This module defines data models for request validation and response formatting
to ensure type safety and data integrity in the API layer.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator


class ProcessEmailRequest(BaseModel):
    """Request model for processing a single email."""
    email_id: Optional[str] = None
    thread_id: Optional[str] = None
    sender: EmailStr = Field(..., description="Sender email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="List of attachments")
    date: Optional[str] = None

    @validator('subject')
    def validate_subject(cls, v):
        """Ensure subject is not just whitespace."""
        if not v.strip():
            raise ValueError("Subject cannot be empty or whitespace only")
        return v.strip()

    @validator('body')
    def validate_body(cls, v):
        """Ensure body is not just whitespace."""
        if not v.strip():
            raise ValueError("Body cannot be empty or whitespace only")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "sender": "client@example.com",
                "subject": "Project Update Request",
                "body": "Hi, I need an update on the project status.",
                "attachments": []
            }
        }


class RunAgentRequest(BaseModel):
    """Request model for running the agent."""
    max_emails: int = Field(default=10, ge=1, le=100, description="Maximum number of emails to process")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "max_emails": 10
            }
        }


class APIResponse(BaseModel):
    """Base response model for API endpoints."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }


class HealthResponse(APIResponse):
    """Health check response model."""
    status: str
    service: str
    version: str

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "status": "healthy",
                "service": "AI Automation Agent API",
                "version": "1.0.0"
            }
        }

