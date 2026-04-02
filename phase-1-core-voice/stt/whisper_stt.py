"""
Whisper STT Client - Small Model Download Approach
Lightweight Speech-to-Text using OpenAI Whisper tiny model
"""
import os
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed. Run: pip install openai-whisper")


class WhisperSTTClient:
    """
    OpenAI Whisper STT Client using tiny model
    
    Responsibilities:
    - Transcribe audio bytes to text
    - Auto-download tiny model (39MB) on first use
    - Work offline after initial download
    - Handle Indian accents reasonably well
    """
    
    def __init__(
        self,
        model_size: str = "tiny",
        language: str = "en",
        download_timeout: int = 300
    ):
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper not installed. Install with: pip install openai-whisper")
            
        self.model_size = model_size  # tiny (39MB), base (142MB), small (464MB)
        self.language = language
        self.download_timeout = download_timeout
        self.model = None
        self._load_model()
        
    def _load_model(self) -> None:
        """Load Whisper model (downloads if not present)"""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info(f"Whisper {self.model_size} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
            
    def transcribe_audio(self, audio_bytes: bytes, language_code: str = None) -> str:
        """
        Transcribe audio bytes to text
        
        Args:
            audio_bytes: Raw audio data (16-bit PCM)
            language_code: Language code (e.g., 'en', 'hi')
            
        Returns:
            Transcribed text
        """
        if not self.model:
            self._load_model()
            
        try:
            import io
            import numpy as np
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            result = self.model.transcribe(
                audio_array,
                language=language_code or self.language,
                fp16=False,  # Use FP32 for compatibility
                verbose=False
            )
            
            transcript = result.get("text", "").strip()
            logger.info(f"Transcription: {transcript}")
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
            
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_size": self.model_size,
            "language": self.language,
            "loaded": self.model is not None,
            "type": "whisper"
        }


# Convenience function
def create_stt_client() -> WhisperSTTClient:
    """Factory function to create Whisper STT client"""
    return WhisperSTTClient()
