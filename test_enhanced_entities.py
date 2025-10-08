"""Test script for enhanced entity detection."""

import json
import requests

API_URL = "https://prime.rnd.2bv.io"

# Test cases with various entity types
test_cases = [
    {
        "name": "Phone Numbers - Various Formats",
        "entities": ["PHONE_NUMBER"],
        "data": {
            "contact1": "+1-555-123-4567",
            "contact2": "(555) 123-4567",
            "contact3": "555-123-4567",
            "contact4": "+44 20 7123 4567",
            "contact5": "5551234567",
        }
    },
    {
        "name": "Email Addresses",
        "entities": ["EMAIL_ADDRESS"],
        "data": {
            "email1": "john.doe@example.com",
            "email2": "alice+tag@company.org",
            "email3": "support@subdomain.example.co.uk",
        }
    },
    {
        "name": "US SSN",
        "entities": ["US_SSN"],
        "data": {
            "ssn1": "123-45-6789",
            "ssn2": "987-65-4321",
        }
    },
    {
        "name": "Credit Cards",
        "entities": ["CREDIT_CARD"],
        "data": {
            "visa": "4532-1234-5678-9010",
            "mastercard": "5425-2334-3010-9903",
        }
    },
    {
        "name": "URLs and IPs",
        "entities": ["URL", "IP_ADDRESS"],
        "data": {
            "website": "https://example.com/path",
            "ip": "192.168.1.100",
        }
    },
    {
        "name": "Mixed PII",
        "entities": ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"],
        "data": {
            "employee": {
                "name": "Robert Smith",
                "email": "robert.smith@company.com",
                "phone": "+1-555-987-6543",
                "city": "San Francisco"
            },
            "emergency_contact": {
                "name": "Sarah Smith",
                "phone": "+1-555-111-2222",
                "email": "sarah@example.com"
            }
        }
    },
]


def test_anonymization(test_case):
    """Test a single anonymization case."""
    print(f"\n{'='*60}")
    print(f"Test: {test_case['name']}")
    print(f"Entities: {', '.join(test_case['entities'])}")
    print(f"{'='*60}")

    # Build request
    entities_param = ",".join(test_case['entities'])
    url = f"{API_URL}/anonymize?entities={entities_param}"

    print(f"\n📤 Input:")
    print(json.dumps(test_case['data'], indent=2))

    try:
        # Make request
        response = requests.post(url, json=test_case['data'], timeout=10)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Output (Status: {response.status_code}):")
            print(json.dumps(result, indent=2))

            # Analyze changes
            input_str = json.dumps(test_case['data'])
            output_str = json.dumps(result)

            if input_str == output_str:
                print(f"\n⚠️  WARNING: No changes detected - entities may not be working!")
            else:
                print(f"\n✅ SUCCESS: Entities were anonymized!")

        else:
            error = response.json()
            print(f"\n❌ Error (Status: {response.status_code}):")
            print(json.dumps(error, indent=2))

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")


def main():
    """Run all test cases."""
    print(f"\n{'='*60}")
    print(f"Testing Enhanced Entity Detection")
    print(f"API: {API_URL}")
    print(f"{'='*60}")

    for test_case in test_cases:
        test_anonymization(test_case)

    print(f"\n{'='*60}")
    print(f"All tests completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
