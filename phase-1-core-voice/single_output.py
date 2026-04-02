"""
Gradio 5.0 Fix - Explicit output handling
"""
import gradio as gr
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup paths - use project root (parent directory)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase-1-core-voice"))
sys.path.insert(0, str(ROOT / "phase-3-llm-orchestrator"))
sys.path.insert(0, str(ROOT / "phase-4-integration"))
sys.path.insert(0, str(ROOT / "phase-4-integration" / "ui"))  # For simple_state_machine

# Try importing at module level to verify paths work
try:
    from simple_state_machine import run_simple_state_machine
    print("✅ simple_state_machine imported successfully", file=sys.stderr)
    STATE_MACHINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ simple_state_machine import failed: {e}", file=sys.stderr)
    STATE_MACHINE_AVAILABLE = False

def process_single(audio_path):
    """Return single string for debug output."""
    logs = []
    
    def log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        return "\n".join(logs)
    
    if not audio_path:
        return log("❌ Please record audio first")
    
    try:
        log(f"📁 File: {audio_path}")
        
        # Check file exists
        if not os.path.exists(audio_path):
            return log("❌ File not found")
        
        file_size = os.path.getsize(audio_path)
        log(f"✅ File size: {file_size} bytes")
        
        # VAD
        log("🔊 Loading VAD...")
        from vad.silero_vad_multilingual import create_vad
        import soundfile as sf
        import librosa
        
        vad = create_vad()
        log("✅ VAD loaded")
        
        audio_data, sr = sf.read(audio_path)
        log(f"✅ Audio read: {len(audio_data)} samples @ {sr}Hz")
        
        if sr != 16000:
            log(f"🔄 Resampling to 16000Hz")
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
        
        speech_chunk = vad.process(audio_data)
        audio_to_process = speech_chunk.audio_data if hasattr(speech_chunk, 'is_speech') else audio_data
        log("✅ VAD processing complete")
        
        # ASR
        log("🎤 Loading Whisper ASR...")
        from stt.hf_whisper_asr import create_hf_asr
        asr = create_hf_asr(model_name="openai/whisper-base")
        log("✅ ASR loaded")
        
        transcript = asr.transcribe(audio_to_process)
        log(f"✅ Transcript: '{transcript}'")
        
        if not transcript:
            return log("❌ No speech detected in audio")
        
        # LLM
        log("🤖 Loading State Machine...")
        if STATE_MACHINE_AVAILABLE:
            response_text, _ = run_simple_state_machine(transcript, {})
            log(f"✅ Response: '{response_text}'")
        else:
            log("⚠️ State machine not available, using mock response")
            response_text = f"You said: {transcript}. How can I help you today?"
        
        # TTS
        log("🔈 Loading ParlerTTS...")
        from tts.hf_parler_tts import create_hf_tts
        tts = create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")
        log("✅ TTS loaded")
        
        output_path = tempfile.mktemp(suffix=".wav")
        log(f"💾 Synthesizing to: {output_path}")
        
        tts.synthesize_to_file(response_text, output_path)
        
        if os.path.exists(output_path):
            out_size = os.path.getsize(output_path)
            log(f"✅ Audio file created: {out_size} bytes")
            
            # Validate
            try:
                test_audio, test_sr = sf.read(output_path)
                log(f"✅ Valid audio: {len(test_audio)} samples @ {test_sr}Hz")
            except Exception as e:
                log(f"⚠️ Audio validation warning: {e}")
            
            log("🎉 SUCCESS! Pipeline complete")
            return "\n".join(logs)
        else:
            return log("❌ ERROR: Audio file not created!")
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return log(f"❌ ERROR: {str(e)}\n{error_detail}")

# Create UI
with gr.Blocks() as demo:
    gr.Markdown("# 🎙️ Voice Agent - Single Output Test")
    gr.Markdown("Debug log will show all pipeline steps")
    
    audio_in = gr.Audio(sources=["microphone"], type="filepath", label="🎤 Record Your Voice")
    btn = gr.Button("🚀 Process Voice", variant="primary")
    
    # Single output - just the debug log
    debug_output = gr.Textbox(
        label="📋 Debug Log Panel", 
        lines=20,
        interactive=False,
        value="Ready. Record audio and click Process."
    )
    
    # Simple single output click handler
    btn.click(
        fn=process_single,
        inputs=[audio_in],
        outputs=debug_output
    )

if __name__ == "__main__":
    print("="*60)
    print("Voice Agent - Single Output Test")
    print("="*60)
    print("URL: http://localhost:7866")
    print("="*60)
    demo.launch(server_name="0.0.0.0", server_port=7866, share=False)
