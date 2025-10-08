# Advanced PII Detection Endpoints

This document describes the new advanced endpoints that replicate all capabilities from the Presidio demo application.

## Overview

The following endpoints have been added without modifying the original `/anonymize` endpoint:

1. **POST /analyze** - Detect PII without anonymization
2. **POST /anonymize-advanced** - Anonymize with multiple operators
3. **POST /annotate** - Get text annotations for highlighting
4. **POST /synthesize** - Generate synthetic text with OpenAI
5. **GET /entities** - List supported entity types

---

## 1. POST /analyze

Analyze text for PII entities without performing anonymization.

### Request Body

```json
{
  "text": "My name is John Smith and my email is john@example.com",
  "entities": ["PERSON", "EMAIL_ADDRESS"],
  "score_threshold": 0.35,
  "allow_list": ["John"],
  "deny_list": ["secret123"],
  "return_decision_process": false
}
```

### Parameters

- `text` (required): Text to analyze
- `entities` (optional): List of entity types to detect. If null, all entities are detected
- `score_threshold` (optional, default: 0.35): Minimum confidence score (0.0-1.0)
- `allow_list` (optional): Words to exclude from detection
- `deny_list` (optional): Words to always detect as GENERIC_PII
- `return_decision_process` (optional, default: false): Include detailed analysis explanation

### Response

```json
{
  "text": "My name is John Smith and my email is john@example.com",
  "findings": [
    {
      "entity_type": "PERSON",
      "text": "John Smith",
      "start": 11,
      "end": 21,
      "score": 0.85
    },
    {
      "entity_type": "EMAIL_ADDRESS",
      "text": "john@example.com",
      "start": 38,
      "end": 54,
      "score": 1.0
    }
  ],
  "summary": {
    "PERSON": 1,
    "EMAIL_ADDRESS": 1
  }
}
```

### Example cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith and my email is john@example.com",
    "entities": ["PERSON", "EMAIL_ADDRESS"],
    "score_threshold": 0.35
  }'
```

---

## 2. POST /anonymize-advanced

Anonymize text using various operators (redact, replace, mask, hash, encrypt, highlight).

### Request Body

```json
{
  "text": "My SSN is 123-45-6789 and my phone is (555) 123-4567",
  "operator": "mask",
  "entities": null,
  "score_threshold": 0.35,
  "allow_list": null,
  "deny_list": null,
  "mask_char": "*",
  "number_of_chars": 15,
  "encrypt_key": null
}
```

### Parameters

- `text` (required): Text to anonymize
- `operator` (required): Anonymization operator
  - `"redact"` - Remove PII completely
  - `"replace"` - Replace with entity type placeholder (e.g., `<PERSON>`)
  - `"mask"` - Replace N characters with mask character
  - `"hash"` - Replace with SHA-256 hash
  - `"encrypt"` - Replace with AES encryption (requires encrypt_key)
  - `"highlight"` - Return original text (use with findings for UI highlighting)
- `entities` (optional): Entity types to detect
- `score_threshold` (optional, default: 0.35): Minimum confidence score
- `allow_list` (optional): Words to exclude from detection
- `deny_list` (optional): Words to always detect as GENERIC_PII
- `mask_char` (optional, default: "*"): Character for masking (mask operator only)
- `number_of_chars` (optional, default: 15): Number of chars to mask (mask operator only)
- `encrypt_key` (optional): AES encryption key (encrypt operator only, 16 chars)

### Response

```json
{
  "original_text": "My SSN is 123-45-6789 and my phone is (555) 123-4567",
  "anonymized_text": "My SSN is *************** and my phone is ***************",
  "operator": "mask",
  "findings": [
    {
      "entity_type": "US_SSN",
      "text": "123-45-6789",
      "start": 10,
      "end": 21,
      "score": 0.85
    },
    {
      "entity_type": "PHONE_NUMBER",
      "text": "(555) 123-4567",
      "start": 39,
      "end": 53,
      "score": 0.7
    }
  ],
  "summary": {
    "US_SSN": 1,
    "PHONE_NUMBER": 1
  }
}
```

### Example cURL - Mask Operator

```bash
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My SSN is 123-45-6789",
    "operator": "mask",
    "mask_char": "*",
    "number_of_chars": 15
  }'
```

### Example cURL - Encrypt Operator

```bash
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith",
    "operator": "encrypt",
    "encrypt_key": "WmZq4t7w!z%C&F)J"
  }'
```

### Example cURL - Hash Operator

```bash
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Email: john@example.com",
    "operator": "hash"
  }'
