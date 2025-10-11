# Decision Process - Full Field Reference

Complete documentation for the **decision process** feature in the `/analyze` endpoint.

## Overview

When `return_decision_process: true`, each PII finding includes detailed information about **how** and **why** it was detected, including:

- Which recognizer detected it
- Pattern matching details
- Validation results
- Score adjustments
- Context enhancements

---

## Request

```json
{
  "text": "Your text here",
  "return_decision_process": true
}
```

---

## Response Structure

### Complete Response Example

```json
{
  "text": "Hi, I'm David Johnson from Liverpool. Email: test@presidio.site. SSN: 078-05-1126",
  "findings": [
    {
      "entity_type": "PERSON",
      "text": "David Johnson",
      "start": 9,
      "end": 22,
      "score": 1.0,
      "analysis_explanation": {
        "recognizer": "SpacyRecognizer",
        "original_score": 1.0,
        "textual_explanation": "Identified as PERSON by spaCy's Named Entity Recognition"
      }
    },
    {
      "entity_type": "LOCATION",
      "text": "Liverpool",
      "start": 28,
      "end": 37,
      "score": 1.0,
      "analysis_explanation": {
        "recognizer": "SpacyRecognizer",
        "original_score": 1.0,
        "textual_explanation": "Identified as LOCATION by spaCy's Named Entity Recognition"
      }
    },
    {
      "entity_type": "EMAIL_ADDRESS",
      "text": "test@presidio.site",
      "start": 46,
      "end": 64,
      "score": 1.0,
      "analysis_explanation": {
        "recognizer": "EmailRecognizer",
        "original_score": 1.0,
        "pattern_name": "Email (Medium)",
        "pattern": "\\b((([!#$%&'*+\\-/=?^_`{|}~\\w])|([!#$%&'*+\\-/=?^_`{|}~\\w][!#$%&'*+\\-/=?^_`{|}~\\.\\w]{0,}[!#$%&'*+\\-/=?^_`{|}~\\w]))[@]\\w+([-.]\\w+)*\\.\\w+([-.]\\w+)*)\\b",
        "score": 0.5,
        "validation_result": 1.0,
        "textual_explanation": "Detected by `EmailRecognizer` using pattern `Email (Medium)`"
      }
    },
    {
      "entity_type": "US_SSN",
      "text": "078-05-1126",
      "start": 71,
      "end": 82,
      "score": 0.85,
      "analysis_explanation": {
        "recognizer": "UsSsnRecognizer",
        "original_score": 0.85,
        "pattern_name": "SSN (medium)",
        "pattern": "\\b([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})\\b",
        "score": 0.5,
        "validation_result": 0.85,
        "score_context_improvement": 0.35,
        "textual_explanation": "Detected by `UsSsnRecognizer` using pattern `SSN (medium)`"
      }
    }
  ],
  "summary": {
    "PERSON": 1,
    "LOCATION": 1,
    "EMAIL_ADDRESS": 1,
    "US_SSN": 1
  }
}
```

---

## Field Definitions

### Standard Finding Fields (Always Present)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `entity_type` | string | Type of PII entity | `"PERSON"`, `"EMAIL_ADDRESS"`, `"US_SSN"` |
| `text` | string | Actual PII text found | `"John Smith"` |
| `start` | integer | Start position (0-indexed) | `11` |
| `end` | integer | End position | `21` |
| `score` | float | Final confidence score | `0.85` |

### Analysis Explanation Fields (When `return_decision_process: true`)

#### Core Fields (Always Present in Explanation)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `recognizer` | string | Name of the recognizer that detected this entity | `"EmailRecognizer"`, `"SpacyRecognizer"` |
| `original_score` | float | Original confidence score before adjustments | `0.85` |
| `textual_explanation` | string | Human-readable explanation | `"Detected by EmailRecognizer using pattern Email (Medium)"` |

#### Pattern-Based Recognition Fields (When Using Pattern Recognizers)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `pattern_name` | string | Name of the regex pattern used | `"Email (Medium)"`, `"SSN (medium)"`, `"IPv4"` |
| `pattern` | string | Actual regex pattern | `"\\b([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})\\b"` |
| `score` | float | Base score of the pattern | `0.5` |

#### Validation Fields (When Validation is Applied)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `validation_result` | float | Score after validation (0.0-1.0) | `0.85`, `1.0` |

**Note:** Validation checks if the detected text is actually valid. For example:
- Credit cards: Luhn algorithm validation
- SSN: Format and range validation
- Email: RFC validation
- IBAN: Checksum validation

#### Context Enhancement Fields (When Context Words are Found)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `score_context_improvement` | float | Score boost from context words | `0.35` |
| `supportive_context_word` | string | Context word that boosted confidence | `"SSN"`, `"email"`, `"passport"` |

**Context words** are terms near the PII that increase confidence. For example:
- "My **SSN** is 123-45-6789" → boost for `US_SSN`
- "**Email**: john@example.com" → boost for `EMAIL_ADDRESS`
- "**Passport** number: AB123456" → boost for `US_PASSPORT`

---

## Score Calculation Flow

Understanding how the final `score` is calculated:

```
1. Pattern Match
   ↓
   base pattern score (e.g., 0.5)

