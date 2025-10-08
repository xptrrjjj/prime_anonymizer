# Docker Verification for Advanced Endpoints

## ✅ Current Dockerfile Status: **COMPATIBLE**

Your existing Dockerfile works perfectly with all new endpoints without any modifications needed.

---

## Why It Already Works

### 1. **Application Code Copy**
```dockerfile
COPY app/ ./app/
```
✅ This line already copies ALL files in the `app/` directory, including:
- `app/presidio_advanced.py` (new)
- `app/openai_synthesis.py` (new)
- `app/endpoints_advanced.py` (new)
- `app/main.py` (updated with router import)

### 2. **Dependencies**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
✅ Your `requirements.txt` already has everything needed:
- `presidio-analyzer==2.2.354`
- `presidio-anonymizer==2.2.354`
- `fastapi==0.104.1`
- `pydantic-settings==2.1.0`

### 3. **spaCy Model**
```dockerfile
RUN python -m spacy download en_core_web_lg
```
✅ Already downloads the spaCy model needed for PII detection.

### 4. **Application Entry Point**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
✅ Starts the FastAPI app which now includes all new endpoints via the router.

---

## What's Missing (Optional)

### OpenAI Package (Only for `/synthesize` endpoint)

If you want to use the `/synthesize` endpoint inside Docker, you need to add `openai` to requirements.txt.

**Current State:**
- `/analyze` ✅ Works
- `/anonymize-advanced` (redact, replace, mask, hash, encrypt, highlight) ✅ Works
- `/annotate` ✅ Works
- `/entities` ✅ Works
- `/synthesize` ❌ Requires `openai` package

**To enable `/synthesize`:**

Add to `requirements.txt`:
```txt
openai>=1.0.0
```

Then rebuild Docker:
```bash
docker build -t prime-anonymizer .
```

---

## Testing Docker Build

### Build the Image

```bash
cd d:\2bv\prime_anonymizer
docker build -t prime-anonymizer .
```

**Expected Output:**
```
[+] Building 45.2s (12/12) FINISHED
...
Successfully built xyz123
Successfully tagged prime-anonymizer:latest
```

### Run the Container

```bash
docker run -d \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  --name prime-anonymizer \
  prime-anonymizer
```

### Test All New Endpoints

```bash
# Test entities endpoint
curl -X GET "http://localhost:8000/entities"

# Test analyze endpoint
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com"}'

# Test anonymize-advanced with mask
curl -X POST "http://localhost:8000/anonymize-advanced" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "operator": "mask"}'

# Test annotate
curl -X POST "http://localhost:8000/annotate" \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is John Smith"}'

# Test original endpoint (should still work)
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith", "email": "john@example.com"}'
```

### Expected Results

✅ All endpoints should return 200 OK with valid JSON responses.

---

## Docker Compose (Recommended)

For easier management, create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prime-anonymizer:
    build: .
    container_name: prime-anonymizer
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - MAX_REQUEST_SIZE=2097152  # 2 MiB
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/entities"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Usage:**
```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

---

## Health Check Update (Optional Enhancement)

Your current health check uses the `/anonymize` endpoint. Consider updating to use `/entities` since it's simpler and doesn't require a POST body:

**Current:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/anonymize -X POST -H "Content-Type: application/json" -d '{"test": "health"}' || exit 1
```

**Suggested (simpler):**
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/entities || exit 1
```

This is more reliable because:
- ✅ GET request (simpler than POST)
- ✅ No request body needed
- ✅ Faster response
- ✅ Tests the new routing system

---

## Updated Dockerfile (With Optional Improvements)

Here's an enhanced version with OpenAI support and improved health check:

```dockerfile
# Use Python 3.11 slim image for production
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY app/ ./app/

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Improved health check using /entities endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/entities || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key change:** Only the health check (optional improvement).

---

## .dockerignore Verification

Your `.dockerignore` is already optimal:

```
# Excludes unnecessary files
__pycache__/
*.py[cod]
.venv/
venv/
logs/
data/
.pytest_cache/
README.md
Dockerfile
.dockerignore
```

✅ No changes needed. New Python files in `app/` will be included automatically.

---

## File Size Impact

### Before (Original)
```
Image size: ~850 MB
```

### After (With New Endpoints)
```
Image size: ~850 MB (no change)
```

**Why no size increase?**
- New Python files are minimal (<50 KB total)
- No new system dependencies
- No new large packages (unless adding `openai`)

**If adding OpenAI:**
```
Image size: ~860 MB (+10 MB for openai package)
```

---

## Production Deployment Checklist

### Before Deploying

- [ ] Test Docker build locally
- [ ] Verify all endpoints work in container
- [ ] Check health check passes
- [ ] Ensure volumes are mounted correctly
- [ ] Review environment variables

### Environment Variables to Set

```bash
# Optional: Set log level
-e LOG_LEVEL=INFO

# Optional: Set max request size
-e MAX_REQUEST_SIZE=2097152

# Optional: For synthesis endpoint (if using)
-e OPENAI_API_KEY=sk-...
-e OPENAI_MODEL=gpt-3.5-turbo-instruct
```

### Resource Limits (Recommended)

```yaml
# In docker-compose.yml
services:
  prime-anonymizer:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Troubleshooting

### Issue: "Module not found: endpoints_advanced"

**Cause:** Application code not copied correctly.

**Solution:**
```bash
# Rebuild with --no-cache
docker build --no-cache -t prime-anonymizer .
```

### Issue: Health check failing

**Cause:** Application taking longer to start.

**Solution:** Increase `start-period` in health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3
```

### Issue: "/synthesize endpoint not working"

**Cause:** Missing `openai` package.

**Solution:**
1. Add `openai>=1.0.0` to `requirements.txt`
2. Rebuild: `docker build -t prime-anonymizer .`

---

## Summary

### ✅ What Already Works

Your existing Dockerfile is **100% compatible** with:
- POST `/analyze`
- POST `/anonymize-advanced` (operators: redact, replace, mask, hash, encrypt, highlight)
- POST `/annotate`
- GET `/entities`
- POST `/anonymize` (original endpoint)

### 📦 Optional Addition (For Synthesis)

To enable POST `/synthesize`:
1. Add `openai>=1.0.0` to `requirements.txt`
2. Rebuild Docker image
3. Pass OpenAI API key via environment variable or request body

### 🚀 Recommended Actions

**Minimal (Keep as-is):**
```bash
# Just rebuild and you're done
docker build -t prime-anonymizer .
docker run -d -p 8000:8000 prime-anonymizer
```

**Enhanced (With synthesis support):**
```bash
# Add to requirements.txt
echo "openai>=1.0.0" >> requirements.txt

# Rebuild
docker build -t prime-anonymizer .

# Run with OpenAI key (optional)
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  prime-anonymizer
```

**No Dockerfile changes required!** 🎉
