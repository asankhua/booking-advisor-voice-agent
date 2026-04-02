"""
Hugging Face Transformers Whisper ASR Implementation
Speech-to-Text using openai/whisper models via transformers pipeline
"""
import os
import logging
from typing import Optional, Dict, Any, Union
import time
import torch
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor

logger = logging.getLogger(__name__)


class HFWhisperASR:
    """
    Hugging Face Whisper ASR Client
    
    Responsibilities:
    - Transcribe audio files to text using Whisper models
    - Support multiple languages
    - Handle model loading and caching
    - Track latency metrics
    """
    
    def __init__(
        self,
        model_name: str = "openai/whisper-base",  # 74MB, good balance
        device: str = "auto",
        language: str = "en",
        task: str = "transcribe"
    ):
        """
        Initialize Whisper ASR pipeline
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: "auto", "cpu", or "cuda"
            language: Language code (e.g., "en", "hi" for multilingual)
            task: "transcribe" or "translate"
        """
        self.model_name = model_name
        self.language = language
        self.task = task
        
        # Determine device
        if device == "auto":
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Loading Whisper model: {model_name} on {self.device}")
        
        # Load model and processor manually for more control
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name)
        self.model.to(self.device)
        
        # Create pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            device=self.device,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        
        # Metrics
        self._total_requests = 0
        self._total_latency = 0.0
        
        logger.info(f"Whisper ASR initialized: model={model_name}, device={self.device}")
        
    def transcribe(
        self, 
        audio_input: Union[str, bytes, torch.Tensor],
        language: Optional[str] = None,
        return_timestamps: bool = False
    ) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_input: Path to audio file, audio bytes, or tensor
            language: Language code (overrides default)
            return_timestamps: Whether to return word-level timestamps
            
        Returns:
            Transcribed text
        """
        if audio_input is None or (isinstance(audio_input, str) and not audio_input):
            return ""
        
        start_time = time.time()
        self._total_requests += 1
        
        try:
            # Prepare generate kwargs
            generate_kwargs = {
                "task": self.task,
                "language": language or self.language,
            }
            if hasattr(self, 'initial_prompt') and self.initial_prompt:
                generate_kwargs["prompt_ids"] = self.processor.get_prompt_ids(
                    self.initial_prompt, return_tensors="pt"
                ).to(self.device)
            
            # Run inference
            result = self.pipe(
                audio_input,
                return_timestamps=return_timestamps,
                generate_kwargs=generate_kwargs
            )
            
            # Extract text
            if isinstance(result, dict):
                transcript = result.get("text", "")
            elif isinstance(result, list) and len(result) > 0:
                transcript = result[0].get("text", "") if isinstance(result[0], dict) else str(result[0])
            else:
                transcript = str(result)
            
            # Track latency
            latency = time.time() - start_time
            self._total_latency += latency
            
            logger.info(f"ASR successful: '{transcript[:50]}...' in {latency:.2f}s")
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            return ""
    
    def transcribe_file(self, file_path: str, **kwargs) -> str:
        """Convenience method for file transcription"""
        return self.transcribe(file_path, **kwargs)
    
    def transcribe_bytes(self, audio_bytes: bytes, sample_rate: int = 16000, **kwargs) -> str:
        """
        Transcribe from raw audio bytes
        
        Args:
            audio_bytes: Raw audio data (convert to numpy array first)
            sample_rate: Audio sample rate (default 16kHz)
        """
        import numpy as np
        import io
        import soundfile as sf
        
        # Convert bytes to numpy array
        audio_buffer = io.BytesIO(audio_bytes)
        audio_array, sr = sf.read(audio_buffer)
        
        # Resample if needed (whisper expects 16kHz)
        if sr != 16000:
            import librosa
            audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=16000)
        
        return self.transcribe(audio_array, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get latency metrics"""
        if self._total_requests == 0:
            return {"avg_latency_ms": 0, "total_requests": 0}
        
        return {
            "avg_latency_ms": (self._total_latency / self._total_requests) * 1000,
            "total_requests": self._total_requests,
            "model_name": self.model_name,
            "device": self.device
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics"""
        self._total_requests = 0
        self._total_latency = 0.0


# Convenience factory function
def create_hf_asr(
    model_name: str = "openai/whisper-base",
    device: str = "auto",
    language: str = "en"
) -> HFWhisperASR:
    """Factory function to create HF Whisper ASR"""
    return HFWhisperASR(
        model_name=model_name,
        device=device,
        language=language
    )


if __name__ == "__main__":
    # Test the ASR
    logging.basicConfig(level=logging.INFO)
    
    print("Testing HF Whisper ASR...")
    asr = create_hf_asr(model_name="openai/whisper-tiny")  # Use tiny for quick test
    
    print(f"Model: {asr.model_name}")
    print(f"Device: {asr.device}")
    print(f"Metrics: {asr.get_metrics()}")
