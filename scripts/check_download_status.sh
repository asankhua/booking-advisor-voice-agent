#!/bin/bash
# Check model download status

echo "=========================================="
echo "Model Download Status Check"
echo "=========================================="
echo ""

# Check if download is running
echo "📊 Download Process:"
ps aux | grep -E "download_models" | grep -v grep || echo "   Not currently running"
echo ""

# Check cache directory
echo "📁 Hugging Face Cache:"
CACHE_DIR="$HOME/.cache/huggingface/hub"

if [ -d "$CACHE_DIR" ]; then
    echo "   Location: $CACHE_DIR"
    echo "   Size: $(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)"
    echo ""
    
    echo "📂 Models Found:"
    ls -1 "$CACHE_DIR" | grep "models--" || echo "   No models yet"
    echo ""
    
    # Check for specific models
    echo "🔍 Specific Models:"
    if [ -d "$CACHE_DIR/models--openai--whisper-base" ]; then
        echo "   ✅ Whisper Base: $(du -sh "$CACHE_DIR/models--openai--whisper-base" 2>/dev/null | cut -f1)"
    else
        echo "   ⏳ Whisper Base: Not downloaded"
    fi
    
    if [ -d "$CACHE_DIR/models--parler-tts--parler-tts-mini-v1" ]; then
        echo "   ✅ ParlerTTS Mini: $(du -sh "$CACHE_DIR/models--parler-tts--parler-tts-mini-v1" 2>/dev/null | cut -f1)"
    else
        echo "   ⏳ ParlerTTS Mini: Not downloaded"
    fi
else
    echo "   ❌ Cache directory not found"
fi

echo ""
echo "=========================================="