2. Validation (if applicable)
   ↓
   validation_result (e.g., 0.85)

3. Context Enhancement (if applicable)
   ↓
   + score_context_improvement (e.g., +0.35)

4. Final Score
   ↓
   final score (e.g., 0.85)
```

### Example: US SSN Detection

```json
{
  "entity_type": "US_SSN",
  "text": "078-05-1126",
  "score": 0.85,
  "analysis_explanation": {
    "recognizer": "UsSsnRecognizer",
    "pattern_name": "SSN (medium)",
    "pattern": "\\b([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})\\b",
    "score": 0.5,                          // Base pattern score
    "validation_result": 0.85,             // After format validation
    "score_context_improvement": 0.35,     // Boost from context word
    "supportive_context_word": "SSN",      // Context word found
    "original_score": 0.85                 // Final after all adjustments
  }
}
```

**Calculation:**
1. Pattern matched: `score = 0.5`
2. Validation passed: `validation_result = 0.85`
3. Context word "SSN" found nearby: `+0.35 boost`
4. Final score: `0.85`

---

## Recognition Methods

### 1. NER Model Recognition (spaCy, Flair, Transformers)

**Example:**
```json
{
  "entity_type": "PERSON",
  "score": 1.0,
  "analysis_explanation": {
    "recognizer": "SpacyRecognizer",
    "original_score": 1.0,
    "textual_explanation": "Identified as PERSON by spaCy's Named Entity Recognition"
  }
}
```

**Characteristics:**
- No pattern or validation fields
- High confidence for well-trained entities
- Model-based recognition

---

### 2. Pattern Recognition (Regex-Based)

**Example:**
```json
{
  "entity_type": "EMAIL_ADDRESS",
  "score": 1.0,
  "analysis_explanation": {
    "recognizer": "EmailRecognizer",
    "original_score": 1.0,
    "pattern_name": "Email (Medium)",
    "pattern": "\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
    "score": 0.5,
    "validation_result": 1.0,
    "textual_explanation": "Detected by `EmailRecognizer` using pattern `Email (Medium)`"
  }
}
```

**Characteristics:**
- Has `pattern_name` and `pattern` fields
- Base `score` from pattern strength
- May have `validation_result` if validation applied

---

### 3. Deny List Recognition (Custom Words)

**Example:**
```json
{
  "entity_type": "GENERIC_PII",
  "score": 1.0,
  "analysis_explanation": {
    "recognizer": "PatternRecognizer",
    "original_score": 1.0,
    "textual_explanation": "Matched deny list term"
  }
}
```

**Characteristics:**
- High confidence (usually 1.0)
- Used for custom sensitive terms

---

## Recognizer Types Reference

| Recognizer | Method | Has Pattern | Has Validation | Example Entity |
|------------|--------|-------------|----------------|----------------|
| SpacyRecognizer | NER Model | ❌ | ❌ | PERSON, LOCATION |
| FlairRecognizer | NER Model | ❌ | ❌ | PERSON, LOCATION, ORGANIZATION |
| EmailRecognizer | Regex Pattern | ✅ | ✅ | EMAIL_ADDRESS |
| PhoneRecognizer | Regex Pattern | ✅ | ✅ | PHONE_NUMBER |
| CreditCardRecognizer | Regex Pattern | ✅ | ✅ Luhn | CREDIT_CARD |
| UsSsnRecognizer | Regex Pattern | ✅ | ✅ Format | US_SSN |
| IpRecognizer | Regex Pattern | ✅ | ❌ | IP_ADDRESS |
| UrlRecognizer | Regex Pattern | ✅ | ❌ | URL |
| IbanRecognizer | Regex Pattern | ✅ | ✅ Checksum | IBAN_CODE |
| CryptoRecognizer | Regex Pattern | ✅ | ✅ Checksum | CRYPTO |
| PatternRecognizer | Deny List | ❌ | ❌ | GENERIC_PII |

---

## Example Use Cases

### 1. Debugging: Why wasn't this detected?

**Query:**
```json
{
  "text": "My ID is abc123",
  "return_decision_process": true,
  "score_threshold": 0.3
}
```

**Analysis:** Check if any patterns matched with low scores below threshold.

---

### 2. Auditing: Show detection reasoning

**Query:**
```json
{
  "text": "SSN: 123-45-6789",
  "return_decision_process": true
}
```

**Response shows:**
- Pattern used: `SSN (medium)`
- Validation result: `0.85`
- Context boost: `+0.35` from "SSN"
- Final score: `0.85`

---

### 3. Tuning: Adjust thresholds

See which entities are borderline (scores near threshold):

```json
{
  "text": "Call 555-1234",
  "return_decision_process": true,
  "score_threshold": 0.5
}
```

Check `score` vs `score_threshold` to understand filtering.

---

### 4. Understanding Context Impact

```bash
# Without context
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "123-45-6789", "return_decision_process": true}'

