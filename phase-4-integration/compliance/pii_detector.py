"""
PII Detector for Voice Agent
Detects Personally Identifiable Information in real-time
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    PHONE = "phone"
    EMAIL = "email"
    PAN = "pan"
    AADHAAR = "aadhaar"
    ACCOUNT_NUMBER = "account_number"


@dataclass
class PIIDetection:
    pii_type: PIIType
    value: str
    position: tuple  # (start, end)
    confidence: float


class PIIDetector:
    """
    PII Detection with regex patterns for Indian context
    
    Detects:
    - Phone numbers (+91 or 10 digits)
    - Email addresses
    - PAN (ABCDE1234F)
    - Aadhaar (12 digits)
    - Account numbers (9-16 digits)
    """
    
    PATTERNS = {
        PIIType.PHONE: [
            r'\b(\+91[\s-]?)?[6-9]\d{9}\b',
            r'\b(\+91[\s-]?)?\d{5}[\s-]?\d{5}\b'
        ],
        PIIType.EMAIL: [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ],
        PIIType.PAN: [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
        ],
        PIIType.AADHAAR: [
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            r'\b\d{12}\b'
        ],
        PIIType.ACCOUNT_NUMBER: [
            r'\b\d{9,16}\b'
        ]
    }
    
    # Security interrupt messages
    INTERRUPT_MESSAGES = {
        PIIType.PHONE: "For your security, please don't share phone numbers on this call. You can provide contact details securely after receiving your booking confirmation.",
        PIIType.EMAIL: "For your security, please don't share email addresses on this call. You can provide them securely after receiving your booking confirmation.",
        PIIType.PAN: "For your security, please don't share your PAN on this call. You can provide identity documents securely after receiving your booking confirmation.",
        PIIType.AADHAAR: "For your security, please don't share your Aadhaar number on this call. You can provide identity documents securely after receiving your booking confirmation.",
        PIIType.ACCOUNT_NUMBER: "For your security, please don't share account numbers on this call. You can provide banking details securely after receiving your booking confirmation."
    }
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self._compiled = {}
        for pii_type, patterns in self.PATTERNS.items():
            self._compiled[pii_type] = [re.compile(p, re.IGNORECASE) for p in patterns]
            
    def detect(self, text: str) -> List[PIIDetection]:
        """
        Detect PII in text
        
        Returns:
            List of PIIDetection objects
        """
        if not self.enabled or not text:
            return []
            
        detections = []
        
        for pii_type, patterns in self._compiled.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    detection = PIIDetection(
                        pii_type=pii_type,
                        value=match.group(),
                        position=(match.start(), match.end()),
                        confidence=1.0
                    )
                    detections.append(detection)
                    
        return detections
        
    def detect_and_respond(self, text: str) -> Dict[str, Any]:
        """
        Detect PII and return interrupt response if found
        
        Returns:
            Dict with should_interrupt, detections, and message
        """
        detections = self.detect(text)
        
        if not detections:
            return {
                "should_interrupt": False,
                "detections": [],
                "message": None,
                "pii_types": []
            }
            
        # Get unique PII types detected
        pii_types = list(set(d.pii_type for d in detections))
        
        # Use message for first detected type
        primary_message = self.INTERRUPT_MESSAGES.get(pii_types[0], "For your security, please don't share personal details on this call.")
        
        return {
            "should_interrupt": True,
            "detections": [
                {
                    "type": d.pii_type.value,
                    "value": d.value,
                    "position": d.position
                } for d in detections
            ],
            "message": primary_message,
            "pii_types": [p.value for p in pii_types]
        }
        
    def has_pii(self, text: str) -> bool:
        """Quick check if text contains any PII"""
        return len(self.detect(text)) > 0
        
    def get_detected_types(self, text: str) -> List[PIIType]:
        """Get list of PII types detected"""
        detections = self.detect(text)
        return list(set(d.pii_type for d in detections))


# Convenience function
def create_pii_detector() -> PIIDetector:
    """Factory function"""
    return PIIDetector()
