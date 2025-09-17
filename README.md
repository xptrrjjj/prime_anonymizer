# Prime Anonymizer API

A FastAPI-based backend service that anonymizes PII (Personally Identifiable Information) in JSON payloads using Microsoft Presidio. The service provides deterministic, consistent anonymization within each request while maintaining complete JSON structure preservation.

## Features

- **Single Endpoint**: POST `/anonymize` - accepts any valid JSON and returns it with PII anonymized
- **Deterministic Anonymization**: Same PII values get same replacement tokens within a request
- **Comprehensive PII Detection**: Detects PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, IBAN, US_SSN, LOCATION, DATE_TIME, IP_ADDRESS, URL
- **Structure Preservation**: Maintains exact JSON structure, ordering, and non-string data types
- **Multiple Strategies**: Replace with tokens (default) or hash-based anonymization
- **Audit Logging**: Complete request logging to both console/file and SQLite database
- **Security Limits**: 2 MiB request size limit, no PII persistence
- **Thread-Safe**: Per-request caches ensure thread safety

## Quick Start

### Local Development

1. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_lg
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

#### Option 1: Docker Compose (Recommended)

```bash
# Clone or copy the project files to your server
docker-compose up -d
```

#### Option 2: Manual Docker Commands

1. **Build the Docker image**:
   ```bash
   docker build -t prime-anonymizer .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name prime-anonymizer \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     --restart unless-stopped \
     prime-anonymizer
   ```

#### AWS EC2 Deployment with nginx-proxy

1. **Launch Ubuntu EC2 instance** with security group allowing ports 80/443
2. **Install Docker**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```
3. **Ensure nginx-proxy network exists**:
   ```bash
   docker network create nginx-proxy
   ```
4. **Deploy the application**:
   ```bash
   # Upload project files or clone from repository
   docker-compose up -d
   ```
5. **Access the API**: `https://prime.rnd.2bv.io`

The API will be available at `http://localhost:8000`

## API Usage

### Basic Anonymization

```bash
curl -X POST "https://prime.rnd.2bv.io/anonymize" \
  -H "Content-Type: application/json" \
  -d '{"user":"Ada Lovelace","contact":{"email":"ada@compute.org","phone":"+1-555-123-4567"},"notes":["Ada Lovelace met Ada Lovelace."]}'
```

**Response**:
```json
{
  "user": "<PERSON_1>",
  "contact": {
    "email": "<EMAIL_ADDRESS_1>",
    "phone": "<PHONE_NUMBER_1>"
  },
  "notes": ["<PERSON_1> met <PERSON_1>."]
}
```

### Query Parameters

- **`strategy`** (optional): `"replace"` (default) or `"hash"`
- **`entities`** (optional): Comma-separated list of entity types to detect

**Examples**:

```bash
# Hash-based anonymization
curl -X POST "https://prime.rnd.2bv.io/anonymize?strategy=hash" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Custom entity types
curl -X POST "https://prime.rnd.2bv.io/anonymize?entities=PERSON,EMAIL_ADDRESS" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "phone": "+1-555-1234"}'
```

## Project Structure

```
prime_anonymizer/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI app, router, middleware
│   ├── anonymize.py         # Presidio engines, entity/operator configs
│   ├── traverse.py          # Recursive JSON traversal/anonymization utilities
│   ├── db.py                # SQLAlchemy engine/session, init tables
│   ├── models.py            # ORM models (AuditLog)
│   └── config.py            # Settings (DB path, log paths, limits)
├── data/                    # SQLite database directory (auto-created)
├── logs/                    # Log files directory (auto-created)
├── tests/
│   └── test_anonymize.py    # Comprehensive test suite
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

The application can be configured via environment variables with the `ANONYMIZER_` prefix:

```bash
# Database settings
ANONYMIZER_DB_PATH=./data/app.db

# Logging settings
ANONYMIZER_LOG_FILE_PATH=./logs/app.log
ANONYMIZER_LOG_MAX_BYTES=10485760  # 10MB
ANONYMIZER_LOG_BACKUP_COUNT=5
ANONYMIZER_LOG_LEVEL=INFO

# Request limits
ANONYMIZER_MAX_REQUEST_SIZE=2097152  # 2MiB
ANONYMIZER_REQUEST_TIMEOUT=30.0

