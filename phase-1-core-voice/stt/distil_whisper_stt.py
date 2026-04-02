"""
distil_whisper_stt.py - Distil-Whisper Small (Quantized) for Fast Indian English ASR

Uses faster-whisper with distil-whisper/small for:
- 6x faster inference than base
- ~400MB download (quantized)
- Good Indian English support
"""
import numpy as np
from faster_whisper import WhisperModel
from typing import Optional


class DistilWhisperSTT:
    """
    Distil-Whisper Small (Quantized) STT
    
    Model: distil-whisper/small.en (English optimized)
    - Size: ~400MB (quantized INT8)
    - Speed: 6x faster than base
    - Good for Indian English accents
    """
    
    def __init__(
        self,
        model_size: str = "distil-small.en",  # distil-whisper/small.en
        device: str = "cpu",
        compute_type: str = "int8",  # Quantized for speed
        initial_prompt: Optional[str] = None
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.initial_prompt = initial_prompt or "Indian English accent. Financial advisory booking."
        
        print(f"Loading Distil-Whisper {model_size} ({compute_type})...")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=None  # Uses ~/.cache/huggingface
        )
        print("✓ Distil-Whisper loaded")
    
    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "en",
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        condition_on_previous_text: bool = True,
        initial_prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio: numpy array (float32, 16kHz, mono)
            language: "en" for English
            beam_size: beam search width
            best_of: number of candidates
            temperature: sampling temperature (0=deterministic)
            condition_on_previous_text: use previous text as prompt
            initial_prompt: context prompt for transcription
        
        Returns:
            Transcribed text
        """
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=beam_size,
            best_of=best_of,
            temperature=temperature,
            condition_on_previous_text=condition_on_previous_text,
            initial_prompt=initial_prompt or self.initial_prompt,
            vad_filter=True,  # Built-in VAD
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        # Collect all segments
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """
        Transcribe from raw audio bytes (16-bit PCM, 16kHz)
        
        Args:
            audio_bytes: Raw PCM bytes
        
        Returns:
            Transcribed text
        """
        # Convert bytes to numpy array
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return self.transcribe(audio)


def create_distil_whisper() -> DistilWhisperSTT:
    """Factory function - creates default instance"""
    return DistilWhisperSTT(
        model_size="distil-small.en",
        device="cpu",
        compute_type="int8"
    )


if __name__ == "__main__":
    # Test
    import time
    
    print("Testing Distil-Whisper STT...")
    stt = create_distil_whisper()
    print(f"Model loaded: {stt.model_size}")
    
    # Simulate audio
    test_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    start = time.time()
    result = stt.transcribe(test_audio)
    elapsed = time.time() - start
    
    print(f"Transcription: {result}")
    print(f"Time: {elapsed:.2f}s")
    print("Test complete!")
