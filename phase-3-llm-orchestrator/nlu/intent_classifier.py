"""
Intent Classifier for Voice Agent
Detects user intent from utterances
"""
import re
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class Intent(Enum):
    BOOK_NEW = "book_new"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    WHAT_TO_PREPARE = "what_to_prepare"
    CHECK_AVAILABILITY = "check_availability"
    INVESTMENT_ADVICE = "investment_advice"  # Compliance flag
    UNKNOWN = "unknown"


@dataclass
class ClassifiedIntent:
    intent: Intent
    confidence: float
    requires_advice_warning: bool
    raw_text: str


class IntentClassifier:
    """
    Rule-based intent classifier with keyword matching
    
    Intents:
    - book_new: "book", "schedule", "make an appointment"
    - reschedule: "reschedule", "change", "move"
    - cancel: "cancel", "delete", "remove"
    - what_to_prepare: "what to bring", "what do I need"
    - check_availability: "when are you free", "what slots"
    - investment_advice: "what stock", "should I buy", "recommend" (flagged)
    """
    
    # Intent patterns
    PATTERNS = {
        Intent.BOOK_NEW: [
            r'\b(book|schedule|make an appointment|set up a meeting|want to meet|need an appointment)\b'
        ],
        Intent.RESCHEDULE: [
            r'\b(reschedule|change|move|different time|another day|can\'t make it)\b'
        ],
        Intent.CANCEL: [
            r'\b(cancel|delete|remove|don\'t need|no longer|not coming)\b'
        ],
        Intent.WHAT_TO_PREPARE: [
            r'\b(what to bring|what do i need|what should i prepare|documents required|what to carry)\b'
        ],
        Intent.CHECK_AVAILABILITY: [
            r'\b(when are you free|what slots|available times|when can i|what days)\b'
        ],
        Intent.INVESTMENT_ADVICE: [
            r'\b(what stock should|should i buy|recommend.*fund|recommend.*stock|invest in|market prediction|which.*fund|best.*investment|which investment|investment is best|will the market|market go up)\b'
        ]
    }
    
    def classify(self, text: str) -> ClassifiedIntent:
        """
        Classify user intent from text
        
        Returns:
            ClassifiedIntent with intent, confidence, and flags
        """
        text_lower = text.lower()
        scores = {}
        
        # Score each intent
        for intent, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            scores[intent] = score
            
        # Get best match
        if max(scores.values()) == 0:
            return ClassifiedIntent(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                requires_advice_warning=False,
                raw_text=text
            )
            
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        total_score = sum(scores.values())
        
        confidence = max_score / total_score if total_score > 0 else 0.0
        
        # Flag investment advice attempts
        requires_warning = best_intent == Intent.INVESTMENT_ADVICE
        
        return ClassifiedIntent(
            intent=best_intent,
            confidence=confidence,
            requires_advice_warning=requires_warning,
            raw_text=text
        )
        
    def is_advice_seeking(self, text: str) -> bool:
        """Quick check for investment advice intent"""
        result = self.classify(text)
        return result.intent == Intent.INVESTMENT_ADVICE
        
    def get_intent_description(self, intent: Intent) -> str:
        """Get human-readable intent description"""
        descriptions = {
            Intent.BOOK_NEW: "Booking a new appointment",
            Intent.RESCHEDULE: "Rescheduling existing appointment",
            Intent.CANCEL: "Cancelling appointment",
            Intent.WHAT_TO_PREPARE: "Asking what to prepare",
            Intent.CHECK_AVAILABILITY: "Checking available slots",
            Intent.INVESTMENT_ADVICE: "Seeking investment advice (BLOCKED)",
            Intent.UNKNOWN: "Unknown intent"
        }
        return descriptions.get(intent, "Unknown")


# Convenience function
def create_intent_classifier() -> IntentClassifier:
    """Factory function"""
    return IntentClassifier()
