"""
Email processing module for Gmail API integration.

This module handles fetching, reading, and parsing emails from Gmail
using the Gmail API. It provides functionality to retrieve emails,
extract content, and parse attachments.
"""

import os
import base64
import logging
import re
from typing import List, Dict, Optional, Any
from email.mime.text import MIMEText
from datetime import datetime

from agent.exceptions import GmailAPIError, EmailProcessingError

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logging.warning("Gmail API libraries not available. Using mock mode.")


logger = logging.getLogger(__name__)


class EmailProcessor:
    """Handles Gmail API operations for fetching and processing emails."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email processor.
        
        Args:
            config: Configuration dictionary containing Gmail API settings
        """
        self.config = config
        self.gmail_config = config.get("gmail", {})
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Gmail API or set up mock mode."""
        if not GMAIL_AVAILABLE:
            logger.warning("Gmail API not available. Running in mock mode.")
            return
        
        creds = None
        token_file = self.gmail_config.get("token_file", "config/gmail_token.json")
        credentials_file = self.gmail_config.get("credentials_file", "config/gmail_credentials.json")
        scopes = self.gmail_config.get("scopes", [])
        
        # Load existing token
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, scopes)
            except Exception as e:
                logger.warning(f"Error loading token: {e}")
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if os.path.exists(credentials_file):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            credentials_file, scopes
                        )
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        logger.warning(f"Error authenticating: {e}. Running in mock mode.")
                        return
                else:
                    logger.warning(f"Credentials file not found: {credentials_file}. Running in mock mode.")
                    return
            
            # Save credentials for next run
            try:
                os.makedirs(os.path.dirname(token_file), exist_ok=True)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.warning(f"Error saving token: {e}")
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authenticated successfully")
        except Exception as e:
            logger.warning(f"Error building Gmail service: {e}. Running in mock mode.")
    
    def fetch_emails(self, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail inbox.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries with parsed content
        """
        if not self.service:
            return self._fetch_mock_emails(max_results or 5)
        
        try:
            max_results = max_results or self.gmail_config.get("max_emails_per_fetch", 10)
            
            # Fetch message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='is:unread'
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                try:
                    email_data = self._get_email_details(msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {msg['id']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(emails)} emails")
            return emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific email.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with email details or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Extract attachments
            attachments = self._extract_attachments(message['payload'], message_id)
            
            return {
                'id': message_id,
                'thread_id': message.get('threadId', ''),
                'sender': sender,
                'subject': subject,
                'body': body,
                'date': date,
                'attachments': attachments,
                'snippet': message.get('snippet', ''),
                'raw': message
            }
        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.
        
        Args:
            payload: Email payload from Gmail API
            
        Returns:
            Email body text
        """
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif mime_type == 'text/html' and not body:
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            mime_type = payload.get('mimeType', '')
            if mime_type in ['text/plain', 'text/html']:
                data = payload.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body or "No body content"
    
    def _extract_attachments(self, payload: Dict[str, Any], message_id: str) -> List[Dict[str, Any]]:
        """
        Extract attachment information from email payload.
        
        Args:
            payload: Email payload from Gmail API
            message_id: Gmail message ID
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        def extract_from_parts(parts: List[Dict[str, Any]]) -> None:
            for part in parts:
                if part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': part.get('mimeType', ''),
                        'size': part.get('body', {}).get('size', 0),
                        'attachment_id': part.get('body', {}).get('attachmentId', ''),
                        'message_id': message_id
                    })
                if 'parts' in part:
                    extract_from_parts(part['parts'])
        
        if 'parts' in payload:
            extract_from_parts(payload['parts'])
        
        return attachments
    
    def download_attachment(
        self, 
        message_id: str, 
        attachment_id: str, 
        filename: str,
        save_path: str
    ) -> Optional[str]:
        """
        Download an attachment from Gmail.
        
        Args:
            message_id: Gmail message ID
            attachment_id: Gmail attachment ID
            filename: Name of the file
            save_path: Directory to save the attachment
            
        Returns:
            Path to saved file or None if error
        """
        if not self.service:
            return self._mock_download_attachment(filename, save_path)
        
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            os.makedirs(save_path, exist_ok=True)
            
            file_path = os.path.join(save_path, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Downloaded attachment: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading attachment: {e}")
            return None
    
    def send_reply(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> bool:
        """
        Send an email reply via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            thread_id: Optional thread ID to reply in thread
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            EmailProcessingError: If sending fails and service is available
        """
        if not self.service:
            logger.info(f"[MOCK] Would send reply to {to}: {subject}")
            return True
        
        # Validate email address format
        if not self._is_valid_email(to):
            logger.error(f"Invalid email address: {to}")
            raise EmailProcessingError(f"Invalid email address: {to}")
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if thread_id:
                message['In-Reply-To'] = thread_id
                message['References'] = thread_id
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_message = {'raw': raw_message}
            if thread_id:
                send_message['threadId'] = thread_id
            
            self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()
            
            logger.info(f"Sent reply to {to}")
            return True
            
        except HttpError as e:
            logger.error(f"Gmail API error sending reply: {e}")
            raise GmailAPIError(f"Failed to send reply: {e}") from e
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            raise EmailProcessingError(f"Failed to send reply: {e}") from e
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _fetch_mock_emails(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate mock emails for testing when Gmail API is not available.
        
        Args:
            count: Number of mock emails to generate
            
        Returns:
            List of mock email dictionaries
        """
        mock_emails = [
            {
                'id': f'mock_{i}',
                'thread_id': f'thread_{i}',
                'sender': f'client{i}@example.com',
                'subject': f'Request for Project Update - Email {i}',
                'body': f'Hi, I need an update on the project status. Can you provide a summary? This is mock email {i}.',
                'date': datetime.now().isoformat(),
                'attachments': [{'filename': f'document_{i}.pdf', 'mime_type': 'application/pdf', 'size': 1024}] if i % 2 == 0 else [],
                'snippet': f'Request for project update - mock email {i}'
            }
            for i in range(1, count + 1)
        ]
        logger.info(f"Generated {len(mock_emails)} mock emails")
        return mock_emails
    
    def _mock_download_attachment(self, filename: str, save_path: str) -> Optional[str]:
        """
        Mock attachment download for testing.
        
        Args:
            filename: Name of the file
            save_path: Directory to save the attachment
            
        Returns:
            Path to saved file
        """
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, filename)
        
        # Create a mock file
        with open(file_path, 'w') as f:
            f.write(f"Mock attachment content for {filename}")
        
        logger.info(f"[MOCK] Created attachment: {file_path}")
        return file_path

