# Services Required for Advanced Endpoints

This document outlines what services and dependencies are needed to use the advanced PII detection endpoints.

## Quick Summary

| Endpoint | Required Services | Optional Services | Can Work Without External Services? |
|----------|------------------|-------------------|-------------------------------------|
| `/analyze` | ✅ None (built-in) | Azure AI Language | ✅ Yes |
| `/anonymize-advanced` | ✅ None (built-in) | Azure AI Language | ✅ Yes |
| `/annotate` | ✅ None (built-in) | Azure AI Language | ✅ Yes |
| `/entities` | ✅ None (built-in) | - | ✅ Yes |
| `/synthesize` | ❌ **OpenAI API** | Azure OpenAI | ❌ No |

---

## Built-In Capabilities (No External Services Needed)

### ✅ **Most Endpoints Work Out of the Box**

The following endpoints work **immediately** without any external services:

1. **POST /analyze** - PII detection
2. **POST /anonymize-advanced** - Anonymization (operators: redact, replace, mask, hash, encrypt, highlight)
3. **POST /annotate** - Text annotation
4. **GET /entities** - List entity types

These use **Presidio's built-in recognizers** which include:
- Pattern-based recognition (regex patterns)
- Rule-based recognition
- spaCy NLP models (already installed)

---

## Required Python Packages

### Already Installed (From Your Current requirements.txt)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
presidio-analyzer==2.2.354
presidio-anonymizer==2.2.354
spacy==3.7.2
pydantic-settings==2.1.0
```

These are **sufficient** for all endpoints except `/synthesize`.

### Additional Packages Needed for OpenAI Synthesis

To use the `/synthesize` endpoint, add to `requirements.txt`:

```txt
# For OpenAI synthesis endpoint
openai>=1.0.0
```

**Installation:**
```bash
pip install openai
```

---

## Optional External Services

### 1. **OpenAI API** (Required ONLY for `/synthesize`)

**What it does:** Generates realistic fake PII values to replace detected entities.

**Cost:** Pay-per-use API
- GPT-3.5-turbo-instruct: ~$0.0015 per 1K tokens
- GPT-4: ~$0.03 per 1K tokens

**Setup:**
1. Create account at https://platform.openai.com
2. Generate API key
3. Pass key in request:
```json
{
  "text": "My name is John Smith",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-3.5-turbo-instruct"
}
```

**Alternative:** Use Azure OpenAI if you have Azure subscription.

---

### 2. **Azure OpenAI** (Alternative to OpenAI for `/synthesize`)

**What it does:** Same as OpenAI but using Azure's managed service.

**Cost:** Pay-per-use, similar pricing to OpenAI

**Setup:**
1. Create Azure OpenAI resource
2. Deploy a model (e.g., gpt-35-turbo-instruct)
3. Get endpoint and key
4. Pass in request:
```json
{
  "text": "My name is John Smith",
  "openai_api_key": "your-azure-key",
  "openai_api_type": "azure",
  "azure_endpoint": "https://your-resource.openai.azure.com",
  "azure_deployment": "your-deployment-name",
  "api_version": "2023-05-15"
}
```

**Additional Package:**
```bash
pip install openai  # Same package works for both OpenAI and Azure
```

---

### 3. **Azure AI Language (Text Analytics)** (Optional Enhancement)

**What it does:** Enhanced PII detection using Microsoft's cloud service (not implemented in current endpoints, but available from presidio_demo).

**Cost:** Pay-per-use
- Standard: $1 per 1,000 text records
- Free tier: 5,000 records/month

**Setup:**
1. Create Azure Cognitive Services resource
2. Get key and endpoint
3. Would require modifying the analyzer engine initialization (not currently implemented)

**Additional Packages:**
```bash
pip install azure-ai-textanalytics
```

**Note:** This is **not required** for current implementation. Built-in Presidio recognizers work well.

---

## spaCy Language Models

### Already Installed
Your existing setup should have spaCy models installed. If not:

```bash
# Download small English model (lightweight, fast)
python -m spacy download en_core_web_sm

# OR download large model (better accuracy, slower)
python -m spacy download en_core_web_lg
```

**Current Implementation:** Uses whichever spaCy model is available via Presidio's default configuration.

---

## Database (Already Configured)

Your existing setup includes:
- SQLite database for audit logs
- Already configured in your `app/db.py`
- **No additional service needed**

---

## What You Need Right Now

### Minimal Setup (Core Features)

**To use all endpoints EXCEPT `/synthesize`:**

```bash
# Your existing requirements.txt is sufficient
pip install -r requirements.txt

# Ensure spaCy model is installed
python -m spacy download en_core_web_sm

# Start the server
uvicorn app.main:app --reload
```

**Available endpoints:**
- ✅ POST /analyze
- ✅ POST /anonymize-advanced (all operators except synthesize)
- ✅ POST /annotate
- ✅ GET /entities
- ❌ POST /synthesize (requires OpenAI)

---

### Full Setup (All Features Including Synthesis)

**Step 1: Install OpenAI package**
```bash
pip install openai
```

**Step 2: Update requirements.txt**
```txt
# Add this line to requirements.txt
openai>=1.0.0
```

**Step 3: Get OpenAI API Key**
- Sign up at https://platform.openai.com
- Generate API key
- Keep it secure (don't commit to git)

**Step 4: Test synthesis endpoint**
```bash
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith",
    "openai_api_key": "sk-YOUR-KEY-HERE",
    "openai_model": "gpt-3.5-turbo-instruct"
  }'
