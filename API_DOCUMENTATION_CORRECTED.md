# Prime Anonymizer API - Complete Documentation

**Version:** 1.0.0
**Base URL (Production):** `https://prime.rnd.2bv.io`
**Base URL (Development):** `http://localhost:8000`

---

## ⚠️ IMPORTANT: Entity Type Limitations

**TESTED ON PRODUCTION - ACTUAL BEHAVIOR:**

### Working Entity Types (3 only):
- ✅ `PERSON` - Names (high accuracy)
- ⚠️ `PHONE_NUMBER` - Very limited detection (see notes)
- ✅ `LOCATION` - Cities, places (moderate accuracy)

### Invalid Entity Types (API will reject):
- ❌ `EMAIL_ADDRESS`
- ❌ `US_SSN`
- ❌ `IBAN`
- ❌ `DATE_TIME`
- ❌ `IP_ADDRESS`
- ❌ `URL`
- ❌ `CREDIT_CARD`

**These are NOT supported by the current Presidio configuration and will return error 400.**

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Endpoint Reference](#endpoint-reference)
3. [Request Specification](#request-specification)
4. [Response Specification](#response-specification)
5. [Error Handling](#error-handling)
6. [Entity Types (Reality Check)](#entity-types-reality-check)
7. [Strategies](#strategies)
8. [Examples](#examples)
9. [Integration Guide](#integration-guide)

---

## Quick Start

```bash
# Basic usage - only PERSON, PHONE_NUMBER, LOCATION detected by default
curl -X POST "https://prime.rnd.2bv.io/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "city": "San Francisco"}'

# Explicit entity selection (only PERSON and LOCATION work reliably)
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON,LOCATION" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "city": "San Francisco"}'
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
| `entities` | string | **No** | `"PERSON,PHONE_NUMBER,LOCATION"` | Comma-separated: `PERSON`, `PHONE_NUMBER`, `LOCATION` | Entity types to detect |

### Request Headers

```
Content-Type: application/json
```

### Request Body

- **Format:** Valid JSON (object, array, or primitive)
- **Max Size:** 2 MiB (2,097,152 bytes)
- **Encoding:** UTF-8

---

## Response Specification

### Success Response (200 OK)

**Content-Type:** `application/json`

**Body:** The anonymized version of the input JSON with the same structure.

#### Response Characteristics
- ✅ Maintains exact JSON structure
- ✅ Preserves data types (numbers, booleans, null unchanged)
- ✅ Only strings with detected PII are modified
- ✅ Deterministic within a request (same PII → same token)
- ❌ **Phone numbers often NOT detected** (format-specific)

### Example Success Response

**Input:**
```json
{
  "name": "Alice Johnson",
  "age": 30,
  "city": "San Francisco",
  "active": true
}
```

**Output (default entities):**
```json
{
  "name": "<PERSON_1>",
  "age": 30,
  "city": "<LOCATION_1>",
  "active": true
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error description here"
}
```

### HTTP Status Codes

| Status | Error Type | Common Causes |
|--------|------------|---------------|
| **400** | Bad Request | Invalid JSON, invalid entity types, empty body |
| **413** | Payload Too Large | Body > 2 MiB |
| **500** | Internal Server Error | Processing failure |

### Common Errors

#### Invalid Entity Types
```bash
# Request with unsupported entities
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Response (400)
{
  "detail": "Invalid entities: EMAIL_ADDRESS"
}
```

#### Empty Request Body
```json
{
  "detail": "Empty request body"
}
```

#### Invalid JSON
```json
{
  "detail": "Invalid JSON: Expecting ',' delimiter: line 2 column 5 (char 10)"
}
```

---

## Entity Types (Reality Check)

### Actually Working Entities

| Entity | Accuracy | Notes |
|--------|----------|-------|
| `PERSON` | ✅ High | Reliably detects names like "Alice Johnson", "Dr. Smith" |
| `LOCATION` | ✅ Medium | Detects cities ("San Francisco"), some addresses |
| `PHONE_NUMBER` | ❌ Very Poor | **Rarely works** - see details below |

### Phone Number Detection (BROKEN)

**PHONE_NUMBER entity is essentially non-functional for common formats.**

❌ **NOT Detected:**
- `"+1-555-123-4567"` (US format with dashes)
- `"+1-555-987-6543"`
- `"+1 (555) 123-4567"` (US format with parens)
- Most real-world phone formats

**Test Result:**
```json
// Input with entities=PERSON,PHONE_NUMBER
{
  "employee": {
    "full_name": "Robert Smith",
    "phone": "+1-555-987-6543"
  },
  "emergency_contact": {
    "name": "Sarah Smith",
    "phone": "+1-555-111-2222"
  }
}

// Output - phones NOT anonymized
{
  "employee": {
    "full_name": "<PERSON_1>",
    "phone": "+1-555-987-6543"  // ❌ NOT detected
  },
  "emergency_contact": {
    "name": "<PERSON_2>",
    "phone": "+1-555-111-2222"  // ❌ NOT detected
  }
}
```

**Conclusion:** Do NOT rely on PHONE_NUMBER detection.

### Unsupported Entities

These will cause **400 Bad Request** errors:

- ❌ `EMAIL_ADDRESS` - Not available in Presidio config
- ❌ `US_SSN` - Not available
- ❌ `CREDIT_CARD` - Not available
- ❌ `IBAN` - Not available
- ❌ `DATE_TIME` - Not available
- ❌ `IP_ADDRESS` - Not available
- ❌ `URL` - Not available

### Default Entities

When `entities` parameter is omitted:
```python
["PERSON", "PHONE_NUMBER", "LOCATION"]
```

**Recommendation:** Only use `PERSON` and `LOCATION` for reliable results.

---

## Strategies

### Replace Strategy (Default)

**Parameter:** `strategy=replace` (or omit)

**Behavior:**
- Replaces PII with token format: `<ENTITY_TYPE_N>`
- Deterministic within one request
- Same value → same token in one request
- Tokens reset for each new request

**Example:**
```json
// Input
{
  "users": ["Alice", "Bob", "Alice"],
  "note": "Alice works with Bob"
}

// Output
{
  "users": ["<PERSON_1>", "<PERSON_2>", "<PERSON_1>"],
  "note": "<PERSON_1> works with <PERSON_2>"
}
```

### Hash Strategy

**Parameter:** `strategy=hash`

**Behavior:**
- Replaces with SHA-256 hash (8 chars)
- Format: `<ENTITY_TYPE_hash>`
- Deterministic within one request

**Example:**
```json
// Input
{
  "name": "Alice Johnson"
}

// Output
{
  "name": "<PERSON_a1b2c3d4>"
}
```

---

## Examples

### Example 1: Basic - Only PERSON Detection

**Request:**
```bash
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON" \
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
  "phone": "+1-555-123-4567"
}
```

### Example 2: PERSON + LOCATION

**Request:**
```bash
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON,LOCATION" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "city": "San Francisco",
    "country": "United States"
  }'
```

**Response:**
```json
{
  "name": "<PERSON_1>",
  "city": "<LOCATION_1>",
  "country": "<LOCATION_2>"
}
```

### Example 3: Deterministic Behavior

**Request:**
```bash
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON" \
  -H "Content-Type: application/json" \
  -d '{
    "manager": "Alice Johnson",
    "employee": "Bob Smith",
    "notes": ["Alice Johnson is manager", "Bob Smith reports to Alice Johnson"]
  }'
```

**Response:**
```json
{
  "manager": "<PERSON_1>",
  "employee": "<PERSON_2>",
  "notes": [
    "<PERSON_1> is manager",
    "<PERSON_2> reports to <PERSON_1>"
  ]
}
```

### Example 4: Type Preservation

**Request:**
```bash
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON" \
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

---

## Integration Guide

### JavaScript / TypeScript

```typescript
const API_URL = 'https://prime.rnd.2bv.io';

// Only use working entity types
const VALID_ENTITIES = ['PERSON', 'LOCATION'] as const;

async function anonymizeJSON(
  data: any,
  strategy: 'replace' | 'hash' = 'replace',
  entities: string[] = ['PERSON', 'LOCATION']
): Promise<any> {
  // Validate entities (avoid API errors)
  const invalidEntities = entities.filter(e => !VALID_ENTITIES.includes(e as any));
  if (invalidEntities.length > 0) {
    console.warn(`Ignoring invalid entities: ${invalidEntities.join(', ')}`);
    entities = entities.filter(e => VALID_ENTITIES.includes(e as any));
  }

  const params = new URLSearchParams();
  if (strategy) params.append('strategy', strategy);
  if (entities.length > 0) params.append('entities', entities.join(','));

  const url = `${API_URL}/anonymize?${params.toString()}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

// Usage
const result = await anonymizeJSON(
  { name: 'Alice', city: 'San Francisco' },
  'replace',
  ['PERSON', 'LOCATION']
);
```

### Python

```python
import requests
from typing import Any, Dict, List

API_URL = "https://prime.rnd.2bv.io"
VALID_ENTITIES = ["PERSON", "LOCATION"]  # Only working entities

def anonymize_json(
    data: Any,
    strategy: str = "replace",
    entities: List[str] = None
) -> Dict[str, Any]:
    if entities is None:
        entities = ["PERSON", "LOCATION"]

    # Filter out invalid entities
    entities = [e for e in entities if e in VALID_ENTITIES]
    if not entities:
        entities = ["PERSON"]  # Fallback

    params = {
        "strategy": strategy,
        "entities": ",".join(entities)
    }

    response = requests.post(
        f"{API_URL}/anonymize",
        params=params,
        headers={"Content-Type": "application/json"},
        json=data
    )

    if response.status_code == 200:
        return response.json()
    else:
        error = response.json().get("detail", "Unknown error")
        raise Exception(f"API Error {response.status_code}: {error}")

# Usage
result = anonymize_json(
    {"name": "Alice", "city": "San Francisco"},
    strategy="replace",
    entities=["PERSON", "LOCATION"]
)
```

---

## CORS Configuration

Allowed origins:
- `http://localhost:3000`
- `http://localhost:3001`
- `https://prime.rnd.2bv.io`
- `https://prime-ui.rnd.2bv.io`

---

## Recommendations for UI

### Entity Selector (Corrected)

**DO NOT offer these options:**
- ❌ EMAIL_ADDRESS
- ❌ PHONE_NUMBER (detection broken)
- ❌ US_SSN
- ❌ CREDIT_CARD
- ❌ IBAN
- ❌ DATE_TIME
- ❌ IP_ADDRESS
- ❌ URL

**ONLY offer:**
- ✅ PERSON
- ✅ LOCATION

### Example Templates (Updated)

Use examples that **only demonstrate working entities**:

**Good Example:**
```json
{
  "customer": {
    "name": "Alice Johnson",
    "city": "San Francisco",
    "country": "United States"
  },
  "sales_rep": {
    "name": "Bob Smith",
    "region": "California"
  }
}
```

**Bad Example (will fail user expectations):**
```json
{
  "name": "Alice Johnson",
  "email": "alice@example.com",  // Won't be anonymized
  "phone": "+1-555-123-4567",     // Won't be anonymized
  "ssn": "123-45-6789"            // Won't be anonymized
}
```

---

## FAQ

**Q: Why don't phone numbers/emails get anonymized?**
A: The Presidio configuration doesn't support EMAIL_ADDRESS, and PHONE_NUMBER detection is essentially broken for common formats.

**Q: Can I add more entity types?**
A: No, entity types are fixed by the Presidio library configuration.

**Q: Is PHONE_NUMBER entity useless?**
A: Yes, for practical purposes. It rarely detects real-world phone formats.

**Q: What should my UI show?**
A: Only offer PERSON and LOCATION as entity options. Remove all others to avoid confusion.

---

**Last Updated:** 2024-10-08
**API Version:** 1.0.0
**Tested Against:** https://prime.rnd.2bv.io
