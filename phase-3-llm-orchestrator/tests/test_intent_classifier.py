"""
Tests for Intent Classifier
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlu.intent_classifier import create_intent_classifier, Intent


def test_intent_classifier():
    """Test intent classification"""
    classifier = create_intent_classifier()
    
    print("Testing Intent Classifier...")
    
    test_cases = [
        ("I want to book an appointment", Intent.BOOK_NEW),
        ("Schedule a meeting with advisor", Intent.BOOK_NEW),
        ("I need to reschedule my booking", Intent.RESCHEDULE),
        ("Can I change my slot to tomorrow?", Intent.RESCHEDULE),
        ("Cancel my appointment", Intent.CANCEL),
        ("I don't need the meeting anymore", Intent.CANCEL),
        ("What should I bring to the meeting?", Intent.WHAT_TO_PREPARE),
        ("What documents do I need?", Intent.WHAT_TO_PREPARE),
        ("When are you free next week?", Intent.CHECK_AVAILABILITY),
        ("What slots do you have?", Intent.CHECK_AVAILABILITY),
        ("What stock should I buy?", Intent.INVESTMENT_ADVICE),
        ("Recommend a good mutual fund", Intent.INVESTMENT_ADVICE),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = classifier.classify(text)
        status = "✅" if result.intent == expected else "❌"
        if result.intent == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{text[:40]}...' → {result.intent.value} (expected: {expected.value})")
        
    print(f"\nPassed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✅ All intent classifier tests passed!")
    else:
        print(f"\n⚠️  {failed} tests failed")
        
    return failed == 0


if __name__ == "__main__":
    test_intent_classifier()
