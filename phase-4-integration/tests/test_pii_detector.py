"""
Tests for PII Detector
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from compliance.pii_detector import create_pii_detector, PIIType


def test_pii_detector():
    """Test PII detection patterns"""
    detector = create_pii_detector()
    
    print("Testing PII Detector...")
    
    test_cases = [
        ("My phone is 9876543210", PIIType.PHONE),
        ("Call me at +91 98765 43210", PIIType.PHONE),
        ("Email me at test@example.com", PIIType.EMAIL),
        ("My PAN is ABCDE1234F", PIIType.PAN),
        ("Aadhaar: 1234 5678 9012", PIIType.AADHAAR),
        ("Account number 123456789012", PIIType.ACCOUNT_NUMBER),
        ("Just a normal message", None),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_type in test_cases:
        detections = detector.detect(text)
        
        if expected_type is None:
            # Should have no detections
            if len(detections) == 0:
                print(f"  ✅ '{text[:30]}...' → No PII detected")
                passed += 1
            else:
                print(f"  ❌ '{text[:30]}...' → Should be clean but found: {[d.pii_type.value for d in detections]}")
                failed += 1
        else:
            # Should detect expected type
            types_found = [d.pii_type for d in detections]
            if expected_type in types_found:
                print(f"  ✅ '{text[:30]}...' → Found {expected_type.value}")
                passed += 1
            else:
                print(f"  ❌ '{text[:30]}...' → Expected {expected_type.value}, found: {[t.value for t in types_found]}")
                failed += 1
                
    print(f"\nPassed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    # Test interrupt response
    print("\nTesting interrupt response...")
    result = detector.detect_and_respond("My number is 9876543210")
    assert result["should_interrupt"] == True
    assert "security" in result["message"].lower()
    print("  ✅ Interrupt response generated correctly")
    
    if failed == 0:
        print("\n✅ All PII detector tests passed!")
    else:
        print(f"\n⚠️ {failed} tests failed")


if __name__ == "__main__":
    test_pii_detector()
