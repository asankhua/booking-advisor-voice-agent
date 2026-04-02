"""
Tests for Compliance Checker
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from compliance.compliance_checker import create_compliance_checker


def test_compliance_checker():
    """Test compliance validation"""
    checker = create_compliance_checker()
    
    print("Testing Compliance Checker...")
    
    # Test 1: Disclaimer detection
    print("\n1. Testing disclaimer detection...")
    compliant_text = "Hello! I cannot provide investment advice. How can I help?"
    result = checker.check_response(compliant_text, "greeting")
    assert result.is_compliant == True
    print("  ✅ Disclaimer detected in greeting")
    
    # Test 2: Missing disclaimer
    print("\n2. Testing missing disclaimer...")
    non_compliant = "Hello! How can I help you?"
    result = checker.check_response(non_compliant, "greeting")
    assert result.is_compliant == False
    assert result.violation_type == "missing_disclaimer"
    print("  ✅ Missing disclaimer detected")
    
    # Test 3: Investment advice seeking
    print("\n3. Testing advice seeking detection...")
    advice_text = "What stock should I buy?"
    result = checker.check_user_intent(advice_text)
    assert result.is_compliant == False
    assert result.violation_type == "advice_seeking"
    print("  ✅ Advice seeking detected")
    
    # Test 4: Advice refusal message
    print("\n4. Testing advice refusal message...")
    refusal = checker.get_advice_refusal()
    assert "cannot provide investment advice" in refusal
    print("  ✅ Refusal message generated")
    
    # Test 5: Disclaimer template
    print("\n5. Testing disclaimer template...")
    disclaimer = checker.get_disclaimer()
    assert "cannot provide investment advice" in disclaimer
    print("  ✅ Disclaimer template generated")
    
    print("\n✅ All compliance checker tests passed!")


if __name__ == "__main__":
    test_compliance_checker()
