"""
multilingual_pipeline.py — Voice Agent Pipeline
=================================================
This file contains the orchestrator that chains the core voice components:

  1. VAD  (Voice Activity Detection) — Silero VAD (vad/silero_vad.py)
  2. STT  (Speech-to-Text)          — OpenAI Whisper (stt/whisper_stt.py)
  3. LLM  (Language Model)          — Groq API (Llama 3.3 70B)
  4. TTS  (Text-to-Speech)          — ParlerTTS (tts/hf_parler_tts.py)

Pipeline flow:
  Microphone → VAD → STT → LLM → TTS → Speaker
"""

import os
import time
import tempfile
import logging
from typing import Optional, Tuple
from pathlib import Path

import torch
import torchaudio
from dotenv import load_dotenv

# Import local modular components
from stt.whisper_stt import WhisperSTTClient
from tts.hf_parler_tts import HFParlerTTS
from vad.silero_vad import VoiceActivityDetector, SpeechChunk

load_dotenv()

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


class VoicePipeline:
    """
    Main voice pipeline orchestrator that chains VAD → STT → LLM → TTS
    
    Responsibilities:
    - Coordinate the voice processing pipeline
    - Manage component lifecycle (lazy loading)
    - Track latency metrics
    """

    def __init__(self):
        self.vad: Optional[VoiceActivityDetector] = None
        self.stt: Optional[WhisperSTTClient] = None
        self.tts: Optional[HFParlerTTS] = None
        self._latency = {}

    def initialize(self) -> None:
        """Initialize all pipeline components"""
        logger.info("Initializing Voice Pipeline components...")
        
        # Initialize VAD
        self.vad = VoiceActivityDetector()
        self.vad.load_model()
        logger.info("  ✓ VAD loaded")
        
        # Initialize STT
        self.stt = WhisperSTTClient(model_size="tiny")
        logger.info("  ✓ STT loaded")
        
        # Initialize TTS
        self.tts = HFParlerTTS()
        logger.info("  ✓ TTS loaded")
        
        logger.info("Voice Pipeline initialized successfully")

    def process_audio(
        self,
        audio_path: str,
        transcript: Optional[str] = None
    ) -> Tuple[str, str, Optional[bytes]]:
        """
        Process audio through the full pipeline
        
        Args:
            audio_path: Path to audio file
            transcript: Optional pre-transcribed text (for testing)
            
        Returns:
            Tuple of (transcription, response, audio_bytes)
        """
        pipeline_start = time.time()
        
        # Step 1: VAD - Trim silence
        t0 = time.time()
        trimmed_path = self._vad_process(audio_path)
        self._latency['vad'] = time.time() - t0
        logger.info(f"  ⏱  VAD  : {self._latency['vad']:.2f}s")

        # Step 2: STT - Transcribe
        t0 = time.time()
        if transcript is None:
            transcript = self._stt_process(trimmed_path)
        self._latency['stt'] = time.time() - t0
        logger.info(f"  ⏱  STT  : {self._latency['stt']:.2f}s")
        logger.info(f"  📝 Transcript: \"{transcript}\"")

        if not transcript or not transcript.strip():
            return "(could not transcribe)", "", None

        # Step 3: LLM - Generate response
        t0 = time.time()
        response = self._llm_process(transcript)
        self._latency['llm'] = time.time() - t0
        logger.info(f"  ⏱  LLM  : {self._latency['llm']:.2f}s")
        logger.info(f"  💬 Response: \"{response}\"")

        # Step 4: TTS - Synthesize
        t0 = time.time()
        audio_bytes = self._tts_process(response)
        self._latency['tts'] = time.time() - t0
        logger.info(f"  ⏱  TTS  : {self._latency['tts']:.2f}s")

        total = time.time() - pipeline_start
        logger.info(f"  ⏱  TOTAL: {total:.2f}s  ✓")

        return transcript, response, audio_bytes

    def _vad_process(self, audio_path: str) -> str:
        """Process audio with VAD to trim silence"""
        if not self.vad:
            self.vad = VoiceActivityDetector()
            self.vad.load_model()
        
        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            waveform = torchaudio.transforms.Resample(sample_rate, 16000)(waveform)
        
        audio_tensor = waveform.squeeze()
        
        # Get speech timestamps
        speech_timestamps = self.vad.get_speech_timestamps(
            audio_tensor, self.vad.model, sampling_rate=16000
        )
        
        if not speech_timestamps:
            logger.warning("VAD found no speech - passing original audio through")
            return audio_path
        
        # Collect speech chunks
        speech_audio = self.vad.collect_chunks(speech_timestamps, audio_tensor)
        
        # Save trimmed audio
        trimmed_path = tempfile.mktemp(suffix=".wav")
        torchaudio.save(trimmed_path, speech_audio.unsqueeze(0), 16000)
        
        original_dur = len(audio_tensor) / 16000
        trimmed_dur = len(speech_audio) / 16000
        logger.info(f"VAD trimmed {original_dur:.1f}s → {trimmed_dur:.1f}s")
        
        return trimmed_path

    def _stt_process(self, audio_path: str) -> str:
        """Process audio with STT to get transcription"""
        if not self.stt:
            self.stt = WhisperSTTClient(model_size="tiny")
        
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        return self.stt.transcribe_audio(audio_bytes)

    def _llm_process(self, transcript: str) -> str:
        """Process transcript with LLM to get response"""
        try:
            from groq import Groq
        except ImportError:
            logger.warning("Groq not installed - using mock response")
            return f"I heard: {transcript}"
        
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set - using mock response")
            return f"I heard: {transcript}"
        
        try:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise (2-3 sentences)."},
                    {"role": "user", "content": transcript}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"I heard: {transcript}"

    def _tts_process(self, text: str) -> Optional[bytes]:
        """Process text with TTS to get audio"""
        if not self.tts:
            self.tts = HFParlerTTS()
        
        return self.tts.synthesize(text)

    def get_latency_metrics(self) -> dict:
        """Get latency metrics for each component"""
        return self._latency.copy()


