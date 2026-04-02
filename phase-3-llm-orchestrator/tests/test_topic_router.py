"""
Tests for Topic Router
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlu.topic_router import create_topic_router, Topic


def test_topic_router():
    """Test topic routing"""
    router = create_topic_router()
    
    print("Testing Topic Router...")
    
    test_cases = [
        ("I need KYC verification", Topic.KYC_ONBOARDING),
        ("New account setup", Topic.KYC_ONBOARDING),
        ("Set up a SIP", Topic.SIP_MANDATES),
        ("Start monthly investment", Topic.SIP_MANDATES),
        ("Need my tax statement", Topic.STATEMENTS_TAX),
        ("Download account statement", Topic.STATEMENTS_TAX),
        ("How do I withdraw money?", Topic.WITHDRAWALS),
        ("Redeem my funds", Topic.WITHDRAWALS),
        ("Update my nominee", Topic.ACCOUNT_CHANGES),
        ("Change my address", Topic.ACCOUNT_CHANGES),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = router.route(text)
        status = "✅" if result.topic == expected else "❌"
        if result.topic == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{text[:40]}...' → {result.topic.value} (prefix: {result.booking_code_prefix})")
        
    print(f"\nPassed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✅ All topic router tests passed!")
    else:
        print(f"\n⚠️  {failed} tests failed")
        
    return failed == 0


if __name__ == "__main__":
    test_topic_router()
