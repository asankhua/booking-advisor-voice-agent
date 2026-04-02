"""
Integration tests for full pipeline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from compliance.pii_detector import create_pii_detector
from compliance.compliance_checker import create_compliance_checker
from handlers.waitlist_handler import create_waitlist_handler
from error_handling.error_handler import create_error_handler


def test_integration():
    """Test component integration"""
    print("Testing Phase 4 Integration...")
    
    # Test 1: PII + Compliance integration
    print("\n1. Testing PII + Compliance integration...")
    pii_detector = create_pii_detector()
    compliance_checker = create_compliance_checker()
    
    # Simulate user with PII
    user_text = "My phone is 9876543210"
    pii_result = pii_detector.detect_and_respond(user_text)
    
    if pii_result["should_interrupt"]:
        compliance_result = compliance_checker.check_response(pii_result["message"], "intent_classification")
        print(f"   ✅ PII detected, interrupt message compliant: {compliance_result.is_compliant}")
    
    # Test 2: Waitlist handler
    print("\n2. Testing waitlist handler...")
    waitlist = create_waitlist_handler()
    result = waitlist.add_to_waitlist("KYC/Onboarding", "morning", "test-conv-1")
    assert result["success"] == True
    assert "entry_id" in result
    print(f"   ✅ Waitlist entry created: {result['entry_id']}")
    
    # Test 3: Error handler
    print("\n3. Testing error handler...")
    error_handler = create_error_handler()
    
    # Test ValueError
    result = error_handler.handle(ValueError("Test error"), {"conversation_id": "test-1"})
    assert result["action"] in ["retry", "continue"]
    print(f"   ✅ ValueError handled with action: {result['action']}")
    
    # Test ConnectionError
    result = error_handler.handle(ConnectionError("Network down"), {"conversation_id": "test-2"})
    assert result["action"] in ["graceful_degradation", "human_handoff"]
    print(f"   ✅ ConnectionError handled with action: {result['action']}")
    
    print("\n✅ All integration tests passed!")
    print("\n⚠️  Full pipeline test requires:")
    print("   - Phase 1 components (VAD, STT, TTS)")
    print("   - Phase 2 MCP server running")
    print("   - Phase 3 orchestrator")
    print("   - Groq API key configured")


if __name__ == "__main__":
    test_integration()
