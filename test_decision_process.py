"""Test script for decision process and phone recognizer fixes."""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test text from demo
TEST_TEXT = """Here are a few example sentences we currently support:

Hi, my name is David Johnson and I'm originally from Liverpool.
My credit card number is 4095-2609-9393-4932 and my crypto wallet id is 16Yeky6GMjeNkAiNcBY7ZhrLoMSgg1BoyZ.

On 11/10/2024 I visited www.microsoft.com and sent an email to test@presidio.site,  from IP 192.168.0.1.

My passport: 191280342 and my phone number: (212) 555-1234.

This is a valid International Bank Account Number: IL150120690000003111111 . Can you please check the status on bank account 954567876544?

Kate's social security number is 078-05-1126.  Her driver license? it is 1234567A."""


def test_analyze_with_decision_process():
    """Test /analyze endpoint with decision process enabled."""
    print("=" * 80)
    print("TEST: /analyze with decision process")
    print("=" * 80)

    response = requests.post(
        f"{BASE_URL}/analyze",
        json={
            "text": TEST_TEXT,
            "return_decision_process": True,
            "score_threshold": 0.35
        }
    )

    if response.status_code != 200:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(response.text)
        return

    data = response.json()

    print(f"\n✅ SUCCESS: Found {len(data['findings'])} entities")
    print(f"\nSummary: {json.dumps(data['summary'], indent=2)}")

    # Check for phone number false positives
    phone_findings = [f for f in data['findings'] if f['entity_type'] == 'PHONE_NUMBER']
    print(f"\n📞 Phone numbers detected: {len(phone_findings)}")

    if len(phone_findings) > 2:
        print(f"⚠️  WARNING: Too many phone numbers! Should be ~1-2, got {len(phone_findings)}")
        for pf in phone_findings:
            print(f"  - '{pf['text']}' (score: {pf['score']})")
    else:
        print(f"✅ Phone detection looks good!")

    # Check for decision process fields
    print(f"\n🔍 Checking decision process fields...")
    findings_with_explanation = [f for f in data['findings'] if 'analysis_explanation' in f]

    if not findings_with_explanation:
        print("❌ ERROR: No analysis_explanation fields found!")
        return

    print(f"✅ Found {len(findings_with_explanation)} findings with explanations")

    # Show sample explanation
    sample = findings_with_explanation[0]
    print(f"\n📋 Sample explanation for '{sample['text']}':")
    exp = sample['analysis_explanation']

    required_fields = ['recognizer', 'original_score']
    optional_fields = ['pattern_name', 'pattern', 'validation_result',
                      'score_context_improvement', 'supportive_context_word',
                      'textual_explanation']

    # Check required fields
    for field in required_fields:
        if field in exp:
            print(f"  ✅ {field}: {exp[field]}")
        else:
            print(f"  ❌ MISSING: {field}")

    # Check optional fields
    for field in optional_fields:
        if field in exp and exp[field] is not None:
            value = exp[field]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  ✅ {field}: {value}")

    # Show a few more examples
    print(f"\n📊 First 5 findings with explanations:")
    for i, finding in enumerate(findings_with_explanation[:5], 1):
        exp = finding['analysis_explanation']
        pattern_info = f" - {exp.get('pattern_name', 'N/A')}" if 'pattern_name' in exp else ""
        print(f"  {i}. {finding['entity_type']:20s} | {finding['text']:30s} | {exp['recognizer']}{pattern_info}")


def test_anonymize_advanced():
    """Test /anonymize-advanced endpoint."""
    print("\n" + "=" * 80)
    print("TEST: /anonymize-advanced with replace operator")
    print("=" * 80)

    response = requests.post(
        f"{BASE_URL}/anonymize-advanced",
        json={
            "text": TEST_TEXT,
            "operator": "replace",
            "score_threshold": 0.35
        }
    )

    if response.status_code != 200:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(response.text)
        return

    data = response.json()

    print(f"\n✅ SUCCESS: Anonymized text")
    print(f"\nSummary: {json.dumps(data['summary'], indent=2)}")

    # Check for phone number false positives in anonymized text
    phone_count = data['anonymized_text'].count('<PHONE_NUMBER>')
    print(f"\n📞 <PHONE_NUMBER> placeholders in output: {phone_count}")

    if phone_count > 2:
        print(f"⚠️  WARNING: Too many phone numbers! Should be ~1-2, got {phone_count}")
    else:
        print(f"✅ Phone replacement looks good!")

    # Show snippet
    print(f"\n📝 Anonymized text snippet (first 200 chars):")
    print(data['anonymized_text'][:200] + "...")


def main():
    """Run all tests."""
    print("\n🧪 Testing Decision Process and Phone Recognizer Fixes\n")

    try:
        test_analyze_with_decision_process()
        test_anonymize_advanced()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nKey improvements:")
        print("  1. Decision process fields now populate via .to_dict() method")
        print("  2. Phone recognizer patterns tightened to reduce false positives")
        print("  3. All optional fields (pattern_name, pattern, validation_result, etc.) included")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
