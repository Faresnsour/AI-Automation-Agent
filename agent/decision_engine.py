"""
Decision Engine for AI-powered intent detection and entity extraction.

This module uses LLM (OpenAI GPT) to analyze emails, detect intent,
extract entities, and make decisions about workflow execution.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from agent.exceptions import DecisionEngineError, LLMAPIError

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Using mock mode.")


logger = logging.getLogger(__name__)


class DecisionEngine:
    """AI-powered decision engine for email intent detection and classification."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the decision engine.
        
        Args:
            config: Configuration dictionary containing LLM settings
        """
        self.config = config
        self.llm_config = config.get("llm", {})
        self.model = self.llm_config.get("model", "gpt-4")
        self.temperature = self.llm_config.get("temperature", 0.3)
        self.max_tokens = self.llm_config.get("max_tokens", 1000)
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}. Using mock mode.")
                    self.client = None
            else:
                logger.warning("OPENAI_API_KEY not found. Using mock mode.")
                self.client = None
        else:
            self.client = None
    
    def analyze_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an email and return structured decision data.
        
        Args:
            email: Email dictionary with sender, subject, body, etc.
            
        Returns:
            Dictionary containing intent, priority, entities, and decision
        """
        if not self.client:
            return self._mock_analyze_email(email)
        
        try:
            prompt = self._build_analysis_prompt(email)
            response = self._call_llm(prompt)
            decision = self._parse_llm_response(response, email)
            return decision
        except LLMAPIError as e:
            logger.warning(f"LLM API error, falling back to mock analysis: {e}")
            return self._mock_analyze_email(email)
        except Exception as e:
            logger.error(f"Unexpected error analyzing email: {e}")
            # Fallback to mock analysis for safety
            return self._mock_analyze_email(email)
    
    def _build_analysis_prompt(self, email: Dict[str, Any]) -> str:
        """
        Build the prompt for LLM analysis.
        
        Args:
            email: Email dictionary
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following email and provide a structured JSON response.

Email Details:
- From: {email.get('sender', 'Unknown')}
- Subject: {email.get('subject', 'No Subject')}
- Body: {email.get('body', '')[:1000]}

Please analyze this email and respond with a JSON object containing:
1. "intent": One of ["reply", "summarize", "create_task", "ignore"]
2. "priority": One of ["low", "medium", "high", "urgent"]
3. "entities": Object with:
   - "client_name": Extracted client/contact name (or null)
   - "request_type": Type of request (e.g., "project_update", "meeting_request", "support", etc.)
   - "urgency_indicators": List of urgency keywords found
   - "deadline": Any mentioned deadline (or null)
4. "reasoning": Brief explanation of the decision
5. "workflow_actions": List of actions to take: ["reply", "create_task", "save_attachment", "none"]

Respond ONLY with valid JSON, no additional text.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM API with the prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            LLM response text
            
        Raises:
            LLMAPIError: If API call fails
        """
        if not self.client:
            raise LLMAPIError("OpenAI client not initialized")
        
        try:
            # Use modern OpenAI API (v1.x)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email analysis assistant. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise LLMAPIError("Empty response from LLM API")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            raise LLMAPIError(f"LLM API call failed: {e}") from e
    
    def _parse_llm_response(self, response: str, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM response and structure the decision.
        
        Args:
            response: Raw LLM response
            email: Original email dictionary
            
        Returns:
            Structured decision dictionary
            
        Raises:
            DecisionEngineError: If parsing fails and fallback is not available
        """
        try:
            # Extract JSON from response (handle code blocks)
            cleaned_response = self._extract_json_from_response(response)
            decision_data = json.loads(cleaned_response)
            
            # Ensure required fields with defaults
            decision = {
                "intent": decision_data.get("intent", "ignore"),
                "priority": decision_data.get("priority", "medium"),
                "entities": decision_data.get("entities", {}),
                "reasoning": decision_data.get("reasoning", "No reasoning provided"),
                "workflow_actions": decision_data.get("workflow_actions", []),
                "confidence": decision_data.get("confidence", 0.8),
                "timestamp": datetime.now().isoformat()
            }
            
            # Validate and sanitize intent
            valid_intents = ["reply", "summarize", "create_task", "ignore"]
            if decision["intent"] not in valid_intents:
                logger.warning(f"Invalid intent '{decision['intent']}', defaulting to 'ignore'")
                decision["intent"] = "ignore"
            
            # Validate and sanitize priority
            valid_priorities = ["low", "medium", "high", "urgent"]
            if decision["priority"] not in valid_priorities:
                logger.warning(f"Invalid priority '{decision['priority']}', defaulting to 'medium'")
                decision["priority"] = "medium"
            
            # Validate confidence is between 0 and 1
            if not isinstance(decision["confidence"], (int, float)) or not 0 <= decision["confidence"] <= 1:
                decision["confidence"] = 0.8
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response as JSON: {e}")
            logger.debug(f"Response was: {response[:500]}")
            # Fallback to mock analysis
            logger.info("Falling back to mock analysis due to JSON parsing error")
            return self._mock_analyze_email(email)
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            raise DecisionEngineError(f"Failed to parse LLM response: {e}") from e
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response, handling code blocks and markdown.
        
        Args:
            response: Raw response string
            
        Returns:
            Cleaned JSON string
        """
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Try to find JSON object in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response
    
    def _mock_analyze_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock email analysis for testing when LLM is not available.
        
        Args:
            email: Email dictionary
            
        Returns:
            Mock decision dictionary
        """
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('sender', '')
        
        # Simple rule-based mock analysis
        intent = "ignore"
        priority = "medium"
        workflow_actions = []
        
        if any(word in subject + body for word in ['update', 'status', 'progress']):
            intent = "summarize"
            workflow_actions = ["create_task"]
            priority = "medium"
        elif any(word in subject + body for word in ['urgent', 'asap', 'immediately', 'critical']):
            intent = "reply"
            workflow_actions = ["reply", "create_task"]
            priority = "urgent"
        elif any(word in subject + body for word in ['meeting', 'call', 'schedule']):
            intent = "create_task"
            workflow_actions = ["create_task"]
            priority = "high"
        elif any(word in subject + body for word in ['question', 'help', 'support']):
            intent = "reply"
            workflow_actions = ["reply"]
            priority = "medium"
        
        # Extract client name (simple mock extraction)
        client_name = None
        if '@' in sender:
            client_name = sender.split('@')[0].replace('.', ' ').title()
        
        decision = {
            "intent": intent,
            "priority": priority,
            "entities": {
                "client_name": client_name,
                "request_type": "general_inquiry" if intent == "reply" else "task_request",
                "urgency_indicators": ["mock_analysis"],
                "deadline": None
            },
            "reasoning": f"Mock analysis: Detected intent '{intent}' based on keywords",
            "workflow_actions": workflow_actions,
            "confidence": 0.7,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Mock analysis completed for email: {email.get('id', 'unknown')}")
        return decision
    
    def generate_reply(self, email: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """
        Generate an AI-powered email reply.
        
        Args:
            email: Original email dictionary
            decision: Decision dictionary from analyze_email
            
        Returns:
            Generated reply text
        """
        if not self.client:
            return self._mock_generate_reply(email, decision)
        
        try:
            prompt = self._build_reply_prompt(email, decision)
            response = self._call_llm(prompt)
            return response.strip()
        except LLMAPIError as e:
            logger.warning(f"LLM API error generating reply, using mock reply: {e}")
            return self._mock_generate_reply(email, decision)
        except Exception as e:
            logger.error(f"Unexpected error generating reply: {e}")
            return self._mock_generate_reply(email, decision)
    
    def _build_reply_prompt(self, email: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """
        Build prompt for reply generation.
        
        Args:
            email: Original email dictionary
            decision: Decision dictionary
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate a professional, concise email reply to the following email.

Original Email:
From: {email.get('sender', 'Unknown')}
Subject: {email.get('subject', 'No Subject')}
Body: {email.get('body', '')[:500]}

Context:
- Intent: {decision.get('intent', 'reply')}
- Priority: {decision.get('priority', 'medium')}
- Client: {decision.get('entities', {}).get('client_name', 'Unknown')}

Generate a professional reply that:
1. Acknowledges the email
2. Addresses the main request or question
3. Is concise and actionable
4. Maintains a professional tone

Reply text only, no subject line or headers.
"""
        return prompt
    
    def _mock_generate_reply(self, email: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """
        Generate a mock reply for testing.
        
        Args:
            email: Original email dictionary
            decision: Decision dictionary
            
        Returns:
            Mock reply text
        """
        client_name = decision.get('entities', {}).get('client_name', 'there')
        reply = f"""Hi {client_name},

Thank you for your email. I've received your message regarding "{email.get('subject', 'your request')}".

I'll review this and get back to you shortly. If this is urgent, please don't hesitate to reach out directly.

Best regards,
AI Automation Agent
"""
        return reply