# With context
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "return_decision_process": true}'
```

Compare `score_context_improvement` fields to see the boost.

---

## Complete cURL Examples

### Example 1: Email Detection

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Contact: john@example.com",
    "return_decision_process": true
  }'
```

**Response:**
```json
{
  "findings": [{
    "entity_type": "EMAIL_ADDRESS",
    "text": "john@example.com",
    "score": 1.0,
    "analysis_explanation": {
      "recognizer": "EmailRecognizer",
      "pattern_name": "Email (Medium)",
      "pattern": "\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
      "score": 0.5,
      "validation_result": 1.0
    }
  }]
}
```

---

### Example 2: Credit Card with Validation

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Card: 4532-1234-5678-9010",
    "return_decision_process": true
  }'
```

**Response:**
```json
{
  "findings": [{
    "entity_type": "CREDIT_CARD",
    "text": "4532-1234-5678-9010",
    "score": 1.0,
    "analysis_explanation": {
      "recognizer": "CreditCardRecognizer",
      "pattern_name": "All Credit Cards (weak)",
      "pattern": "\\b((4\\d{3})|(5[0-5]\\d{2})|(6\\d{3}))...",
      "score": 0.3,
      "validation_result": 1.0,
      "textual_explanation": "Detected by CreditCardRecognizer using pattern All Credit Cards (weak), passed Luhn check"
    }
  }]
}
```

---

### Example 3: Context Enhancement

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Employee SSN: 078-05-1126",
    "return_decision_process": true
  }'
```

**Response:**
```json
{
  "findings": [{
    "entity_type": "US_SSN",
    "text": "078-05-1126",
    "score": 0.85,
    "analysis_explanation": {
      "recognizer": "UsSsnRecognizer",
      "pattern_name": "SSN (medium)",
      "score": 0.5,
      "validation_result": 0.85,
      "score_context_improvement": 0.35,
      "supportive_context_word": "SSN"
    }
  }]
}
```

---

## Field Availability Matrix

| Field | NER Models | Pattern Recognizers | Deny List |
|-------|------------|---------------------|-----------|
| `recognizer` | ✅ | ✅ | ✅ |
| `original_score` | ✅ | ✅ | ✅ |
| `textual_explanation` | ✅ | ✅ | ✅ |
| `pattern_name` | ❌ | ✅ | ❌ |
| `pattern` | ❌ | ✅ | ❌ |
| `score` | ❌ | ✅ | ❌ |
| `validation_result` | ❌ | ✅* | ❌ |
| `score_context_improvement` | ❌ | ✅* | ❌ |
| `supportive_context_word` | ❌ | ✅* | ❌ |

\* Only present when validation/context enhancement is applied

---

## Summary

The decision process provides:

1. **Transparency** - See exactly how each PII was detected
2. **Debugging** - Understand why scores are high or low
3. **Auditing** - Compliance and explainability
4. **Tuning** - Optimize thresholds and recognizers

**Enable with:** `"return_decision_process": true` in `/analyze` requests
