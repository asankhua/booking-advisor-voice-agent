"""
Voice Agent - Full UI with Transcript, Response, and Audio
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

def simple_state_machine_response(text, state):
    """Simple rule-based response."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm your advisor voice agent. How can I help you today?", {'state': 'greeting'}
    elif 'book' in text_lower or 'appointment' in text_lower:
        return "I can help you book an appointment. What topic would you like to discuss?", {'state': 'booking'}
    elif 'kyc' in text_lower or 'account' in text_lower:
        return "I can help with KYC and account setup. Would you like to schedule a consultation?", {'state': 'kyc'}
    elif 'sip' in text_lower or 'invest' in text_lower:
        return "I can help with SIP and investment planning. When would you like to discuss this?", {'state': 'investment'}
    else:
        return f"I heard you say: '{text}'. How can I assist you today?", {'state': 'general'}

def process_voice(audio_path):
    """Process audio and return all outputs."""
    logs = []
    
    def log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        return "\n".join(logs)
    
    if not audio_path:
        return "No audio", "Please record audio", None, log("❌ No audio recorded")
    
    try:
        log(f"📁 File: {audio_path}")
        
        # Step 1: VAD
        log("🔊 Loading VAD...")
        from vad.silero_vad_multilingual import create_vad
        import soundfile as sf
        import librosa
        
        vad = create_vad()
        audio_data, sr = sf.read(audio_path)
        
        if sr != 16000:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
        
        speech_chunk = vad.process(audio_data)
        audio_to_process = speech_chunk.audio_data if hasattr(speech_chunk, 'is_speech') else audio_data
        log("✅ VAD complete")
        
        # Step 2: ASR
        log("🎤 Loading ASR...")
        from stt.hf_whisper_asr import create_hf_asr
        asr = create_hf_asr(model_name="openai/whisper-base")
        
        transcript = asr.transcribe(audio_to_process)
        log(f"✅ Transcript: '{transcript}'")
        
        if not transcript:
            return "(no speech)", "Can't understand", None, log("❌ No speech")
        
        # Step 3: LLM
        log("🤖 Generating response...")
        response_text, _ = simple_state_machine_response(transcript, {})
        log(f"✅ Response: '{response_text}'")
        
        # Step 4: TTS
        log("🔈 Loading TTS...")
        from tts.hf_parler_tts import create_hf_tts
        tts = create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")
        
        output_path = tempfile.mktemp(suffix=".wav")
        tts.synthesize_to_file(response_text, output_path)
        
        if os.path.exists(output_path):
            out_size = os.path.getsize(output_path)
            log(f"✅ Audio created: {out_size} bytes")
            log("🎉 SUCCESS!")
            return transcript, response_text, output_path, "\n".join(logs)
        else:
            return transcript, response_text, None, log("❌ TTS failed")
            
    except Exception as e:
        import traceback
        return f"Error: {e}", "", None, log(f"❌ ERROR: {e}\n{traceback.format_exc()}")

# Create UI
with gr.Blocks(title="Voice Agent - Full UI") as demo:
    gr.Markdown("# 🎙️ Voice Agent")
    gr.Markdown("### Record your voice and get AI response with audio")
    
    with gr.Row():
        # Left column - Input
        with gr.Column():
            gr.Markdown("**Your Voice Input**")
            audio_in = gr.Audio(
                sources=["microphone"], 
                type="filepath", 
                label="🎤 Click to Record"
            )
            btn = gr.Button("🚀 Process Voice", variant="primary", size="lg")
        
        # Right column - Outputs
        with gr.Column():
            gr.Markdown("**AI Agent Response**")
            
            transcript_box = gr.Textbox(
                label="📝 What You Said (Transcript)",
                lines=2,
                interactive=False
            )
            
            response_box = gr.Textbox(
                label="💬 Agent Text Response",
                lines=3,
                interactive=False
            )
            
            audio_out = gr.Audio(
                label="🔊 Agent Voice (Audio)",
                type="filepath",
                autoplay=False
            )
    
    # Debug log at bottom
    with gr.Row():
        debug_log = gr.Textbox(
            label="📋 Debug Log",
            lines=10,
            interactive=False,
            value="Ready. Record audio and click Process."
        )
    
    # Connect button to function
    btn.click(
        fn=process_voice,
        inputs=[audio_in],
        outputs=[transcript_box, response_box, audio_out, debug_log]
    )
    
    gr.Markdown("---")
    gr.Markdown("**Local URL:** http://localhost:7868")

if __name__ == "__main__":
    print("="*60)
    print("Voice Agent - Full UI")
    print("="*60)
    print("URL: http://localhost:7868")
    print("Features:")
    print("  - Transcript display")
    print("  - Agent text response")
    print("  - Agent voice audio")
    print("  - Debug log")
    print("="*60)
    demo.launch(server_name="0.0.0.0", server_port=7868, share=False)
