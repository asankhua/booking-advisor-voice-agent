"""
Advisor Voice Agent - Hugging Face Spaces Deployment
English-only Voice Agent with HF Transformers (Whisper + ParlerTTS)
"""

import os
import sys
import time
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

import streamlit as st
import torch
import torchaudio
import numpy as np
from dotenv import load_dotenv

# Page config MUST be first Streamlit call
st.set_page_config(
    page_title="Advisor Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup paths - use parent directory (project root)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase-1-core-voice"))
sys.path.insert(0, str(ROOT / "phase-3-llm-orchestrator"))
sys.path.insert(0, str(ROOT / "phase-4-integration"))

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CUSTOM CSS FOR PROFESSIONAL UI
# =============================================================================
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    /* Header styling */
    .agent-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    .agent-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #fff, #e0e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .agent-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px;
        margin: 8px 0 8px auto;
        max-width: 75%;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease;
    }
    
    .agent-message {
        background: #f8f9fa;
        color: #2c3e50;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 4px;
        margin: 8px auto 8px 0;
        max-width: 75%;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        animation: slideInLeft 0.3s ease;
    }
    
    .system-message {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        margin: 10px auto;
        text-align: center;
        font-size: 14px;
        max-width: 90%;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 13px;
        font-weight: 600;
        margin: 4px;
        transition: all 0.3s ease;
    }
    
    .status-active {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        animation: pulse 2s infinite;
    }
    
    .status-pending {
        background: #e9ecef;
        color: #6c757d;
    }
    
    .status-done {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
    }
    
    /* Control panel */
    .control-panel {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Audio recorder styling */
    .stAudioInput {
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    
    /* Animations */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Footer */
    .agent-footer {
        text-align: center;
        padding: 2rem;
        color: white;
        font-size: 12px;
        margin-top: 3rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'conversation_state': {
            'id': None,
            'state': 'greeting',
            'topic': None,
            'time_preference': None,
            'selected_slot': None,
            'booking_code': None,
            'available_slots': [],
            'slot_offered': False,
        },
        'chat_history': [],
        'debug_logs': [],
        'pipeline_status': {
            'VAD': 'pending',
            'ASR': 'pending',
            'LLM': 'pending',
            'TTS': 'pending'
        },
        'last_audio_response': None,
        'models_loaded': False,
        'vad': None,
        'asr': None,
        'tts': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# MODEL LOADING (LAZY)
# =============================================================================
@st.cache_resource
def load_vad():
    """Load Silero VAD model."""
    from vad.silero_vad_multilingual import create_vad
    with st.spinner("🔊 Loading VAD model..."):
        return create_vad()

@st.cache_resource
def load_asr():
    """Load Whisper ASR model."""
    from stt.hf_whisper_asr import create_hf_asr
    with st.spinner("🎤 Loading Whisper ASR..."):
        return create_hf_asr(model_name="openai/whisper-base")

@st.cache_resource  
def load_tts():
    """Load ParlerTTS model."""
    from tts.hf_parler_tts import create_hf_tts
    with st.spinner("🔈 Loading ParlerTTS..."):
        return create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")

def ensure_models_loaded():
    """Ensure all models are loaded."""
    if not st.session_state.models_loaded:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.vad = load_vad()
            st.success("✅ VAD Ready")
        
        with col2:
            st.session_state.asr = load_asr()
            st.success("✅ ASR Ready")
        
        with col3:
            st.session_state.tts = load_tts()
            st.success("✅ TTS Ready")
        
        st.session_state.models_loaded = True
        time.sleep(0.5)
        st.rerun()

# =============================================================================
# PIPELINE PROCESSING
# =============================================================================
def update_status(component: str, status: str):
    """Update pipeline status."""
    st.session_state.pipeline_status[component] = status

def process_audio(audio_bytes: bytes) -> Tuple[str, str, Optional[bytes]]:
    """
    Process audio through the full pipeline.
    
    Returns: (transcript, response_text, audio_response)
    """
    if not audio_bytes:
        st.warning("⚠️ Please record some audio first!")
        return "", "", None
    
    try:
        # Step 1: VAD
        update_status('VAD', 'active')
        with st.spinner("🔊 Processing voice..."):
            # Convert bytes to audio array
            import io
            import soundfile as sf
            
            audio_buffer = io.BytesIO(audio_bytes)
            audio_array, sample_rate = sf.read(audio_buffer)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                import librosa
                audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=16000)
            
            # Process through VAD
            speech_chunk = st.session_state.vad.process(audio_array)
            audio_to_process = speech_chunk.audio_data if speech_chunk.is_speech else audio_array
        
        update_status('VAD', 'done')
        
        # Step 2: ASR (Whisper)
        update_status('ASR', 'active')
        with st.spinner("🎤 Transcribing..."):
            transcript = st.session_state.asr.transcribe(audio_to_process)
        
        if not transcript:
            st.error("❌ Could not understand audio. Please speak clearly.")
            update_status('ASR', 'error')
            return "", "", None
        
        update_status('ASR', 'done')
        st.success(f"📝 You said: \"{transcript}\"")
        
        # Step 3: LLM (Groq)
        update_status('LLM', 'active')
        with st.spinner("🤖 Thinking..."):
            from simple_state_machine import run_simple_state_machine
            response_text, _ = run_simple_state_machine(
                transcript, 
                st.session_state.conversation_state
            )
        
        update_status('LLM', 'done')
        
        # Step 4: TTS (ParlerTTS)
        update_status('TTS', 'active')
        with st.spinner("🔈 Generating response..."):
            audio_response = st.session_state.tts.synthesize(
                response_text, 
                return_bytes=True
            )
        
        update_status('TTS', 'done')
        
        return transcript, response_text, audio_response
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        st.error(f"❌ Error: {e}")
        return "", "", None

# =============================================================================
# UI COMPONENTS
# =============================================================================
def render_header():
    """Render the professional header."""
    st.markdown("""
    <div class="agent-header">
        <div class="agent-title">🎙️ Advisor Voice Agent</div>
        <div class="agent-subtitle">
            AI-Powered Financial Advisory Appointment Booking<br>
            <small>Built with Hugging Face Transformers • Whisper + ParlerTTS</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_status():
    """Render pipeline status indicators."""
    status = st.session_state.pipeline_status
    html = '<div style="text-align: center; margin: 1rem 0;">'
    
    for label, state in status.items():
        if state == "done":
            css_class = "status-done"
            icon = "✓"
        elif state == "active":
            css_class = "status-active"
            icon = "●"
        else:
            css_class = "status-pending"
            icon = "○"
        
        html += f'<span class="status-badge {css_class}">{icon} {label}</span>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_chat():
    """Render chat history."""
    chat_html = '<div class="chat-container">'
    
    for msg in st.session_state.chat_history:
        role = msg.get("role", "")
        text = msg.get("text", "").replace("\n", "<br>")
        
        if role == "user":
            chat_html += f'<div class="user-message">{text}</div>'
        elif role == "agent":
            chat_html += f'<div class="agent-message">{text}</div>'
        elif role == "system":
            chat_html += f'<div class="system-message">{text}</div>'
    
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

def add_message(role: str, text: str):
    """Add message to chat history."""
    st.session_state.chat_history.append({
        "role": role,
        "text": text,
        "time": datetime.now().strftime("%H:%M")
    })

def reset_conversation():
    """Reset the conversation."""
    st.session_state.conversation_state = {
        'id': None,
        'state': 'greeting',
        'topic': None,
        'time_preference': None,
        'selected_slot': None,
        'booking_code': None,
        'available_slots': [],
        'slot_offered': False,
    }
    st.session_state.chat_history = []
    st.session_state.pipeline_status = {
        'VAD': 'pending',
        'ASR': 'pending',
        'LLM': 'pending',
        'TTS': 'pending'
    }
    st.session_state.last_audio_response = None

# =============================================================================
# MAIN APP
# =============================================================================
def main():
    """Main application."""
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Controls")
        
        if st.button("🔄 New Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()
        
        st.markdown("---")
        st.subheader("📊 Status")
        st.write(f"**Models:** {'✅ Loaded' if st.session_state.models_loaded else '⏳ Loading...'}")
        st.write(f"**Messages:** {len(st.session_state.chat_history)}")
        
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown("""
        **Voice Pipeline:**
        - 🔊 VAD: Silero
        - 🎤 ASR: Whisper Base
        - 🧠 LLM: Groq Llama 3.3
        - 🔈 TTS: ParlerTTS Mini
        
        **Deployment:**
        Hugging Face Spaces
        """)
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎤 Voice Input")
        
        # Model loading status
        if not st.session_state.models_loaded:
            ensure_models_loaded()
        
        # Audio input
        audio_input = st.audio_input("Click to record your voice")
        
        # Control buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            send_disabled = audio_input is None or not st.session_state.models_loaded
            if st.button("📤 Send Voice", type="primary", disabled=send_disabled, use_container_width=True):
                if audio_input:
                    # Reset status
                    for key in st.session_state.pipeline_status:
                        st.session_state.pipeline_status[key] = 'pending'
                    
                    # Process
                    audio_bytes = audio_input.getvalue()
                    transcript, response, audio_response = process_audio(audio_bytes)
                    
                    if transcript and response:
                        add_message("user", transcript)
                        add_message("agent", response)
                        st.session_state.last_audio_response = audio_response
                        st.rerun()
        
        with col_btn2:
            if st.button("🗑️ Clear", use_container_width=True):
                reset_conversation()
                st.rerun()
        
        # Pipeline status
        render_status()
        
        # Audio output
        if st.session_state.last_audio_response:
            st.markdown("### 🔊 Response")
            st.audio(st.session_state.last_audio_response, format="audio/wav")
    
    with col2:
        st.markdown("### 💬 Conversation")
        
        if not st.session_state.chat_history:
            st.info("👋 Welcome! Click the microphone to start a conversation.")
        else:
            render_chat()
    
    # Footer
    st.markdown("""
    <div class="agent-footer">
        <p>© 2026 Advisor Voice Agent • Built with ❤️ using Hugging Face Transformers</p>
        <p>Whisper ASR • ParlerTTS • Groq LLM • Silero VAD</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
