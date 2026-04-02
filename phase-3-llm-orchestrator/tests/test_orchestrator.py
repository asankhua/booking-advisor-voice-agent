"""
Tests for Orchestrator
Note: Requires Groq API key and MCP server running
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import create_orchestrator


def test_orchestrator_components():
    """Test orchestrator initialization"""
    print("Testing Orchestrator...")
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  GROQ_API_KEY not set. Skipping integration tests.")
        print("   Set GROQ_API_KEY in environment to run full tests.")
        return False
        
    try:
        print("\n1. Testing orchestrator initialization...")
        orch = create_orchestrator()
        print("   ✅ Orchestrator initialized")
        
        print("\n2. Testing compliance check...")
        result = orch._check_compliance("My phone is 9876543210")
        assert result["should_interrupt"] == True
        print("   ✅ PII detection working")
        
        print("\n3. Testing state machine...")
        from core.state_machine import StateMachine, State
        sm = StateMachine()
        assert sm.current_state == State.GREETING
        print("   ✅ State machine initialized")
        
        print("\n✅ Orchestrator component tests passed!")
        print("\n⚠️  Full integration test requires:")
        print("   - MCP server running on localhost:8000")
        print("   - Valid GROQ_API_KEY")
        print("   Run: python -c 'from core.orchestrator import create_orchestrator; o = create_orchestrator(); print(o.process(\"test-1\", \"Hello\"))'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_orchestrator_components()