```

---

## 3. POST /annotate

Get text broken into segments with entity labels for UI highlighting.

### Request Body

```json
{
  "text": "My name is John Smith and I live in Seattle",
  "entities": null,
  "score_threshold": 0.35,
  "allow_list": null,
  "deny_list": null
}
```

### Parameters

Same as `/analyze` endpoint (without `return_decision_process`)

### Response

```json
{
  "text": "My name is John Smith and I live in Seattle",
  "annotations": [
    {
      "text": "My name is ",
      "entity_type": null,
      "start": 0,
      "end": 11
    },
    {
      "text": "John Smith",
      "entity_type": "PERSON",
      "start": 11,
      "end": 21
    },
    {
      "text": " and I live in ",
      "entity_type": null,
      "start": 21,
      "end": 36
    },
    {
      "text": "Seattle",
      "entity_type": "LOCATION",
      "start": 36,
      "end": 43
    }
  ],
  "summary": {
    "PERSON": 1,
    "LOCATION": 1
  }
}
```

### Example cURL

```bash
curl -X POST "http://localhost:8000/annotate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith and I live in Seattle"
  }'
```

### Frontend Usage Example

```javascript
// Render with different colors for each entity type
annotations.forEach(annotation => {
  const span = document.createElement('span');
  span.textContent = annotation.text;

  if (annotation.entity_type) {
    span.className = `pii-${annotation.entity_type.toLowerCase()}`;
    span.style.backgroundColor = getColorForEntityType(annotation.entity_type);
  }

  container.appendChild(span);
});
```

---

## 4. POST /synthesize

Generate synthetic text with fake PII values using OpenAI.

### Request Body

```json
{
  "text": "My name is John Smith and I live in Seattle. My email is john@example.com",
  "entities": null,
  "score_threshold": 0.35,
  "openai_api_key": "sk-...",
  "openai_model": "gpt-3.5-turbo-instruct",
  "openai_api_type": "openai",
  "azure_endpoint": null,
  "azure_deployment": null,
  "api_version": "2023-05-15"
}
```

### Parameters

- `text` (required): Text to synthesize
- `entities` (optional): Entity types to detect
- `score_threshold` (optional, default: 0.35): Minimum confidence score
- `openai_api_key` (required): OpenAI API key
- `openai_model` (optional, default: "gpt-3.5-turbo-instruct"): Model name
- `openai_api_type` (optional, default: "openai"): "openai" or "azure"
- `azure_endpoint` (optional): Azure OpenAI endpoint URL
- `azure_deployment` (optional): Azure deployment name
- `api_version` (optional, default: "2023-05-15"): Azure API version

### Response

```json
{
  "original_text": "My name is John Smith and I live in Seattle. My email is john@example.com",
  "synthetic_text": "My name is Maria Rodriguez and I live in Toronto. My email is maria.r@sample.org",
  "findings": [
    {
      "entity_type": "PERSON",
      "text": "John Smith",
      "start": 11,
      "end": 21,
      "score": 0.85
    },
    {
      "entity_type": "LOCATION",
      "text": "Seattle",
      "start": 37,
      "end": 44,
      "score": 0.85
    },
    {
      "entity_type": "EMAIL_ADDRESS",
      "text": "john@example.com",
      "start": 58,
      "end": 74,
      "score": 1.0
    }
  ],
  "summary": {
    "PERSON": 1,
    "LOCATION": 1,
    "EMAIL_ADDRESS": 1
  }
}
```

### Example cURL - OpenAI

```bash
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith and I live in Seattle",
    "openai_api_key": "sk-...",
    "openai_model": "gpt-3.5-turbo-instruct",
    "openai_api_type": "openai"
  }'
```

### Example cURL - Azure OpenAI

```bash
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith",
    "openai_api_key": "your-azure-key",
    "openai_model": "gpt-35-turbo-instruct",
    "openai_api_type": "azure",
    "azure_endpoint": "https://your-resource.openai.azure.com",
    "azure_deployment": "your-deployment-name",
    "api_version": "2023-05-15"
  }'
