"""Comprehensive tests for the Prime Anonymizer API."""

import json
import pytest
import requests
from typing import Any, Dict

# Test configuration
BASE_URL = "http://localhost:8000"
ANONYMIZE_URL = f"{BASE_URL}/anonymize"


class TestAnonymizeEndpoint:
    """Test cases for the /anonymize endpoint."""

    def test_person_email_phone_in_nested_structure(self):
        """Test redaction of PERSON, EMAIL, PHONE in nested dicts and lists."""
        payload = {
            "user": "Ada Lovelace",
            "contact": {
                "email": "ada@compute.org",
                "phone": "+1-555-123-4567"
            },
            "notes": ["Ada Lovelace met Ada Lovelace."],
            "metadata": {
                "created_by": "Charles Babbage",
                "contacts": [
                    {"name": "Alan Turing", "email": "alan@enigma.com"},
                    {"name": "Grace Hopper", "phone": "+1-555-987-6543"}
                ]
            }
        }

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Check structure is preserved
        assert isinstance(result, dict)
        assert "user" in result
        assert "contact" in result
        assert isinstance(result["contact"], dict)
        assert "notes" in result
        assert isinstance(result["notes"], list)
        assert len(result["notes"]) == 1

        # Check PII is anonymized
        assert result["user"].startswith("<PERSON")
        assert result["contact"]["email"].startswith("<EMAIL_ADDRESS")
        assert result["contact"]["phone"].startswith("<PHONE_NUMBER")

        # Check deterministic behavior: same person should get same token
        ada_token = result["user"]
        assert ada_token in result["notes"][0]
        # The note should contain the same token twice
        note_tokens = [token for token in result["notes"][0].split() if token.startswith("<PERSON")]
        assert all(token == ada_token for token in note_tokens)

    def test_preserves_non_string_types(self):
        """Test that numbers, booleans, and nulls are preserved exactly."""
        payload = {
            "name": "John Smith",
            "age": 42,
            "height": 5.9,
            "active": True,
            "inactive": False,
            "notes": None,
            "scores": [95, 87.5, None, True, False],
            "metadata": {
                "count": 0,
                "factor": 3.14159
            }
        }

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Check non-string values are preserved
        assert result["age"] == 42
        assert result["height"] == 5.9
        assert result["active"] is True
        assert result["inactive"] is False
        assert result["notes"] is None

        # Check list preserves types
        assert result["scores"][0] == 95
        assert result["scores"][1] == 87.5
        assert result["scores"][2] is None
        assert result["scores"][3] is True
        assert result["scores"][4] is False

        # Check nested object preserves types
        assert result["metadata"]["count"] == 0
        assert result["metadata"]["factor"] == 3.14159

        # Only string should be anonymized
        assert result["name"].startswith("<PERSON")

    def test_deterministic_within_request_mapping(self):
        """Test that same values get same tokens within a single request."""
        payload = {
            "person1": "Alice Johnson",
            "person2": "Bob Wilson",
            "person3": "Alice Johnson",  # Same as person1
            "emails": [
                "alice@example.com",
                "bob@test.org",
                "alice@example.com"  # Same as first email
            ],
            "text": "Alice Johnson emailed alice@example.com to Bob Wilson at bob@test.org"
        }

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Same person should get same token
        assert result["person1"] == result["person3"]
        assert result["person1"] != result["person2"]

        # Same email should get same token
        assert result["emails"][0] == result["emails"][2]
        assert result["emails"][0] != result["emails"][1]

        # Text should use the same tokens
        text_tokens = result["text"]
        assert result["person1"] in text_tokens  # Alice's token
        assert result["person2"] in text_tokens  # Bob's token
        assert result["emails"][0] in text_tokens  # Alice's email token
        assert result["emails"][1] in text_tokens  # Bob's email token

    def test_large_payload_under_limit(self):
        """Test handling of large-ish payload under the 2 MiB limit."""
        # Create a payload with many repeated names and emails
        people = []
        for i in range(100):
            people.append({
                "name": f"Person {i % 10}",  # Reuse names for deterministic testing
                "email": f"person{i % 10}@company.com",  # Reuse emails
                "phone": f"+1-555-{i:03d}-{i:04d}",
                "description": f"Person {i % 10} works at company and can be reached at person{i % 10}@company.com"
            })

        payload = {
            "company": "Acme Corporation",
            "employees": people,
            "total_count": len(people)
        }

        # Verify payload is under limit (should be much smaller than 2 MiB)
        payload_bytes = len(json.dumps(payload).encode('utf-8'))
        assert payload_bytes < 2 * 1024 * 1024

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Check structure preserved
        assert "employees" in result
        assert len(result["employees"]) == 100
        assert result["total_count"] == 100

        # Check deterministic behavior: same names should get same tokens
        name_tokens = {}
        email_tokens = {}

        for employee in result["employees"]:
            name_token = employee["name"]
            email_token = employee["email"]

            # Extract original indices to check deterministic mapping
            phone = employee["phone"]
            idx = int(phone.split("-")[1])
            original_idx = idx % 10

            if original_idx not in name_tokens:
                name_tokens[original_idx] = name_token
                email_tokens[original_idx] = email_token
            else:
                # Same original person should have same tokens
                assert name_tokens[original_idx] == name_token
                assert email_tokens[original_idx] == email_token

    def test_strategy_hash_returns_hashed_values(self):
        """Test that strategy=hash returns hash-based replacements."""
        payload = {
            "name": "John Doe",
            "email": "john@example.com"
        }

        response = requests.post(ANONYMIZE_URL, json=payload, params={"strategy": "hash"})
        assert response.status_code == 200

        result = response.json()

        # Hash strategy should still use angle bracket format but with hash suffixes
        assert result["name"].startswith("<PERSON_")
        assert result["email"].startswith("<EMAIL_ADDRESS_")

        # Hash tokens should be different from replace tokens
        replace_response = requests.post(ANONYMIZE_URL, json=payload, params={"strategy": "replace"})
        replace_result = replace_response.json()

        assert result["name"] != replace_result["name"]
        assert result["email"] != replace_result["email"]

    def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 error."""
        # Send malformed JSON
        response = requests.post(
            ANONYMIZE_URL,
            data='{"name": "John", "age":}',  # Invalid JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

        error = response.json()
        assert "error" in error or "detail" in error

    def test_empty_body_returns_400(self):
        """Test that empty request body returns 400."""
        response = requests.post(ANONYMIZE_URL, data="", headers={"Content-Type": "application/json"})
        assert response.status_code == 400

    def test_payload_over_limit_returns_413(self):
        """Test that payload over 2 MiB limit returns 413."""
        # Create a payload just over 2 MiB
        large_string = "x" * (2 * 1024 * 1024 + 1000)  # Just over 2 MiB
        payload = {"data": large_string}

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 413

        error = response.json()
        assert "error" in error or "detail" in error

    def test_invalid_strategy_returns_400(self):
        """Test that invalid strategy parameter returns 400."""
        payload = {"name": "John Doe"}

        response = requests.post(ANONYMIZE_URL, json=payload, params={"strategy": "invalid"})
        assert response.status_code == 400

        error = response.json()
        assert "error" in error or "detail" in error

    def test_invalid_entities_returns_400(self):
        """Test that invalid entities parameter returns 400."""
        payload = {"name": "John Doe"}

        response = requests.post(ANONYMIZE_URL, json=payload, params={"entities": "INVALID_ENTITY"})
        assert response.status_code == 400

        error = response.json()
        assert "error" in error or "detail" in error

    def test_custom_entities_parameter(self):
        """Test that custom entities parameter works correctly."""
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-1234"
        }

        # Only anonymize PERSON entities
        response = requests.post(ANONYMIZE_URL, json=payload, params={"entities": "PERSON"})
        assert response.status_code == 200

        result = response.json()

        # Only name should be anonymized
        assert result["name"].startswith("<PERSON")
        assert result["email"] == "john@example.com"  # Should remain unchanged
        assert result["phone"] == "+1-555-1234"  # Should remain unchanged

    def test_array_as_root_element(self):
        """Test that arrays can be the root element."""
        payload = [
            {"name": "Alice", "email": "alice@test.com"},
            {"name": "Bob", "email": "bob@test.com"},
            {"name": "Alice", "email": "alice@test.com"}  # Duplicate for deterministic test
        ]

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Should be a list
        assert isinstance(result, list)
        assert len(result) == 3

        # Check deterministic behavior
        assert result[0]["name"] == result[2]["name"]  # Same Alice token
        assert result[0]["email"] == result[2]["email"]  # Same email token
        assert result[0]["name"] != result[1]["name"]  # Different from Bob

    def test_string_as_root_element(self):
        """Test that strings can be the root element."""
        payload = "John Doe called Alice Johnson at +1-555-1234"

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Should be a string with PII anonymized
        assert isinstance(result, str)
        assert "<PERSON" in result
        assert "<PHONE_NUMBER" in result
        assert "John Doe" not in result
        assert "Alice Johnson" not in result
        assert "+1-555-1234" not in result

    def test_complex_nested_structure(self):
        """Test deeply nested and complex JSON structures."""
        payload = {
            "company": {
                "name": "Tech Corp",
                "ceo": "John Smith",
                "employees": [
                    {
                        "personal": {
                            "name": "Alice Johnson",
                            "contacts": {
                                "email": "alice@techcorp.com",
                                "phone": "+1-555-0001"
                            }
                        },
                        "projects": [
                            {
                                "name": "Project Alpha",
                                "team": ["Alice Johnson", "Bob Wilson"],
                                "contact_info": {
                                    "lead_email": "alice@techcorp.com"
                                }
                            }
                        ]
                    }
                ]
            }
        }

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()

        # Navigate deep structure
        employee = result["company"]["employees"][0]
        project = employee["projects"][0]

        # Check that Alice gets the same token everywhere
        alice_token = employee["personal"]["name"]
        assert alice_token.startswith("<PERSON")
        assert alice_token in project["team"]

        # Check that email gets the same token everywhere
        email_token = employee["personal"]["contacts"]["email"]
        assert email_token.startswith("<EMAIL_ADDRESS")
        assert project["contact_info"]["lead_email"] == email_token

    def test_multiple_entity_types_detection(self):
        """Test detection of various PII entity types."""
        payload = {
            "profile": {
                "name": "John Doe",
                "ssn": "123-45-6789",
                "email": "john@example.com",
                "phone": "+1-555-123-4567",
                "credit_card": "4532-1234-5678-9012",
                "address": "123 Main Street, New York, NY",
                "website": "https://johndoe.com",
                "ip_address": "192.168.1.1",
                "birth_date": "1990-05-15"
            }
        }

        response = requests.post(ANONYMIZE_URL, json=payload)
        assert response.status_code == 200

        result = response.json()
        profile = result["profile"]

        # Check that various entity types are detected and anonymized
        # Note: Exact detection depends on Presidio's models, but these should commonly be detected
        assert profile["name"].startswith("<PERSON")
        assert profile["email"].startswith("<EMAIL_ADDRESS")
        assert profile["phone"].startswith("<PHONE_NUMBER")

        # These may or may not be detected depending on Presidio configuration
        # Just ensure they're either anonymized or left as-is (both are valid)
        assert isinstance(profile["ssn"], str)
        assert isinstance(profile["credit_card"], str)
        assert isinstance(profile["website"], str)


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_anonymize.py -v
    pytest.main([__file__, "-v"])