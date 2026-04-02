"""
Silero VAD Integration for Voice Activity Detection
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
    Voice Activity Detection using Silero VAD
    
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
        logger.info("Loading Silero VAD model...")
        
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        
        self.model = model
        self.utils = utils
        
        (get_speech_timestamps,
         save_audio,
         read_audio,
         VADIterator,
         collect_chunks) = utils
        
        self.vad_iterator = VADIterator(model)
        
        logger.info("Silero VAD model loaded successfully")
        
    # Silero requires fixed-size windows: 512 samples @ 16 kHz, 256 @ 8 kHz
    _WINDOW_SIZES = {16000: 512, 8000: 256}

    def _get_window_size(self) -> int:
        return self._WINDOW_SIZES.get(self.sample_rate, 512)

    def process(self, audio_chunk: np.ndarray) -> 'SpeechChunk':
        """
        Process an audio chunk and detect voice activity.

        The incoming chunk from Gradio can be any length. We split it into
        fixed 512-sample windows (required by Silero at 16 kHz), run the
        model on each window, and aggregate the result.
        """
        if self.model is None:
            raise RuntimeError("VAD model not loaded. Call load_model() first.")

        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        if len(audio_chunk) == 0:
            return SpeechChunk(is_speech=False, audio_data=np.array([], dtype=np.float32),
                               duration_ms=0, confidence=0.0)

        if np.max(np.abs(audio_chunk)) > 1.0:
            audio_chunk = audio_chunk / 32768.0

        # Prepend any leftover samples from previous call
        if len(self._buffer) > 0:
            audio_chunk = np.concatenate([self._buffer, audio_chunk])
            self._buffer = np.array([], dtype=np.float32)

        win = self._get_window_size()
        n_windows = len(audio_chunk) // win

        if n_windows == 0:
            self._buffer = audio_chunk
            return SpeechChunk(is_speech=False, audio_data=np.array([], dtype=np.float32),
                               duration_ms=0, confidence=0.0)

        # Save leftover samples for next call
        leftover = len(audio_chunk) - n_windows * win
        if leftover > 0:
            self._buffer = audio_chunk[n_windows * win:]

        speech_prob = 0.0
        for i in range(n_windows):
            window = audio_chunk[i * win: (i + 1) * win]
            tensor_window = torch.from_numpy(window)
            with torch.no_grad():
                prob = self.model(tensor_window, self.sample_rate).item()
            if prob > speech_prob:
                speech_prob = prob

        is_speech = speech_prob >= self.threshold
        processed_audio = audio_chunk[:n_windows * win]

        if is_speech:
            self._speech_buffer.append(processed_audio)
            self._silence_counter = 0
            self._is_speaking = True
        else:
            if self._is_speaking:
                self._silence_counter += 1

                silence_duration = self._silence_counter * self.chunk_duration_ms
                if silence_duration >= self.min_silence_duration_ms:
                    if len(self._speech_buffer) > 0:
                        speech_audio = np.concatenate(self._speech_buffer)
                        self._speech_buffer = []
                        self._is_speaking = False

                        speech_duration = len(speech_audio) / self.sample_rate * 1000
                        if speech_duration >= self.min_speech_duration_ms:
                            return SpeechChunk(
                                is_speech=True,
                                audio_data=speech_audio,
                                duration_ms=speech_duration,
                                confidence=speech_prob
                            )

        return SpeechChunk(
            is_speech=False,
            audio_data=np.array([], dtype=np.float32),
            duration_ms=0,
            confidence=speech_prob
        )
        
    def reset(self) -> None:
        """Reset VAD state for new conversation"""
        self._buffer = np.array([], dtype=np.float32)
        self._speech_buffer = []
        self._is_speaking = False
        self._silence_counter = 0
        if self.vad_iterator:
            self.vad_iterator.reset_states()


class SpeechChunk:
    """Result from VAD processing"""
    
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


# Convenience function for quick testing
def create_vad() -> VoiceActivityDetector:
    """Factory function to create and load VAD"""
    vad = VoiceActivityDetector()
    vad.load_model()
    return vad
