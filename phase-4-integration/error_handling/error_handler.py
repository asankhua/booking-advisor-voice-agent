"""
Error Handler for Voice Agent
Graceful error handling and human handoff
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """
    Global error handling for voice agent
    
    Strategies:
    - Low: Retry once, then continue
    - Medium: Inform user, continue
    - High: Graceful degradation to human
    - Critical: Immediate handoff
    """
    
    HUMAN_HANDOFF_MESSAGE = (
        "I'm having trouble understanding. Let me connect you with a human agent "
        "who can help you right away. Please hold."
    )
    
    RETRY_MESSAGE = (
        "I didn't catch that. Could you please repeat?"
    )
    
    FALLBACK_MESSAGES = {
        "stt_failure": "I didn't hear that clearly. Could you speak a bit louder?",
        "llm_timeout": "I'm thinking... just a moment.",
        "tts_failure": "I've got your booking details. Please check the screen.",
        "mcp_failure": "I'm having trouble with the booking system. Let me try again.",
        "network_error": "Connection seems slow. Working on it...",
        "unknown": "I apologize, something went wrong. Could you try again?"
    }
    
    def __init__(self, handoff_number: Optional[str] = None):
        self.handoff_number = handoff_number
        self.error_counts = {}
        self.max_retries = 3
        
    def handle(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle error and return recovery action
        
        Returns:
            Dict with action, message, and handoff flag
        """
        error_type = type(error).__name__
        severity = self._classify_error(error)
        
        logger.error(f"Error: {error_type} | Severity: {severity.value} | Context: {context}")
        
        # Count errors per conversation
        conv_id = context.get("conversation_id", "unknown")
        if conv_id not in self.error_counts:
            self.error_counts[conv_id] = 0
        self.error_counts[conv_id] += 1
        
        # Check if too many errors
        if self.error_counts[conv_id] >= self.max_retries:
            return self._trigger_handoff("Too many errors")
            
        # Handle based on severity
        if severity == ErrorSeverity.CRITICAL:
            return self._trigger_handoff(str(error))
            
        elif severity == ErrorSeverity.HIGH:
            return {
                "action": "graceful_degradation",
                "message": self.FALLBACK_MESSAGES.get("unknown"),
                "handoff": False,
                "retry": False
            }
            
        elif severity == ErrorSeverity.MEDIUM:
            return {
                "action": "retry",
                "message": self.RETRY_MESSAGE,
                "handoff": False,
                "retry": True
            }
            
        else:  # LOW
            return {
                "action": "continue",
                "message": None,
                "handoff": False,
                "retry": True
            }
            
    def _classify_error(self, error: Exception) -> ErrorSeverity:
        """Classify error severity"""
        error_type = type(error).__name__
        
        critical_errors = ["SystemExit", "KeyboardInterrupt"]
        high_errors = ["ConnectionError", "TimeoutError", "RuntimeError"]
        medium_errors = ["ValueError", "KeyError", "AttributeError"]
        
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
            
    def _trigger_handoff(self, reason: str) -> Dict[str, Any]:
        """Trigger human handoff"""
        logger.warning(f"Human handoff triggered: {reason}")
        
        return {
            "action": "human_handoff",
            "message": self.HUMAN_HANDOFF_MESSAGE,
            "handoff": True,
            "retry": False,
            "handoff_number": self.handoff_number
        }
        
    def get_error_message(self, error_type: str) -> str:
        """Get user-friendly error message"""
        return self.FALLBACK_MESSAGES.get(error_type, self.FALLBACK_MESSAGES["unknown"])
        
    def reset_error_count(self, conversation_id: str):
        """Reset error count for conversation"""
        if conversation_id in self.error_counts:
            del self.error_counts[conversation_id]


# Convenience function
def create_error_handler() -> ErrorHandler:
    """Factory function"""
    import os
    handoff_number = os.getenv("HUMAN_HANDOFF_NUMBER")
    return ErrorHandler(handoff_number=handoff_number)
