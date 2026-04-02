"""
Download required models for the Voice Agent
"""
import os
import sys
from pathlib import Path

def get_cache_size():
    """Get size of Hugging Face cache."""
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache_dir.exists():
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(cache_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    
    return total_size / (1024 * 1024)  # Convert to MB

def download_models():
    """Download Whisper and ParlerTTS models."""
    print("="*60)
    print("Downloading Voice Agent Models")
    print("="*60)
    
    # Show cache location
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    print(f"\n📁 Cache location: {cache_dir}")
    initial_size = get_cache_size()
    print(f"📊 Current cache size: {initial_size:.1f} MB")
    
    # Download Whisper
    print("\n1. Downloading Whisper Base (openai/whisper-base) ~74MB")
    try:
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-base")
        AutoProcessor.from_pretrained("openai/whisper-base")
        print("✅ Whisper Base downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading Whisper: {e}")
        return False
    
    # Download ParlerTTS
    print("\n2. Downloading ParlerTTS Mini (parler-tts/parler-tts-mini-v1) ~600MB")
    try:
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1")
        AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")
        print("✅ ParlerTTS Mini downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading ParlerTTS: {e}")
        return False
    
    # Show final size
    final_size = get_cache_size()
    downloaded_size = final_size - initial_size
    
    print("\n" + "="*60)
    print("✅ All models downloaded successfully!")
    print("="*60)
    print(f"\n📁 Cache location: {cache_dir}")
    print(f"📊 Downloaded: {downloaded_size:.1f} MB")
    print(f"📊 Total cache size: {final_size:.1f} MB")
    print(f"\n💡 Models are saved to Hugging Face cache and will be reused")
    return True

if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