```

**Available endpoints:**
- ✅ POST /analyze
- ✅ POST /anonymize-advanced (ALL operators)
- ✅ POST /annotate
- ✅ GET /entities
- ✅ POST /synthesize

---

## Cost Analysis

### Free (No External Services)

**Endpoints:** `/analyze`, `/anonymize-advanced`, `/annotate`, `/entities`

**Cost:** $0 - Everything runs locally
- No API calls
- No cloud services
- Just your server resources

**Best for:**
- Development
- Testing
- Privacy-focused applications
- Budget-constrained projects

---

### With OpenAI (Synthesis Feature)

**Endpoint:** `/synthesize`

**Cost:** Pay per request
- Typical request: 100-500 tokens
- Cost per request: $0.0002 - $0.0008 (GPT-3.5)
- 1,000 requests: ~$0.20 - $0.80

**Example calculation:**
```
Average text: 200 tokens (input) + 100 tokens (output) = 300 tokens
Cost: 300 tokens × $0.0015 / 1000 = $0.00045 per request
10,000 requests/month = $4.50/month
```

**Best for:**
- Generating realistic test data
- Data augmentation
- Compliance demonstrations

---

## Deployment Considerations

### Development Environment

**Minimum:**
```yaml
Hardware:
  CPU: 2 cores
  RAM: 4 GB
  Disk: 2 GB (for models)

Software:
  Python: 3.10+
  pip packages: requirements.txt
  spaCy model: en_core_web_sm
```

### Production Environment

**Recommended:**
```yaml
Hardware:
  CPU: 4+ cores
  RAM: 8+ GB
  Disk: 5 GB

Software:
  Python: 3.10+
  pip packages: requirements.txt
  spaCy model: en_core_web_lg (better accuracy)

Optional:
  Redis: For caching analysis results
  PostgreSQL: Instead of SQLite for audit logs
```

---

## Testing Without External Services

### Test Script (No API Keys Required)

```bash
# Start server
uvicorn app.main:app --reload &

# Wait for server to start
sleep 5

# Test analyze endpoint
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com and my phone is 555-1234"}'

# Test anonymize-advanced with mask
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{"text": "My SSN is 123-45-6789", "operator": "mask"}'

# Test anonymize-advanced with hash
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{"text": "My SSN is 123-45-6789", "operator": "hash"}'

# Test annotate
curl -X POST "http://localhost:8000/annotate" \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is John Smith and I live in Seattle"}'

# Test entities
curl -X GET "http://localhost:8000/entities"

echo "All tests completed successfully! ✅"
```

---

## Frequently Asked Questions

### Q: Can I use the endpoints without any external services?
**A:** Yes! All endpoints except `/synthesize` work completely offline using built-in Presidio recognizers.

### Q: Do I need Azure for anything?
**A:** No. Azure AI Language and Azure OpenAI are optional alternatives, not requirements.

### Q: What's the difference between OpenAI and Azure OpenAI?
**A:** Same underlying models, different hosting:
- **OpenAI**: Direct API, easier setup, pay-as-you-go
- **Azure OpenAI**: Enterprise features, Azure integration, compliance certifications

### Q: Is the spaCy model included?
**A:** It should be installed with `pip install spacy`, but you may need to download the language model:
```bash
python -m spacy download en_core_web_sm
```

### Q: Can I use a different NLP model?
**A:** Current implementation uses spaCy, but presidio_demo code shows support for Flair, Transformers, and Stanza. These would require additional implementation.

### Q: Do I need internet access?
**A:**
- **Without synthesis:** No, everything runs locally
- **With synthesis:** Yes, requires OpenAI API access

### Q: What about GDPR/compliance?
**A:**
- Built-in endpoints: Process data locally, no external transmission
- Synthesis endpoint: Sends anonymized data to OpenAI (data already de-identified)

---

## Summary Table

| Feature | Service Required | Cost | Setup Complexity |
|---------|-----------------|------|------------------|
| PII Detection | None (built-in) | Free | ✅ Easy |
| Replace/Redact | None (built-in) | Free | ✅ Easy |
| Mask | None (built-in) | Free | ✅ Easy |
| Hash | None (built-in) | Free | ✅ Easy |
| Encrypt | None (built-in) | Free | ✅ Easy |
| Highlight/Annotate | None (built-in) | Free | ✅ Easy |
| **Synthesize** | **OpenAI API** | **~$5-20/mo** | **⚠️ Medium** |
| Enhanced Detection | Azure AI (optional) | ~$10-50/mo | ⚠️ Medium |

---

## Next Steps

### To Get Started Now (Free)

1. Verify packages installed:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. Start server:
```bash
uvicorn app.main:app --reload
```

3. Test endpoints:
```bash
curl -X GET "http://localhost:8000/entities"
```

### To Add Synthesis Later

1. Install OpenAI:
```bash
pip install openai
```

2. Get API key from https://platform.openai.com

3. Test synthesis:
```bash
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "openai_api_key": "sk-..."}'
```

---

## Support & Troubleshooting

**Common Issues:**

1. **"Module 'openai' not found"** → Only affects `/synthesize`, install with `pip install openai`
2. **"spaCy model not found"** → Run `python -m spacy download en_core_web_sm`
3. **"OpenAI API error"** → Check API key is valid and has credits

**All other endpoints work without any external dependencies!** ✅