# ===================================================================
#  CONVENIENCE FUNCTIONS
# ===================================================================

def run_pipeline(
    audio_path: str,
    history: list = None
) -> Tuple[str, str, Optional[bytes], list]:
    """
    Run the full voice-agent pipeline end to end.
    
    Args:
        audio_path: file path from Gradio's microphone widget
        history: conversation history (for future LLM context)
        
    Returns:
        (user_transcript, llm_reply, tts_audio_bytes, updated_history)
    """
    pipeline = VoicePipeline()
    pipeline.initialize()
    
    transcript, response, audio_bytes = pipeline.process_audio(audio_path)
    
    updated_history = history or []
    updated_history.append({"role": "user", "parts": [transcript]})
    updated_history.append({"role": "model", "parts": [response]})
    
    return transcript, response, audio_bytes, updated_history


if __name__ == "__main__":
    # Test the pipeline
    import sys
    
    print("Testing Voice Pipeline...")
    print("=" * 50)
    
    # Check if test audio file provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if os.path.exists(audio_file):
            pipeline = VoicePipeline()
            pipeline.initialize()
            
            transcript, response, audio, history = run_pipeline(audio_file)
            
            print(f"\n📝 Transcript: {transcript}")
            print(f"💬 Response: {response}")
            print(f"🔊 Audio: {len(audio) if audio else 0} bytes")
        else:
            print(f"Error: Audio file not found: {audio_file}")
    else:
        print("Usage: python multilingual_pipeline.py <audio_file.wav>")
        print("\nTesting component imports...")
        
        # Test imports
        from stt.whisper_stt import WhisperSTTClient
        from tts.hf_parler_tts import HFParlerTTS
        from vad.silero_vad import VoiceActivityDetector
        
        print("✓ All imports successful")
        print("✓ Voice Pipeline module ready")
