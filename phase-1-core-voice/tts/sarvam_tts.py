"""
Sarvam AI TTS — Bulbul v2
POST https://api.sarvam.ai/text-to-speech
Returns base64-encoded WAV — decoded to bytes here.
"""
import os, base64, requests, logging, io
from typing import Optional

logger = logging.getLogger(__name__)

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# Indian English female voice — closest to a natural Indian accent
DEFAULT_SPEAKER   = "anushka"  # Indian English female voice
DEFAULT_LANGUAGE  = "en-IN"
DEFAULT_PITCH     = 0
DEFAULT_PACE      = 1.1       # slightly faster than default
DEFAULT_LOUDNESS  = 1.5


class SarvamTTS:
    """
    Sarvam AI Text-to-Speech (Bulbul v2)
    Drop-in replacement for HFParlerTTS — same .synthesize() interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        speaker: str = DEFAULT_SPEAKER,
        language: str = DEFAULT_LANGUAGE,
    ):
        self.api_key  = api_key or os.getenv("SARVAM_API_KEY", "")
        self.speaker  = speaker
        self.language = language
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not set — TTS calls will fail")

    # ── primary interface (matches HFParlerTTS) ───────────────────────────────
    def synthesize(self, text: str, speaker_prompt: Optional[str] = None,
                   return_bytes: bool = True) -> Optional[bytes]:
        """
        Convert text → WAV bytes via Sarvam TTS.
        speaker_prompt is ignored (kept for interface compatibility).
        """
        if not text or not text.strip():
            return None
        return self._call_api(text)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _call_api(self, text: str) -> Optional[bytes]:
        # Sarvam TTS has a 500-char limit per request — split if needed
        chunks = self._split(text, 490)
        all_audio = b""
        for chunk in chunks:
            try:
                resp = requests.post(
                    SARVAM_TTS_URL,
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": [chunk],
                        "target_language_code": self.language,
                        "speaker": self.speaker,
                        "pitch": DEFAULT_PITCH,
                        "pace": DEFAULT_PACE,
                        "loudness": DEFAULT_LOUDNESS,
                        "speech_sample_rate": 22050,
                        "enable_preprocessing": True,
                        "model": "bulbul:v2",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                audios = data.get("audios", [])
                if audios:
                    all_audio += base64.b64decode(audios[0])
            except Exception as e:
                logger.error(f"Sarvam TTS error: {e}")
        return all_audio if all_audio else None

    @staticmethod
    def _split(text: str, max_chars: int) -> list[str]:
        """Split at sentence boundaries to stay under char limit."""
        if len(text) <= max_chars:
            return [text]
        chunks, current = [], ""
        for sentence in text.replace("! ", ". ").replace("? ", ". ").split(". "):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current) + len(sentence) + 2 <= max_chars:
                current += ("" if not current else ". ") + sentence
            else:
                if current:
                    chunks.append(current + ".")
                current = sentence
        if current:
            chunks.append(current)
        return chunks or [text[:max_chars]]

    def get_metrics(self):
        return {"provider": "sarvam", "speaker": self.speaker, "language": self.language}


def create_sarvam_tts(api_key: Optional[str] = None, speaker: str = DEFAULT_SPEAKER,
                      language: str = DEFAULT_LANGUAGE) -> SarvamTTS:
    return SarvamTTS(api_key=api_key, speaker=speaker, language=language)
