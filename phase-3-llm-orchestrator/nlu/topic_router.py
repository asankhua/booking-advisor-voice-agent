"""
Topic Router - Maps user utterances to 5 allowed topics
"""
import re
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass


class Topic(Enum):
    KYC_ONBOARDING = "KYC/Onboarding"
    SIP_MANDATES = "SIP/Mandates"
    STATEMENTS_TAX = "Statements/Tax Docs"
    WITHDRAWALS = "Withdrawals & Timelines"
    ACCOUNT_CHANGES = "Account Changes/Nominee"
    UNKNOWN = "Unknown"


@dataclass
class TopicResult:
    topic: Topic
    confidence: float
    booking_code_prefix: str


class TopicRouter:
    """
    Routes user intent to one of 5 allowed topics
    
    Topics:
    - KYC: KYC, onboarding, new account, verification
    - SIP: SIP, mandate, auto-debit, recurring
    - Statements: Statement, tax, capital gains, 1099
    - Withdrawals: Withdrawal, redemption, payout, timeline
    - Account Changes: Nominee, address change, bank change
    """
    
    # Topic patterns with weights
    PATTERNS = {
        Topic.KYC_ONBOARDING: [
            (r'\b(kyc|know your customer|onboard|new account|new customer|first time|verification|verify)\b', 1.0),
            (r'\b(open.*account|create.*account|start.*account)\b', 0.9),
        ],
        Topic.SIP_MANDATES: [
            (r'\b(sip|systematic investment|mandate|auto.*debit|recurring|monthly investment)\b', 1.0),
            (r'\b(set up.*sip|start.*sip|modify.*sip)\b', 0.9),
        ],
        Topic.STATEMENTS_TAX: [
            (r'\b(statement|tax|capital gain|1099|dividend|interest certificate)\b', 1.0),
            (r'\b(tax document|financial statement|annual statement)\b', 0.9),
        ],
        Topic.WITHDRAWALS: [
            (r'\b(withdraw|redemption|payout|take out money|cash out|sell.*fund)\b', 1.0),
            (r'\b(how long.*withdraw|withdrawal timeline|when.*get.*money)\b', 0.9),
        ],
        Topic.ACCOUNT_CHANGES: [
            (r'\b(nominee|change.*address|update.*address|change.*bank|update.*bank)\b', 1.0),
            (r'\b(account.*change|profile.*update|personal.*details)\b', 0.9),
        ]
    }
    
    # Booking code prefixes
    CODE_PREFIXES = {
        Topic.KYC_ONBOARDING: "KY",
        Topic.SIP_MANDATES: "SI",
        Topic.STATEMENTS_TAX: "ST",
        Topic.WITHDRAWALS: "WI",
        Topic.ACCOUNT_CHANGES: "AC"
    }
    
    def route(self, text: str) -> TopicResult:
        """
        Route text to appropriate topic
        
        Returns:
            TopicResult with topic, confidence, and code prefix
        """
        text_lower = text.lower()
        scores = {topic: 0.0 for topic in Topic if topic != Topic.UNKNOWN}
        
        # Score each topic
        for topic, patterns in self.PATTERNS.items():
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, text_lower))
                scores[topic] += matches * weight
                
        # Get best match
        if max(scores.values()) == 0:
            return TopicResult(
                topic=Topic.UNKNOWN,
                confidence=0.0,
                booking_code_prefix="XX"
            )
            
        best_topic = max(scores, key=scores.get)
        max_score = scores[best_topic]
        total_score = sum(scores.values())
        
        confidence = max_score / total_score if total_score > 0 else 0.0
        prefix = self.CODE_PREFIXES.get(best_topic, "XX")
        
        return TopicResult(
            topic=best_topic,
            confidence=confidence,
            booking_code_prefix=prefix
        )
        
    def get_topic_description(self, topic: Topic) -> str:
        """Get topic description"""
        descriptions = {
            Topic.KYC_ONBOARDING: "KYC and new account onboarding",
            Topic.SIP_MANDATES: "SIP setup and mandate management",
            Topic.STATEMENTS_TAX: "Statements and tax documents",
            Topic.WITHDRAWALS: "Withdrawals and payout timelines",
            Topic.ACCOUNT_CHANGES: "Account changes and nominee updates"
        }
        return descriptions.get(topic, "Unknown topic")
        
    def is_allowed_topic(self, text: str) -> bool:
        """Check if text mentions an allowed topic"""
        result = self.route(text)
        return result.topic != Topic.UNKNOWN and result.confidence > 0.5


# Convenience function
def create_topic_router() -> TopicRouter:
    """Factory function"""
    return TopicRouter()
