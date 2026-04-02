"""
Silero VAD Integration from Multilingual Agent
Optimized for real-time streaming with minimal latency
"""
import torch
import torchaudio
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """
    Voice Activity Detection using Silero VAD (from multilingual agent)
    
    Responsibilities:
    - Detect speech vs silence in audio chunks
    - Slice audio into speech segments
    - Filter background noise
    - Minimize STT API calls by only sending speech chunks
    """
    
    def __init__(
        self,
        chunk_duration_ms: int = 500,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100
    ):
        self.chunk_duration_ms = chunk_duration_ms
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        
        # Calculate samples per chunk
        self.samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)
        
        self.model = None
        self.utils = None
        self._buffer = np.array([], dtype=np.float32)
        self._speech_buffer = []
        self._is_speaking = False
        self._silence_counter = 0
        
    def load_model(self) -> None:
        """Load Silero VAD model from torch hub"""
        try:
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                trust_repo=True
            )
            
            # Extract the helper functions we need
            (
                self.get_speech_timestamps,  # detects speech segments
                _save_audio,
                self.read_audio,             # reads audio into a tensor
                _VADIterator,
                self.collect_chunks,         # extracts speech chunks
            ) = self.utils
            
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise
            
    def process(self, audio_data: np.ndarray) -> 'SpeechChunk':
        """
        Process audio data and detect speech using Silero VAD
        
        Args:
            audio_data: Audio samples (float32 or int16)
            
        Returns:
            SpeechChunk with speech detection result
        """
        if self.model is None:
            self.load_model()
            
        try:
            # Convert to float32 if needed
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
                
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_data)
            
            # Use Silero VAD to get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                audio_tensor, 
                self.model, 
                sampling_rate=self.sample_rate
            )
            
            # Calculate if speech was detected
            speech_detected = len(speech_timestamps) > 0
            
            # Calculate confidence based on speech duration
            if speech_detected:
                total_speech_time = sum(end['end'] - start['start'] for start, end in speech_timestamps)
                total_time = len(audio_data) / self.sample_rate
                confidence = min(total_speech_time / total_time, 1.0)
            else:
                confidence = 0.0
                
            # Return speech chunk
            return SpeechChunk(
                is_speech=speech_detected,
                audio_data=audio_data,
                duration_ms=len(audio_data) * 1000 / self.sample_rate,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return SpeechChunk(
                is_speech=False,
                audio_data=audio_data,
                duration_ms=len(audio_data) * 1000 / self.sample_rate,
                confidence=0.0
            )
            
    def reset(self) -> None:
        """Reset internal buffer"""
        self._buffer = np.array([], dtype=np.float32)
        self._speech_buffer = []
        self._is_speaking = False
        self._silence_counter = 0
        
    def get_info(self) -> dict:
        """Get VAD information"""
        return {
            "type": "silero_vad",
            "sample_rate": self.sample_rate,
            "chunk_duration_ms": self.chunk_duration_ms,
            "threshold": self.threshold,
            "model_loaded": self.model is not None
        }


class SpeechChunk:
    """Simple speech chunk result"""
    def __init__(
        self,
        is_speech: bool,
        audio_data: np.ndarray,
        duration_ms: float,
        confidence: float
    ):
        self.is_speech = is_speech
        self.audio_data = audio_data
        self.duration_ms = duration_ms
        self.confidence = confidence
        
    def __repr__(self):
        return f"SpeechChunk(is_speech={self.is_speech}, duration={self.duration_ms:.0f}ms, confidence={self.confidence:.2f})"


# Convenience function
def create_vad() -> VoiceActivityDetector:
    """Factory function to create and load VAD"""
    vad = VoiceActivityDetector()
    vad.load_model()
    return vad
