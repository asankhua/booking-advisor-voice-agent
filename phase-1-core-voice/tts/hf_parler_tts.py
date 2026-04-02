"""
Hugging Face ParlerTTS Implementation
Text-to-Speech using ParlerTTS models via transformers
"""
import os
import logging
from typing import Optional, Dict, Any
import time
import io
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf

logger = logging.getLogger(__name__)


class HFParlerTTS:
    """
    Hugging Face ParlerTTS Client
    
    Responsibilities:
    - Synthesize text to speech using ParlerTTS
    - Support voice cloning via speaker prompts
    - Handle model loading and caching
    - Support streaming audio output
    """
    
    DEFAULT_SPEAKER_PROMPT = (
        "Priya speaks with a clear Indian English accent, warm and professional tone, "
        "moderate pace, very clear audio with no background noise."
    )
    
    def __init__(
        self,
        model_name: str = "parler-tts/parler-tts-mini-v1",  # 600MB
        device: str = "auto",
        speaker_prompt: Optional[str] = None,
        sample_rate: int = 44100
    ):
        """
        Initialize ParlerTTS model
        
        Args:
            model_name: ParlerTTS model (mini-v1 or large-v1)
            device: "auto", "cpu", or "cuda"
            speaker_prompt: Description of speaker voice characteristics
            sample_rate: Output sample rate
        """
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.speaker_prompt = speaker_prompt or self.DEFAULT_SPEAKER_PROMPT
        
        # Determine device
        if device == "auto":
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Loading ParlerTTS model: {model_name} on {self.device}")
        
        # Load model and tokenizer
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Metrics
        self._total_requests = 0
        self._total_latency = 0.0
        
        logger.info(f"ParlerTTS initialized: model={model_name}, device={self.device}")
        
    def synthesize(
        self, 
        text: str,
        speaker_prompt: Optional[str] = None,
        return_bytes: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
            speaker_prompt: Override default speaker description
            return_bytes: Return raw bytes (True) or numpy array (False)
            
        Returns:
            Audio bytes (WAV format) or numpy array
        """
        if not text or not text.strip():
            return None
        
        start_time = time.time()
        self._total_requests += 1
        
        try:
            # Prepare prompts
            prompt = speaker_prompt or self.speaker_prompt
            
            # Tokenize
            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
            prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(self.device)
            
            # Generate — allow longer audio for full responses
            generation = self.model.generate(
                input_ids=input_ids,
                prompt_input_ids=prompt_input_ids,
                max_new_tokens=2000,
                do_sample=True,
                temperature=1.0,
            )
            
            # Decode to audio
            audio_arr = generation.cpu().numpy().squeeze()
            
            # Track latency
            latency = time.time() - start_time
            self._total_latency += latency
            
            logger.info(f"TTS synthesis successful: {len(audio_arr)} samples ({latency:.2f}s)")
            
            if return_bytes:
                # Convert to WAV bytes
                buffer = io.BytesIO()
                sf.write(buffer, audio_arr, self.sample_rate, format="WAV")
                buffer.seek(0)
                return buffer.read()
            else:
                return audio_arr
                
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None
    
    def synthesize_to_file(
        self, 
        text: str, 
        output_path: str,
        speaker_prompt: Optional[str] = None
    ) -> bool:
        """
        Synthesize and save to file
        
        Args:
            text: Text to synthesize
            output_path: Output file path (.wav)
            speaker_prompt: Override default speaker description
            
        Returns:
            True if successful
        """
        try:
            audio_arr = self.synthesize(text, speaker_prompt=speaker_prompt, return_bytes=False)
            if audio_arr is not None:
                sf.write(output_path, audio_arr, self.sample_rate)
                logger.info(f"Saved audio to {output_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
        return False
    
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
def create_hf_tts(
    model_name: str = "parler-tts/parler-tts-mini-v1",
    device: str = "auto",
    speaker_prompt: Optional[str] = None
) -> HFParlerTTS:
    """Factory function to create HF ParlerTTS"""
    return HFParlerTTS(
        model_name=model_name,
        device=device,
        speaker_prompt=speaker_prompt
    )


if __name__ == "__main__":
    # Test the TTS
    logging.basicConfig(level=logging.INFO)
    
    print("Testing HF ParlerTTS...")
    tts = create_hf_tts()
    
    print(f"Model: {tts.model_name}")
    print(f"Device: {tts.device}")
    
    # Test synthesis
    test_text = "Hello! I am your AI assistant. How can I help you today?"
    audio = tts.synthesize(test_text)
    
    if audio:
        print(f"Generated {len(audio)} bytes of audio")
        # Save to file
        tts.synthesize_to_file(test_text, "test_output.wav")
    else:
        print("Synthesis failed")