```

---

## 5. GET /entities

Get list of all supported PII entity types.

### Request

No request body required (GET request).

### Response

```json
{
  "entities": [
    "AU_ABN",
    "AU_ACN",
    "AU_TFN",
    "CREDIT_CARD",
    "CRYPTO",
    "DATE_TIME",
    "EMAIL_ADDRESS",
    "GENERIC_PII",
    "IBAN_CODE",
    "IP_ADDRESS",
    "LOCATION",
    "MEDICAL_LICENSE",
    "NRP",
    "ORGANIZATION",
    "PERSON",
    "PHONE_NUMBER",
    "SG_NRIC_FIN",
    "UK_NHS",
    "URL",
    "US_BANK_NUMBER",
    "US_DRIVER_LICENSE",
    "US_ITIN",
    "US_PASSPORT",
    "US_SSN"
  ],
  "count": 24
}
```

### Example cURL

```bash
curl -X GET "http://localhost:8000/entities"
```

---

## Comparison with Original /anonymize Endpoint

### Original Endpoint (Unchanged)
- **POST /anonymize** - JSON payload anonymization with deterministic replacement
- Designed for API integrations with complex JSON structures
- Supports `strategy` parameter: "replace" or "hash"
- Supports `entities` query parameter for filtering

### New Advanced Endpoints
- **POST /analyze** - Detection only, no anonymization
- **POST /anonymize-advanced** - Text anonymization with 6 operators
- **POST /annotate** - UI highlighting support
- **POST /synthesize** - AI-generated fake data
- **GET /entities** - Discover available entity types

---

## Entity Types Reference

Common entity types supported by the analyzer:

| Entity Type | Description | Example |
|-------------|-------------|---------|
| PERSON | Person names | "John Smith" |
| EMAIL_ADDRESS | Email addresses | "john@example.com" |
| PHONE_NUMBER | Phone numbers | "(555) 123-4567" |
| CREDIT_CARD | Credit card numbers | "4532-1234-5678-9010" |
| US_SSN | US Social Security | "123-45-6789" |
| US_PASSPORT | US Passport number | "123456789" |
| US_DRIVER_LICENSE | US Driver's License | "D1234567" |
| LOCATION | Geographic locations | "Seattle", "New York" |
| DATE_TIME | Dates and times | "January 1, 2024" |
| IP_ADDRESS | IP addresses | "192.168.1.1" |
| URL | URLs | "https://example.com" |
| IBAN_CODE | Bank account numbers | "GB82 WEST 1234..." |
| CRYPTO | Cryptocurrency wallets | "1A1zP1eP5QGefi..." |
| MEDICAL_LICENSE | Medical licenses | Various formats |
| UK_NHS | UK NHS number | "123 456 7890" |
| AU_ABN | Australian Business | "51 824 753 556" |
| SG_NRIC_FIN | Singapore NRIC/FIN | "S1234567D" |
| GENERIC_PII | Custom deny list | User-defined |

---

## Allow/Deny Lists

### Allow List (Whitelist)
Words in the allow list will NOT be detected as PII, even if they match patterns.

**Example**: If you have a person named "May" in your text but don't want it detected as a date/person:
```json
{
  "text": "May attended the meeting",
  "allow_list": ["May"]
}
```

### Deny List (Blacklist)
Words in the deny list will ALWAYS be detected as `GENERIC_PII`.

**Example**: Detect custom sensitive terms:
```json
{
  "text": "The project codename is BlueHawk",
  "deny_list": ["BlueHawk"]
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK** - Success
- **400 Bad Request** - Invalid parameters or request body
- **500 Internal Server Error** - Processing failure

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

1. **Invalid operator**
```json
{
  "detail": "Invalid operator. Must be one of: redact, replace, mask, hash, encrypt, highlight"
}
```

2. **Missing encryption key**
```json
{
  "detail": "encrypt_key is required for encrypt operator"
}
```

3. **Missing OpenAI key**
```json
{
  "detail": "Synthesis failed: OpenAI API key is required for synthesis"
}
```

---

## Testing the Endpoints

### Start the Server

```bash
cd d:\2bv\prime_anonymizer
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

Use the provided test examples above, or create a test file:

```bash
# Save as test_advanced.sh
#!/bin/bash

# Test analyze endpoint
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is John Smith and my email is john@example.com"}'

# Test anonymize-advanced with mask
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "operator": "mask"}'

# Test entities
curl -X GET "http://localhost:8000/entities"

# Test annotate
curl -X POST "http://localhost:8000/annotate" \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is John and I live in Seattle"}'
```

---

## Integration Examples

### Python Client

```python
import requests

# Analyze text
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "text": "My email is john@example.com",
        "score_threshold": 0.5
    }
)
result = response.json()
print(f"Found {len(result['findings'])} PII entities")

# Anonymize with mask
response = requests.post(
    "http://localhost:8000/anonymize-advanced",
    json={
        "text": "My SSN is 123-45-6789",
        "operator": "mask",
        "number_of_chars": 10
    }
)
print(response.json()["anonymized_text"])
```

### JavaScript Client

```javascript
// Analyze text
const analyzeResponse = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'My email is john@example.com',
    score_threshold: 0.5
  })
});

const result = await analyzeResponse.json();
console.log(`Found ${result.findings.length} PII entities`);

// Get entity types
const entitiesResponse = await fetch('http://localhost:8000/entities');
const entities = await entitiesResponse.json();
console.log(`Supported entities: ${entities.entities.join(', ')}`);
```

---

## Performance Considerations

1. **Caching**: The analyzer engine is cached globally for performance
2. **Token Limits**: OpenAI synthesis is limited by model token limits
3. **Payload Size**: Large text inputs may take longer to process
4. **Concurrent Requests**: The server can handle multiple simultaneous requests

---

## Security Notes

1. **OpenAI Keys**: Never expose API keys in client-side code
2. **Encryption Keys**: Use strong 16-character keys for AES encryption
3. **PII Logging**: Original PII is not logged in the application logs
4. **CORS**: Configure CORS settings appropriately for production

---

## Roadmap / Future Enhancements

Potential future additions based on presidio_demo capabilities:

- [ ] Multi-language support (currently English only)
- [ ] Custom NER model selection (spaCy, Flair, Transformers, etc.)
- [ ] Batch processing endpoint for multiple texts
- [ ] Deanonymization endpoint (for encrypted data)
- [ ] Custom recognizer registration API
- [ ] Webhook notifications for async processing
- [ ] Rate limiting per API key

---

## Support

For issues or questions:
1. Check the error response message
2. Review this documentation
3. Check the server logs for detailed error traces
4. Verify your request matches the examples provided