# spaCy model
ANONYMIZER_SPACY_MODEL=en_core_web_lg
```

## Supported PII Entity Types

- **PERSON**: Names of people
- **PHONE_NUMBER**: Phone numbers in various formats
- **EMAIL_ADDRESS**: Email addresses
- **CREDIT_CARD**: Credit card numbers
- **IBAN**: International Bank Account Numbers
- **US_SSN**: US Social Security Numbers
- **LOCATION**: Geographic locations
- **DATE_TIME**: Dates and times
- **IP_ADDRESS**: IP addresses
- **URL**: Web URLs

## Anonymization Behavior

### Deterministic Replacement

Within a single request, identical PII values receive identical replacement tokens:

**Input**:
```json
{
  "users": ["Alice Johnson", "Bob Smith", "Alice Johnson"],
  "message": "Alice Johnson sent a message to Bob Smith"
}
```

**Output**:
```json
{
  "users": ["<PERSON_1>", "<PERSON_2>", "<PERSON_1>"],
  "message": "<PERSON_1> sent a message to <PERSON_2>"
}
```

### Type Preservation

Non-string values are never modified:

**Input**:
```json
{
  "name": "John Doe",
  "age": 30,
  "active": true,
  "score": 95.5,
  "notes": null
}
```

**Output**:
```json
{
  "name": "<PERSON_1>",
  "age": 30,
  "active": true,
  "score": 95.5,
  "notes": null
}
```

## Testing

### Run All Tests

```bash
pytest tests/test_anonymize.py -v
```

### Test Categories

The test suite covers:

- ✅ PII detection in nested dictionaries and lists
- ✅ Type preservation for numbers, booleans, nulls
- ✅ Deterministic token assignment within requests
- ✅ Large payload handling under 2 MiB limit
- ✅ Hash strategy functionality
- ✅ Error handling (invalid JSON, oversized payloads)
- ✅ Query parameter validation
- ✅ Complex nested structures
- ✅ Multiple entity type detection

### Example Test Run

```bash
pytest tests/test_anonymize.py::TestAnonymizeEndpoint::test_deterministic_within_request_mapping -v
```

### Testing with Docker

```bash
# Run tests inside the container
docker-compose exec prime-anonymizer pytest tests/test_anonymize.py -v

# Or build a test image
docker build -t prime-anonymizer-test --target test .
```

## Logging and Auditing

### Console/File Logs

Structured JSON logs include:
- `ts`: Timestamp
- `request_id`: Unique UUID per request
- `path`: Request path
- `method`: HTTP method
- `status_code`: Response status
- `elapsed_ms`: Processing time
- `client_ip`: Client IP address
- `payload_bytes`: Request size
- `pii_found_by_type`: PII counts by entity type

### SQLite Audit Database

Location: `./data/app.db`

**`audit_logs` table**:
- `id`: Primary key
- `ts`: Timestamp
- `request_id`: Request UUID
- `client_ip`: Client IP
- `status_code`: HTTP status
- `elapsed_ms`: Processing time
- `payload_bytes`: Request size
- `pii_total`: Total PII entities found
- `pii_by_type_json`: JSON string of PII counts by type
- `error_msg`: Error message (if any)

## Security and Privacy

- **No PII Persistence**: Raw payloads are never logged or stored
- **Request Size Limits**: 2 MiB maximum to prevent abuse
- **Timeout Protection**: Reasonable timeouts for processing
- **Thread Safety**: Per-request caches prevent data leakage between requests
- **Audit Trail**: Complete request metadata without sensitive data

## Error Handling

| Status Code | Description | Response |
|-------------|-------------|----------|
| 400 | Invalid JSON or parameters | `{"detail": "error description"}` |
| 413 | Payload too large (>2 MiB) | `{"error": "Request payload too large (max 2 MiB)"}` |
| 500 | Internal server error | `{"error": "Internal server error"}` |

## Dependencies

- **FastAPI**: High-performance web framework
- **Uvicorn**: ASGI server
- **Presidio**: Microsoft's PII detection and anonymization
- **spaCy**: Natural language processing
- **SQLAlchemy**: Database ORM
- **Pydantic Settings**: Configuration management
- **Python JSON Logger**: Structured logging

## Development

### Code Quality

The codebase follows:
- Type hints throughout
- Black/Ruff formatting compliance
- Comprehensive docstrings
- Clear separation of concerns

### Architecture

- **`main.py`**: FastAPI application with middleware
- **`anonymize.py`**: Presidio integration with deterministic caching
- **`traverse.py`**: JSON structure traversal and anonymization
- **`db.py`**: Database operations and session management
- **`models.py`**: SQLAlchemy ORM models
- **`config.py`**: Centralized configuration management

## License

This project is provided as-is for demonstration purposes.