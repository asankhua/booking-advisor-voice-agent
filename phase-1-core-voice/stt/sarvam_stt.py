"""
Sarvam AI STT — Saaras v3
POST https://api.sarvam.ai/speech-to-text
Supports webm/opus natively — no local model needed.
"""
import os, requests, logging
from typing import Optional
import numpy as np
import io, tempfile

logger = logging.getLogger(__name__)

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


class SarvamSTT:
    """
    Sarvam AI Speech-to-Text (Saaras v3)
    Drop-in replacement for HFWhisperASR — same .transcribe() interface.
    """

    def __init__(self, api_key: Optional[str] = None, language: str = "en-IN"):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        self.language = language          # en-IN for Indian English
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not set — STT calls will fail")

    # ── primary interface (matches HFWhisperASR) ──────────────────────────────
    def transcribe(self, audio_input, language: Optional[str] = None, **kwargs) -> str:
        """
        Accept numpy float32 array OR raw bytes OR file path.
        Converts to WAV bytes and sends to Sarvam STT.
        """
        lang = language or self.language
        wav_bytes = self._to_wav_bytes(audio_input)
        if wav_bytes is None:
            return ""
        return self._call_api(wav_bytes, lang)

    def transcribe_bytes(self, audio_bytes: bytes, sample_rate: int = 16000, **kwargs) -> str:
        """Compatibility shim — wraps raw PCM int16 bytes."""
        wav_bytes = self._pcm_to_wav(audio_bytes, sample_rate)
        return self._call_api(wav_bytes, self.language)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _to_wav_bytes(self, audio_input) -> Optional[bytes]:
        """Convert numpy array / bytes / path → WAV bytes."""
        import soundfile as sf

        if isinstance(audio_input, np.ndarray):
            buf = io.BytesIO()
            sf.write(buf, audio_input.astype(np.float32), 16000, format="WAV")
            buf.seek(0)
            return buf.read()

        if isinstance(audio_input, bytes):
            # Already raw bytes — assume PCM int16 at 16kHz
            return self._pcm_to_wav(audio_input, 16000)

        if isinstance(audio_input, str) and os.path.exists(audio_input):
            with open(audio_input, "rb") as f:
                return f.read()

        return None

    def _pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
        import soundfile as sf
        arr = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        buf = io.BytesIO()
        sf.write(buf, arr, sample_rate, format="WAV")
        buf.seek(0)
        return buf.read()

    def _call_api(self, wav_bytes: bytes, language: str) -> str:
        try:
            resp = requests.post(
                SARVAM_STT_URL,
                headers={"api-subscription-key": self.api_key},
                files={"file": ("audio.wav", wav_bytes, "audio/wav")},
                data={
                    "model": "saaras:v3",
                    "language_code": language,
                    "with_timestamps": "false",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            transcript = data.get("transcript", "")
            logger.info(f"Sarvam STT: '{transcript[:60]}'")
            return transcript.strip()
        except Exception as e:
            logger.error(f"Sarvam STT error: {e}")
            return ""


def create_sarvam_stt(api_key: Optional[str] = None, language: str = "en-IN") -> SarvamSTT:
    return SarvamSTT(api_key=api_key, language=language)
