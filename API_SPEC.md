# Prime Anonymizer API Documentation

## Base URL

```
Production: https://prime.rnd.2bv.io
Development: http://localhost:8000
```

## Endpoint

### POST /anonymize

Anonymizes PII (Personally Identifiable Information) in JSON data.

#### Request

**Method:** `POST`

**URL:** `/anonymize`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `strategy` | string | Yes | - | Anonymization strategy: `replace` or `hash` |
| `entities` | string | Yes | - | Comma-separated list of entity types to anonymize |

**Supported Entity Types:**
- `PERSON` - Person names
- `EMAIL_ADDRESS` - Email addresses
- `PHONE_NUMBER` - Phone numbers (various formats)
- `CREDIT_CARD` - Credit card numbers
- `IBAN` - International Bank Account Numbers
- `US_SSN` - US Social Security Numbers
- `LOCATION` - Geographic locations (addresses, cities, etc.)
- `DATE_TIME` - Date and time values
- `IP_ADDRESS` - IP addresses (IPv4/IPv6)
- `URL` - URLs and web addresses

**Headers:**
```
Content-Type: application/json
```

**Body:**
- Any valid JSON object, array, or primitive value
- Maximum size: 2 MiB (2,097,152 bytes)

#### Request Example

**URL:**
```
POST /anonymize?strategy=replace&entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER
```

**Body:**
```json
{
  "customer_id": "CUST-12345",
  "name": "Alice Johnson",
  "email": "alice.johnson@email.com",
  "phone": "+1-555-123-4567",
  "address": {
    "street": "123 Main Street",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102"
  }
}
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Body:**
The anonymized version of the input JSON with specified entities replaced/hashed.

#### Response Example

**Strategy: replace**
```json
{
  "customer_id": "CUST-12345",
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phone": "+1-555-987-6543",
  "address": {
    "street": "123 Main Street",
    "city": "Springfield",
    "state": "CA",
    "zip": "94102"
  }
}
```

**Strategy: hash**
```json
{
  "customer_id": "CUST-12345",
  "name": "a3f2b1c4...",
  "email": "b4e5d6a7...",
  "phone": "c8f9g0h1...",
  "address": {
    "street": "123 Main Street",
    "city": "d9j2k3l4...",
    "state": "CA",
    "zip": "94102"
  }
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid JSON format"
}
```

**413 Payload Too Large**
```json
{
  "detail": "Request payload exceeds maximum size of 2 MiB"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["query", "strategy"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## API Usage Examples

### cURL

```bash
# Replace strategy
curl -X POST "https://prime.rnd.2bv.io/anonymize?strategy=replace&entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice@example.com"}'

# Hash strategy with multiple entities
curl -X POST "https://prime.rnd.2bv.io/anonymize?strategy=hash&entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER,CREDIT_CARD" \
  -H "Content-Type: application/json" \
  -d @input.json
```

### JavaScript (Fetch API)

```javascript
const data = {
  name: "Alice Johnson",
  email: "alice@example.com",
  phone: "+1-555-123-4567"
};

const response = await fetch(
  'https://prime.rnd.2bv.io/anonymize?strategy=replace&entities=PERSON,EMAIL_ADDRESS,PHONE_NUMBER',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  }
);

const anonymized = await response.json();
console.log(anonymized);
```

### Python (requests)

```python
import requests
import json

url = "https://prime.rnd.2bv.io/anonymize"
params = {
    "strategy": "replace",
    "entities": "PERSON,EMAIL_ADDRESS,PHONE_NUMBER"
}
headers = {
    "Content-Type": "application/json"
}
data = {
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "+1-555-123-4567"
}

response = requests.post(url, params=params, headers=headers, json=data)
anonymized = response.json()
print(json.dumps(anonymized, indent=2))
```

## Implementation Notes

### Strategy Differences

**Replace Strategy:**
- Replaces PII with realistic fake data
- Maintains data type and format
- Useful for testing with realistic-looking data
- Non-deterministic (different each time)

**Hash Strategy:**
- Replaces PII with cryptographic hash
- Deterministic (same input → same hash)
- Useful for data analysis and deduplication
- Less realistic appearance

### Entity Detection

The API uses NLP and pattern matching to detect entities:
- Context-aware detection (e.g., "Dr. Smith" recognized as PERSON)
- Format validation (e.g., credit card numbers must pass Luhn check)
- Works with nested JSON structures
- Handles arrays and complex objects

### Performance

- Typical latency: 50-200ms for payloads under 100KB
- Processing time scales with:
  - JSON size
  - Number of entities selected
  - Complexity of nested structures
- Maximum payload: 2 MiB

### CORS Configuration

The API supports CORS with the following origins:
- `http://localhost:3000` (development)
- `https://prime-ui.rnd.2bv.io` (production)

## UI Integration

The Prime Anonymizer UI constructs requests as follows:

```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL; // Base URL without /anonymize
const entitiesParam = entities.join(","); // Array to comma-separated string
const url = `${apiUrl}/anonymize?strategy=${strategy}&entities=${entitiesParam}`;

const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: inputJson // Raw JSON string
});
```

## Rate Limiting

*Note: Document rate limiting if applicable*

Current limits (if any):
- Requests per minute: TBD
- Concurrent connections: TBD
- Payload size: 2 MiB max

## Authentication

*Note: Document if API requires authentication*

Current implementation:
- No authentication required
- Consider adding API key for production use

## Versioning

Current API Version: `1.0`

No version prefix in URL currently. Consider adding `/v1/anonymize` for future versioning.

## Health Check

*Note: Add if available*

Suggested endpoint:
```
GET /health
Response: {"status": "ok"}
```

## OpenAPI/Swagger Documentation

*Note: Add link if available*

Interactive API documentation may be available at:
- `https://prime.rnd.2bv.io/docs` (FastAPI default)
- `https://prime.rnd.2bv.io/redoc` (ReDoc alternative)

## Contact & Support

For API issues or questions:
- Check backend logs
- Review FastAPI documentation
- Contact development team

---

**Last Updated:** 2025-10-08
**API Version:** 1.0
