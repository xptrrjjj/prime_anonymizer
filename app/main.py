"""FastAPI main application with anonymization endpoint."""

import json
import logging
import time
import uuid
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger

from app.anonymize import DeterministicCache
from app.config import ensure_directories, get_settings
from app.db import db_manager
from app.traverse import anonymize_json_recursive, validate_json_structure
from app.endpoints_advanced import router as advanced_router

# Setup logging
ensure_directories()
settings = get_settings()

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, settings.log_level.upper()))

# Console handler with JSON formatting
console_handler = logging.StreamHandler()
console_formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
)
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# File handler with rotation (with fallback)
try:
    file_handler = RotatingFileHandler(
        settings.log_file_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count
    )
    file_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    print(f"File logging enabled: {settings.log_file_path}")
except Exception as e:
    print(f"Warning: Could not create file handler at {settings.log_file_path}: {e}")
    print("Continuing with console logging only")

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Prime Anonymizer API",
    description="Anonymize PII in JSON payloads using Microsoft Presidio",
    version="1.0.0",
    docs_url=None,  # Disable docs to keep only /anonymize endpoint
    redoc_url=None,
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://prime.rnd.2bv.io",
        "https://prime-ui.rnd.2bv.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnonymizeRequest(BaseModel):
    """Request model - accepts any valid JSON."""
    pass


class RequestContext:
    """Thread-local context for request data."""
    def __init__(self):
        self.request_id: Optional[str] = None
        self.start_time: Optional[float] = None
        self.payload_bytes: int = 0
        self.client_ip: Optional[str] = None
        self.pii_counts: Dict[str, int] = {}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and audit trail."""

    async def dispatch(self, request: Request, call_next):
        # Initialize request context
        context = RequestContext()
        context.request_id = str(uuid.uuid4())
        context.start_time = time.time()

        # Get client IP
        context.client_ip = self._get_client_ip(request)

        # Read and measure payload
        if request.method == "POST":
            body = await request.body()
            context.payload_bytes = len(body)

            # Check payload size limit
            if context.payload_bytes > settings.max_request_size:
                elapsed_ms = int((time.time() - context.start_time) * 1000)

                # Log the error
                logger.error(
                    "Request payload too large",
                    extra={
                        "ts": time.time(),
                        "request_id": context.request_id,
                        "path": str(request.url.path),
                        "method": request.method,
                        "status_code": 413,
                        "elapsed_ms": elapsed_ms,
                        "client_ip": context.client_ip,
                        "payload_bytes": context.payload_bytes,
                        "pii_found_by_type": {},
                    }
                )

                # Create audit log
                try:
                    db_manager.create_audit_log(
                        request_id=context.request_id,
                        client_ip=context.client_ip,
                        status_code=413,
                        elapsed_ms=elapsed_ms,
                        payload_bytes=context.payload_bytes,
                        pii_counts={},
                        error_msg="Request payload exceeds 2 MiB limit"
                    )
                except Exception as e:
                    logger.error(f"Failed to create audit log: {e}")

                return JSONResponse(
                    status_code=413,
                    content={"error": "Request payload too large (max 2 MiB)"}
                )

            # Re-create request with body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        # Store context in request state
        request.state.context = context

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
            context.pii_counts = {}
            error_msg = str(e)
        else:
            error_msg = None

        # Calculate elapsed time
        elapsed_ms = int((time.time() - context.start_time) * 1000)

        # Log request
        log_data = {
            "ts": time.time(),
            "request_id": context.request_id,
            "path": str(request.url.path),
            "method": request.method,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "client_ip": context.client_ip,
            "payload_bytes": context.payload_bytes,
            "pii_found_by_type": context.pii_counts,
        }

        if response.status_code >= 400:
            logger.error("Request failed", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)

        # Create audit log
        try:
            db_manager.create_audit_log(
                request_id=context.request_id,
                client_ip=context.client_ip,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                payload_bytes=context.payload_bytes,
                pii_counts=context.pii_counts,
                error_msg=error_msg
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host

        return "unknown"


# Add middleware
app.add_middleware(LoggingMiddleware)

# Include advanced endpoints router
app.include_router(advanced_router, tags=["Advanced PII Detection"])


@app.post("/anonymize")
async def anonymize_json(
    request: Request,
    strategy: str = "replace",
    entities: Optional[str] = None
) -> Dict[str, Any]:
    """
    Anonymize PII in JSON payload using Microsoft Presidio.

    Args:
        strategy: Anonymization strategy ("replace" or "hash")
        entities: Comma-separated list of entity types to detect

    Returns:
        JSON with PII anonymized using deterministic replacement
    """
    context = request.state.context

    # Validate strategy parameter
    if strategy not in ["replace", "hash"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid strategy. Must be 'replace' or 'hash'"
        )

    # Parse entities parameter
    entity_list = None
    if entities:
        entity_list = [entity.strip().upper() for entity in entities.split(",")]
        # Validate entity types against defaults
        valid_entities = set(settings.default_entities)
        invalid_entities = set(entity_list) - valid_entities
        if invalid_entities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entities: {', '.join(invalid_entities)}"
            )

    # Parse JSON payload
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")

        json_data = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {str(e)}"
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UTF-8 encoding in request body"
        )

    # Validate JSON structure
    if not validate_json_structure(json_data):
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON structure"
        )

    # Create deterministic cache for this request
    cache = DeterministicCache()

    # Anonymize the JSON data
    try:
        anonymized_data, pii_counts = anonymize_json_recursive(
            json_data, cache, strategy, entity_list
        )

        # Store PII counts in context for middleware logging
        context.pii_counts = pii_counts

        return anonymized_data

    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Anonymization processing failed"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint (not in requirements but useful for deployment)."""
    return {"status": "healthy"}


# Remove the health endpoint to comply with "exactly ONE endpoint" requirement
app.router.routes = [route for route in app.router.routes if getattr(route, 'path', '') != '/health']


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)