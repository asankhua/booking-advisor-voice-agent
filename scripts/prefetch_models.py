import os
if os.getenv('PREFETCH_HF_MODELS', 'false').lower() == 'true':
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
    from parler_tts import ParlerTTSForConditionalGeneration, AutoTokenizer
    AutoModelForSpeechSeq2Seq.from_pretrained('openai/whisper-base')
    AutoProcessor.from_pretrained('openai/whisper-base')
    ParlerTTSForConditionalGeneration.from_pretrained('parler-tts/parler-tts-mini-v1')
    AutoTokenizer.from_pretrained('parler-tts/parler-tts-mini-v1')
    print('HF models pre-fetched')
else:
    print('Skipping HF model prefetch (VOICE_PROVIDER=sarvam)')
