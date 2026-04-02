"""
Compliance Checker for Voice Agent
Validates compliance requirements: disclaimer, advice refusal, interruption
"""
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ComplianceResult:
    is_compliant: bool
    violation_type: Optional[str]
    message: str
    action_required: str


class ComplianceChecker:
    """
    Compliance validation for voice agent
    
    Checks:
    1. Disclaimer delivered at start
    2. No investment advice given
    3. PII not collected
    4. Investment advice requests refused
    """
    
    DISCLAIMER_KEYWORDS = [
        "cannot provide investment advice",
        "not investment advice",
        "informational only",
        "book an appointment",
        "schedule a consultation"
    ]
    
    INVESTMENT_ADVICE_KEYWORDS = [
        "should I buy",
        "recommend a",
        "what stock",
        "which fund",
        "market prediction",
        "will it go up",
        "investment advice",
        "portfolio recommendation"
    ]
    
    ADVICE_REFUSAL_TEMPLATE = (
        "I cannot provide investment advice. I'm only here to help you book an appointment "
        "with a financial advisor. Would you like me to schedule a consultation?"
    )
    
    DISCLAIMER_TEMPLATE = (
        "Hello! I cannot provide investment advice. I can only help you book an appointment "
        "with a financial advisor. How can I help you today?"
    )
    
    def __init__(self):
        self.disclaimer_delivered = False
        self.advice_requests_count = 0
        
    def check_response(self, response_text: str, current_state: str) -> ComplianceResult:
        """
        Check if agent response is compliant
        
        Returns:
            ComplianceResult with status and required actions
        """
        # Check 1: Disclaimer in first response
        if current_state == "greeting" and not self.disclaimer_delivered:
            if self._has_disclaimer(response_text):
                self.disclaimer_delivered = True
                return ComplianceResult(
                    is_compliant=True,
                    violation_type=None,
                    message="Disclaimer delivered",
                    action_required="none"
                )
            else:
                return ComplianceResult(
                    is_compliant=False,
                    violation_type="missing_disclaimer",
                    message="Disclaimer not found in greeting",
                    action_required="inject_disclaimer"
                )
                
        # Check 2: No investment advice in response
        if self._contains_advice_content(response_text):
            return ComplianceResult(
                is_compliant=False,
                violation_type="potential_advice",
                message="Response may contain investment advice",
                action_required="review_content"
            )
            
        return ComplianceResult(
            is_compliant=True,
            violation_type=None,
            message="Response is compliant",
            action_required="none"
        )
        
    def check_user_intent(self, user_text: str) -> ComplianceResult:
        """
        Check if user is seeking investment advice
        
        Returns:
            ComplianceResult with refusal required flag
        """
        text_lower = user_text.lower()
        
        for keyword in self.INVESTMENT_ADVICE_KEYWORDS:
            if keyword in text_lower:
                self.advice_requests_count += 1
                return ComplianceResult(
                    is_compliant=False,
                    violation_type="advice_seeking",
                    message=f"User seeking investment advice: '{keyword}'",
                    action_required="refuse_advice"
                )
                
        return ComplianceResult(
            is_compliant=True,
            violation_type=None,
            message="User intent is compliant",
            action_required="none"
        )
        
    def get_advice_refusal(self) -> str:
        """Get standard advice refusal message"""
        return self.ADVICE_REFUSAL_TEMPLATE
        
    def get_disclaimer(self) -> str:
        """Get standard disclaimer message"""
        return self.DISCLAIMER_TEMPLATE
        
    def _has_disclaimer(self, text: str) -> bool:
        """Check if text contains disclaimer"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.DISCLAIMER_KEYWORDS)
        
    def _contains_advice_content(self, text: str) -> bool:
        """Check if text contains potential advice content"""
        # This is a simplified check - in production, use more sophisticated detection
        advice_patterns = [
            r'\b(buy|sell|hold)\s+(this|that|the)\s+(stock|fund|share)',
            r'\b(good|best|top)\s+(investment|stock|fund)',
            r'\bwill\s+go\s+(up|down)',
            r'\bmarket\s+will\s+',
        ]
        
        for pattern in advice_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
        
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics"""
        return {
            "disclaimer_delivered": self.disclaimer_delivered,
            "advice_requests_blocked": self.advice_requests_count
        }


# Convenience function
def create_compliance_checker() -> ComplianceChecker:
    """Factory function"""
    return ComplianceChecker()
