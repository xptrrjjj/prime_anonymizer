# Prime Anonymizer API - Complete Documentation

**Version:** 1.0.0
**Base URL (Production):** `https://prime.rnd.2bv.io`
**Base URL (Development):** `http://localhost:8000`

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Endpoint Reference](#endpoint-reference)
3. [Request Specification](#request-specification)
4. [Response Specification](#response-specification)
5. [Error Handling](#error-handling)
6. [Entity Types](#entity-types)
7. [Strategies](#strategies)
8. [Examples](#examples)
9. [Integration Guide](#integration-guide)

---

## Quick Start

```bash
# Basic usage - anonymize with default settings
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice@example.com"}'

# With specific strategy and entities
curl -X POST "http://localhost:8000/anonymize?strategy=replace&entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice@example.com"}'
```

---

## Endpoint Reference

### POST /anonymize

Anonymizes PII (Personally Identifiable Information) in JSON payloads.

**URL:** `/anonymize`
**Method:** `POST`
**Content-Type:** `application/json`

---

## Request Specification

### Query Parameters

| Parameter | Type | Required | Default | Valid Values | Description |
|-----------|------|----------|---------|--------------|-------------|
| `strategy` | string | **No** | `"replace"` | `"replace"`, `"hash"` | Anonymization strategy |
| `entities` | string | **No** | All supported entities | Comma-separated list | Entity types to detect and anonymize |

### Request Headers

```
Content-Type: application/json
```

### Request Body

- **Format:** Valid JSON (object, array, or primitive)
- **Max Size:** 2 MiB (2,097,152 bytes)
- **Encoding:** UTF-8

#### Body Rules
- ✅ Any valid JSON structure
- ✅ Nested objects and arrays
- ✅ Mixed data types (strings, numbers, booleans, null)
- ❌ Invalid JSON syntax
- ❌ Non-UTF-8 encoding
- ❌ Payloads > 2 MiB

---

## Response Specification

### Success Response (200 OK)

**Content-Type:** `application/json`

**Body:** The anonymized version of the input JSON with the same structure.

#### Response Characteristics
- ✅ Maintains exact JSON structure (keys, nesting, arrays)
- ✅ Preserves data types (numbers, booleans, null remain unchanged)
- ✅ Only string values containing PII are modified
- ✅ Deterministic within a request (same PII → same replacement token)
- ✅ Non-deterministic across requests (tokens reset per request)

### Example Success Response

**Input:**
```json
{
  "name": "Alice Johnson",
  "age": 30,
  "email": "alice@example.com",
  "active": true
}
```

**Output (strategy=replace):**
```json
{
  "name": "<PERSON_1>",
  "age": 30,
  "email": "<EMAIL_ADDRESS_1>",
  "active": true
}
```

---

## Error Handling

### Error Response Format

All errors return JSON with a `detail` field:

```json
{
  "detail": "Error description here"
}
```

### HTTP Status Codes

| Status | Error Type | Description | Example |
|--------|------------|-------------|---------|
| **400** | Bad Request | Invalid input | Invalid JSON, empty body, invalid parameters |
| **413** | Payload Too Large | Body exceeds 2 MiB | Request size > 2,097,152 bytes |
| **500** | Internal Server Error | Processing failed | Unexpected server error |

### Detailed Error Scenarios

#### 400 Bad Request

**Scenario 1: Empty Request Body**
```json
{
  "detail": "Empty request body"
}
```

**Scenario 2: Invalid JSON**
```json
{
  "detail": "Invalid JSON: Expecting ',' delimiter: line 2 column 5 (char 10)"
}
```

**Scenario 3: Invalid UTF-8 Encoding**
```json
{
  "detail": "Invalid UTF-8 encoding in request body"
}
```

**Scenario 4: Invalid Strategy**
```json
{
  "detail": "Invalid strategy. Must be 'replace' or 'hash'"
}
```

**Scenario 5: Invalid Entity Types**
```json
{
  "detail": "Invalid entities: INVALID_TYPE, ANOTHER_BAD_TYPE"
}
```

**Scenario 6: Invalid JSON Structure**
```json
{
  "detail": "Invalid JSON structure"
}
```

#### 413 Payload Too Large

```json
{
  "error": "Request payload too large (max 2 MiB)"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Anonymization processing failed"
}
```

---

## Entity Types

### Supported Entity Types (10 Total)

| Entity Type | Description | Example Input | Example Output (Replace) |
|-------------|-------------|---------------|--------------------------|
| `PERSON` | Person names | `"Alice Johnson"` | `"<PERSON_1>"` |
| `EMAIL_ADDRESS` | Email addresses | `"alice@example.com"` | `"<EMAIL_ADDRESS_1>"` |
| `PHONE_NUMBER` | Phone numbers (various formats) | `"+1-555-123-4567"` | `"<PHONE_NUMBER_1>"` |
| `CREDIT_CARD` | Credit card numbers | `"4532-1234-5678-9010"` | `"<CREDIT_CARD_1>"` |
| `IBAN` | International Bank Account Numbers | `"DE89370400440532013000"` | `"<IBAN_1>"` |
| `US_SSN` | US Social Security Numbers | `"123-45-6789"` | `"<US_SSN_1>"` |
| `LOCATION` | Geographic locations | `"San Francisco"`, `"123 Main St"` | `"<LOCATION_1>"` |
| `DATE_TIME` | Date and time values | `"2024-01-15T10:30:00Z"` | `"<DATE_TIME_1>"` |
| `IP_ADDRESS` | IP addresses (IPv4/IPv6) | `"192.168.1.100"` | `"<IP_ADDRESS_1>"` |
| `URL` | Web URLs | `"https://example.com"` | `"<URL_1>"` |

### Default Entity Types (When `entities` is omitted)

The API has a default set of entities configured in `app/config.py`:

```python
default_entities: List[str] = [
    "PERSON",
    "PHONE_NUMBER",
    "LOCATION"
]
```

**Note:** To detect all entity types, explicitly pass all types in the `entities` parameter.

### Using Entity Types

**Detect all entity types:**
```
?entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER,CREDIT_CARD,IBAN,US_SSN,LOCATION,DATE_TIME,IP_ADDRESS,URL
```

**Detect only specific types:**
```
?entities=PERSON,EMAIL_ADDRESS
```

**Use default types (PERSON, PHONE_NUMBER, LOCATION):**
```
(omit the entities parameter)
```

---

## Strategies

### Replace Strategy (Default)

**Parameter:** `strategy=replace` (or omit parameter)

**Behavior:**
- Replaces PII with token placeholders
- Format: `<ENTITY_TYPE_N>` where N is a counter
- Deterministic within a single request
- Same PII value → same token within one request
- Tokens reset for each new request

**Example:**
```json
// Input
{
  "users": ["Alice", "Bob", "Alice"],
  "message": "Alice sent a message to Bob"
}

// Output
{
  "users": ["<PERSON_1>", "<PERSON_2>", "<PERSON_1>"],
  "message": "<PERSON_1> sent a message to <PERSON_2>"
}
```

**Use Cases:**
- Demonstrating PII detection
- Testing and development
- Clear visual identification of PII

### Hash Strategy

**Parameter:** `strategy=hash`

**Behavior:**
- Replaces PII with hash values
- Uses cryptographic hashing
- Deterministic within a single request
- Same PII value → same hash within one request
- Hashes reset for each new request

**Example:**
```json
// Input
{
  "name": "Alice Johnson",
  "email": "alice@example.com"
}

// Output (example hash values)
{
  "name": "a1b2c3d4e5f6...",
  "email": "f6e5d4c3b2a1..."
}
```

**Use Cases:**
- Data masking for analytics
- Preserving referential integrity
- Pseudonymization

---

## Examples

### Example 1: Basic Anonymization (Default Settings)

**Request:**
```bash
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "+1-555-123-4567"
  }'
```

**Response:**
```json
{
  "name": "<PERSON_1>",
  "email": "alice@example.com",
  "phone": "<PHONE_NUMBER_1>"
}
```

**Note:** EMAIL_ADDRESS not anonymized (not in default entities).

### Example 2: Custom Entity Selection

**Request:**
```bash
curl -X POST "http://localhost:8000/anonymize?entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "+1-555-123-4567"
  }'
```

**Response:**
```json
{
  "name": "<PERSON_1>",
  "email": "<EMAIL_ADDRESS_1>",
  "phone": "+1-555-123-4567"
}
```

**Note:** PHONE_NUMBER not anonymized (not in entities parameter).

### Example 3: Hash Strategy

**Request:**
```bash
curl -X POST "http://localhost:8000/anonymize?strategy=hash&entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com"
  }'
```

**Response:**
```json
{
  "name": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
  "email": "3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a"
}
```

### Example 4: Nested Structure Preservation

**Request:**
```bash
curl -X POST "http://localhost:8000/anonymize?entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    "contacts": [
      {
        "name": "Bob Smith",
        "phone": "+1-555-987-6543"
      }
    ],
    "metadata": {
      "created_by": "Alice Johnson",
      "timestamp": 1633024800
    }
  }'
```

**Response:**
```json
{
  "customer": {
    "name": "<PERSON_1>",
    "email": "<EMAIL_ADDRESS_1>"
  },
  "contacts": [
    {
      "name": "<PERSON_2>",
      "phone": "<PHONE_NUMBER_1>"
    }
  ],
  "metadata": {
    "created_by": "<PERSON_1>",
    "timestamp": 1633024800
  }
}
```

**Note:** `"Alice Johnson"` appears twice → same token `<PERSON_1>`.

### Example 5: Type Preservation

**Request:**
```bash
curl -X POST "http://localhost:8000/anonymize?entities=PERSON" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "age": 30,
    "salary": 85000.50,
    "active": true,
    "notes": null
  }'
```

**Response:**
```json
{
  "name": "<PERSON_1>",
  "age": 30,
  "salary": 85000.50,
  "active": true,
  "notes": null
}
```

**Note:** Numbers, booleans, and null are never modified.

---

## Integration Guide

### JavaScript / TypeScript (Frontend)

```typescript
// Configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Client Function
async function anonymizeJSON(
  data: any,
  strategy: 'replace' | 'hash' = 'replace',
  entities?: string[]
): Promise<any> {
  // Build query parameters
  const params = new URLSearchParams();
  if (strategy) {
    params.append('strategy', strategy);
  }
  if (entities && entities.length > 0) {
    params.append('entities', entities.join(','));
  }

  const url = `${API_URL}/anonymize?${params.toString()}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Anonymization failed:', error);
    throw error;
  }
}

// Usage Example
const inputData = {
  name: 'Alice Johnson',
  email: 'alice@example.com',
  phone: '+1-555-123-4567'
};

try {
  const anonymized = await anonymizeJSON(
    inputData,
    'replace',
    ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER']
  );
  console.log('Anonymized:', anonymized);
} catch (error) {
  console.error('Error:', error.message);
}
```

### Python

```python
import requests
import json
from typing import Any, Dict, List, Optional

API_URL = "http://localhost:8000"

def anonymize_json(
    data: Any,
    strategy: str = "replace",
    entities: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Anonymize JSON data using the Prime Anonymizer API."""

    # Build query parameters
    params = {"strategy": strategy}
    if entities:
        params["entities"] = ",".join(entities)

    # Make request
    response = requests.post(
        f"{API_URL}/anonymize",
        params=params,
        headers={"Content-Type": "application/json"},
        json=data
    )

    # Handle response
    if response.status_code == 200:
        return response.json()
    else:
        error_detail = response.json().get("detail", "Unknown error")
        raise Exception(f"API Error {response.status_code}: {error_detail}")

# Usage example
if __name__ == "__main__":
    input_data = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "+1-555-123-4567"
    }

    try:
        anonymized = anonymize_json(
            input_data,
            strategy="replace",
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
        )
        print(json.dumps(anonymized, indent=2))
    except Exception as e:
        print(f"Error: {e}")
```

### cURL Examples

```bash
# Example 1: Minimal request (defaults)
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson"}'

# Example 2: With strategy
curl -X POST "http://localhost:8000/anonymize?strategy=hash" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson"}'

# Example 3: With entities
curl -X POST "http://localhost:8000/anonymize?entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Example 4: Full configuration
curl -X POST "http://localhost:8000/anonymize?strategy=replace&entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER" \
  -H "Content-Type: application/json" \
  -d @input.json

# Example 5: With error handling
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
```

---

## CORS Configuration

The API has CORS enabled for the following origins:

- `http://localhost:3000` (Next.js default dev server)
- `http://localhost:3001` (Alternative dev port)
- `https://prime.rnd.2bv.io` (Production backend)
- `https://prime-ui.rnd.2bv.io` (Production frontend)

**Allowed Methods:** All (`*`)
**Allowed Headers:** All (`*`)
**Credentials:** Enabled

---

## Performance Characteristics

### Latency
- **Typical:** 50-200ms for payloads < 100KB
- **Factors:**
  - JSON size
  - Number of entity types selected
  - Nesting depth
  - Number of PII instances

### Limits
- **Max Payload Size:** 2 MiB (2,097,152 bytes)
- **Request Timeout:** 30 seconds (configurable)

### Optimization Tips
1. Only specify entity types you need
2. Use smaller payloads when possible
3. Consider batching vs individual requests based on use case

---

## Logging and Auditing

The API logs all requests to:
1. **Console/File Logs** (JSON format)
2. **SQLite Database** (`data/app.db`)

### Logged Information
- Request ID (UUID)
- Timestamp
- Client IP address
- HTTP status code
- Processing time (ms)
- Payload size (bytes)
- PII counts by entity type
- Error messages (if any)

### Privacy
- ✅ Metadata is logged
- ❌ Raw payloads are **never** stored
- ❌ PII values are **never** logged

---

## Configuration (Environment Variables)

All settings can be configured via environment variables with the `ANONYMIZER_` prefix:

```bash
# Database
ANONYMIZER_DB_PATH=/app/data/app.db

# Logging
ANONYMIZER_LOG_FILE_PATH=/app/logs/app.log
ANONYMIZER_LOG_MAX_BYTES=10485760  # 10MB
ANONYMIZER_LOG_BACKUP_COUNT=5
ANONYMIZER_LOG_LEVEL=INFO

# Request Limits
ANONYMIZER_MAX_REQUEST_SIZE=2097152  # 2 MiB
ANONYMIZER_REQUEST_TIMEOUT=30.0

# Default Entities (comma-separated)
ANONYMIZER_DEFAULT_ENTITIES=PERSON,PHONE_NUMBER,LOCATION

# spaCy Model
ANONYMIZER_SPACY_MODEL=en_core_web_lg
```

---

## Troubleshooting

### Common Issues

**Issue 1: CORS Error in Browser**
```
Access to fetch at 'http://localhost:8000/anonymize' from origin
'http://localhost:3000' has been blocked by CORS policy
```
**Solution:** Ensure frontend origin is in CORS `allow_origins` list.

**Issue 2: 413 Payload Too Large**
```
{"error": "Request payload too large (max 2 MiB)"}
```
**Solution:** Reduce payload size or increase `ANONYMIZER_MAX_REQUEST_SIZE`.

**Issue 3: Invalid JSON Error**
```
{"detail": "Invalid JSON: ..."}
```
**Solution:** Validate JSON syntax before sending. Use tools like `jq` or online validators.

**Issue 4: Entity Not Detected**
```
// Input: {"ssn": "123-45-6789"}
// Output: {"ssn": "123-45-6789"}  // Not anonymized
```
**Solution:** Ensure entity type is in `entities` parameter (e.g., `?entities=US_SSN`).

**Issue 5: Empty Response**
```
{"detail": "Empty request body"}
```
**Solution:** Ensure request body is not empty and Content-Type header is set.

---

## FAQ

**Q: Is the anonymization reversible?**
A: No. The API does not store mappings. Anonymization is one-way.

**Q: Are tokens consistent across requests?**
A: No. Tokens are deterministic within a single request but reset for each new request.

**Q: Can I anonymize non-JSON data?**
A: No. The API only accepts valid JSON payloads.

**Q: What happens to non-string values?**
A: Numbers, booleans, and null are never modified. Only strings are processed.

**Q: Can I add custom entity types?**
A: Not currently. Entity types are defined by Microsoft Presidio.

**Q: Is there rate limiting?**
A: Not currently implemented. Consider adding for production use.

**Q: Can I use this in production?**
A: The API is production-ready but consider adding authentication and rate limiting.

---

## Version History

**v1.0.0** (2024-10-08)
- Initial release
- Support for 10 entity types
- Replace and hash strategies
- CORS enabled
- SQLite audit logging

---

## Support

For issues, questions, or contributions:
- Review backend logs in `logs/app.log`
- Check SQLite database `data/app.db` for audit logs
- Consult FastAPI documentation: https://fastapi.tiangolo.com

---

**Last Updated:** 2024-10-08
**API Version:** 1.0.0
