"""
Main Voice Pipeline
Integrates all components: VAD, STT, LLM Orchestrator, MCP, TTS
"""
import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Dict, Any, Optional
import numpy as np

# Repo root: pipeline/ -> phase-4-integration/ -> repo
_ROOT = Path(__file__).resolve().parent.parent.parent
for _phase in ("phase-4-integration", "phase-3-llm-orchestrator", "phase-1-core-voice"):
    _p = str(_ROOT / _phase)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from vad.silero_vad import create_vad
from stt.hf_whisper_asr import create_hf_asr
from tts.hf_parler_tts import create_hf_tts
from core.orchestrator import create_orchestrator
from compliance.pii_detector import create_pii_detector
from compliance.compliance_checker import create_compliance_checker
from handlers.waitlist_handler import create_waitlist_handler

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    End-to-end voice pipeline
    
    Flow:
    Audio Stream → VAD → STT → PII Check → LLM Orchestrator → TTS → Audio Output
    """
    
    def __init__(self):
        # Initialize components
        self.vad = create_vad()
        self.stt = create_stt_client()
        self.tts = create_tts_client()
        self.orchestrator = create_orchestrator()
        self.pii_detector = create_pii_detector()
        self.compliance_checker = create_compliance_checker()
        self.waitlist_handler = create_waitlist_handler()
        
        # Metrics
        self.metrics = {
            "total_calls": 0,
            "total_latency": 0.0,
            "pii_interruptions": 0,
            "advice_refusals": 0
        }
        
        logger.info("Voice Pipeline initialized")
        
    async def process_stream(
        self,
        conversation_id: str,
        audio_stream: AsyncIterator[np.ndarray]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process audio stream through pipeline
        
        Yields:
            Dict with status, audio, text, and metadata
        """
        self.metrics["total_calls"] += 1
        
        try:
            async for audio_chunk in audio_stream:
                # Step 1: VAD
                speech_chunk = self.vad.process(audio_chunk)
                
                if not speech_chunk.is_speech:
                    yield {"status": "listening", "audio": None, "text": ""}
                    continue
                    
                # Step 2: STT
                audio_bytes = (speech_chunk.audio_data * 32768).astype(np.int16).tobytes()
                transcript = self.stt.transcribe_audio(audio_bytes)
                
                if not transcript:
                    continue
                    
                # Step 3: PII Check
                pii_result = self.pii_detector.detect_and_respond(transcript)
                if pii_result["should_interrupt"]:
                    self.metrics["pii_interruptions"] += 1
                    audio = self.tts.synthesize(pii_result["message"])
                    yield {
                        "status": "speaking",
                        "audio": audio,
                        "text": pii_result["message"],
                        "compliance": "pii_interruption"
                    }
                    continue
                    
                # Step 4: LLM Orchestration
                result = self.orchestrator.process(conversation_id, transcript)
                
                # Check for advice refusal
                if result.get("intent") == "investment_advice":
                    self.metrics["advice_refusals"] += 1
                    
                # Step 5: TTS
                audio = self.tts.synthesize(result["audio_ready_text"])
                
                yield {
                    "status": "speaking",
                    "audio": audio,
                    "text": result["response_text"],
                    "state": result["state"],
                    "booking_code": result.get("booking_code"),
                    "compliance": None
                }
                
                # Reset VAD for next utterance
                self.vad.reset()
                
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            yield await self._handle_error(e)
            
    async def process_single(
        self,
        conversation_id: str,
        audio_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Process single audio input
        
        Returns:
            Result dict with audio, text, and metadata
        """
        try:
            # Convert bytes to numpy
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Run through pipeline
            async def single_chunk():
                yield audio_data
                
            results = []
            async for result in self.process_stream(conversation_id, single_chunk()):
                results.append(result)
                
            return results[-1] if results else {"status": "error", "text": "No response"}
            
        except Exception as e:
            logger.error(f"Single process error: {e}")
            return await self._handle_error(e)
            
    async def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle pipeline errors gracefully"""
        error_msg = "I apologize, I'm having trouble understanding. Could you please repeat that?"
        
        try:
            audio = self.tts.synthesize(error_msg)
        except:
            audio = b""
            
        return {
            "status": "error",
            "audio": audio,
            "text": error_msg,
            "error": str(error)
        }
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        stt_metrics = self.stt.get_metrics()
        tts_metrics = self.tts.get_metrics()
        
        return {
            "total_calls": self.metrics["total_calls"],
            "pii_interruptions": self.metrics["pii_interruptions"],
            "advice_refusals": self.metrics["advice_refusals"],
            "stt": stt_metrics,
            "tts": tts_metrics
        }


# Convenience function
def create_pipeline() -> VoicePipeline:
    """Factory function"""
    return VoicePipeline()
