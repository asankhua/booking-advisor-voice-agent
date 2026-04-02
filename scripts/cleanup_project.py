#!/usr/bin/env python3
"""
Project Cleanup Script - Removes legacy/duplicate files to match ARCHITECTURE.md
Run this script to clean up the project structure.
"""
import os
import shutil

BASE = '/Users/asankhua/Cursor/Trail/M3- 8 april'

def remove_files(file_list):
    """Remove a list of files"""
    for f in file_list:
        path = os.path.join(BASE, f)
        if os.path.exists(path):
            os.remove(path)
            print(f'✓ Removed: {f}')
        else:
            print(f'✗ Not found: {f}')

def remove_dirs(dir_list):
    """Remove a list of directories"""
    for d in dir_list:
        path = os.path.join(BASE, d)
        if os.path.exists(path) and os.path.isdir(path):
            shutil.rmtree(path)
            print(f'✓ Removed dir: {d}')
        else:
            print(f'✗ Not found: {d}')

def main():
    print("=" * 70)
    print("PROJECT CLEANUP SCRIPT")
    print("=" * 70)
    print("\nThis script will remove legacy/duplicate files to match ARCHITECTURE.md\n")

    # Phase-1-core-voice files to remove
    print("=" * 70)
    print("PHASE 1 CLEANUP - phase-1-core-voice/")
    print("=" * 70)
    
    p1_files = [
        'phase-1-core-voice/app.py',
        'phase-1-core-voice/homework.py',
        'phase-1-core-voice/stt/basic_stt.py',
        'phase-1-core-voice/stt/quick_stt.py',
        'phase-1-core-voice/stt/simple_stt.py',
        'phase-1-core-voice/tts/pyttsx3_tts.py',
        'phase-1-core-voice/vad/webrtc_vad.py',
        'phase-1-core-voice/ui/gradio_app.py',
    ]
    remove_files(p1_files)

    # Phase-4-integration files/dirs to remove
    print("\n" + "=" * 70)
    print("PHASE 4 CLEANUP - phase-4-integration/")
    print("=" * 70)
    
    p4_items = [
        'phase-4-integration/frontend',
        'phase-4-integration/ui/gradio_app_final.py',
        'phase-4-integration/ui/homework.py',
        'phase-4-integration/ui/multilingual_app.py',
        'phase-4-integration/ui/voice_agent.html',
        'phase-4-integration/ui/voice_agent_html.py',
        'phase-4-integration/ui/voice_agent_multilingual.py',
        'phase-4-integration/ui/voice_agent_multilingual_fixed.py',
        'phase-4-integration/ui/voice_agent_minimal.py',
        'phase-4-integration/ui/voice_agent_interface.py',
        'phase-4-integration/ui/debug_voice.py',
    ]
    
    p4_dirs = [item for item in p4_items if isinstance(item, str) and item.startswith('phase-4')]
    p4_files = [item for item in p4_items if not (isinstance(item, str) and item.startswith('phase-4')) or not item.endswith('.py')]
    
    # Separate dirs and files properly
    p4_dirs_to_remove = ['phase-4-integration/frontend']
    p4_files_to_remove = [
        'phase-4-integration/ui/gradio_app_final.py',
        'phase-4-integration/ui/homework.py',
        'phase-4-integration/ui/multilingual_app.py',
        'phase-4-integration/ui/voice_agent.html',
        'phase-4-integration/ui/voice_agent_html.py',
        'phase-4-integration/ui/voice_agent_multilingual.py',
        'phase-4-integration/ui/voice_agent_multilingual_fixed.py',
        'phase-4-integration/ui/voice_agent_minimal.py',
        'phase-4-integration/ui/voice_agent_interface.py',
        'phase-4-integration/ui/debug_voice.py',
    ]
    
    remove_dirs(p4_dirs_to_remove)
    remove_files(p4_files_to_remove)

    # Root files to remove (duplicates)
    print("\n" + "=" * 70)
    print("ROOT CLEANUP - Remove duplicate files")
    print("=" * 70)
    
    root_files = [
        'api_server.py',
        'app.py',
        'app_gradio.py',
        'full_ui.py',
        'professional_ui.py',
        'single_output.py',
        'cleanup.py',
        'download_models.py',
        'launch.py',
        'check_download_status.sh',
        'start_all.sh',
        'start_servers.sh',
    ]
    remove_files(root_files)

    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nExpected remaining structure:")
    print("\nphase-1-core-voice/:")
    print("  - multilingual_pipeline.py (core)")
    print("  - single_output.py (testing)")
    print("  - stt/whisper_stt.py (main STT)")
    print("  - stt/mock_stt.py (testing)")
    print("  - stt/hf_whisper_asr.py (alternative)")
    print("  - tts/hf_parler_tts.py (main TTS)")
    print("  - vad/silero_vad.py (main VAD)")
    print("  - vad/silero_vad_multilingual.py (multilingual)")
    print("  - tests/ (tests)")

    print("\nphase-4-integration/:")
    print("  - api_server.py (main FastAPI)")
    print("  - app.py (Streamlit)")
    print("  - ui/voice_agent.py (Gradio for testing)")
    print("  - ui/voice_agent_simple.py (simple)")
    print("  - ui/simple_state_machine.py (state machine)")
    print("  - compliance/, handlers/, pipeline/, tests/, utils/")

    print("\nfrontend/:")
    print("  - full_ui.py (Gradio for testing)")
    print("  - professional_ui.py (Gradio for testing)")

    print("\nscripts/:")
    print("  - All utility scripts")

if __name__ == '__main__':
    main()
