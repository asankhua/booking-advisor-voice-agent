"""
Mock STT Client - For testing without freezing
Lightweight placeholder STT that doesn't block
"""
import os
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class MockSTTClient:
    """
    Mock STT Client for testing
    
    Responsibilities:
    - Return placeholder text without blocking
    - Simulate speech recognition
    - Prevent UI freezing
    """
    
    def __init__(self):
        self.call_count = 0
        logger.info("Mock STT initialized for testing")
        
    def transcribe_audio(self, audio_bytes: bytes, language_code: str = None) -> str:
        """
        Mock transcription - returns placeholder text
        
        Args:
            audio_bytes: Raw audio data (ignored)
            language_code: Language code (ignored)
            
        Returns:
            Placeholder transcribed text
        """
        self.call_count += 1
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Return different placeholder texts based on call count
        if self.call_count % 5 == 1:
            return "hello"
        elif self.call_count % 5 == 2:
            return "I want to book a KYC appointment"
        elif self.call_count % 5 == 3:
            return "morning"
        elif self.call_count % 5 == 4:
            return "first"
        else:
            return "yes"
            
    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine information"""
        return {
            "engine": "mock",
            "call_count": self.call_count,
            "type": "mock_testing"
        }


# Convenience function
def create_stt_client() -> MockSTTClient:
    """Factory function to create Mock STT client"""
    return MockSTTClient()
