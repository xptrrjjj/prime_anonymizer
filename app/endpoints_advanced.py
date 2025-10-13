"""Advanced API endpoints for Presidio demo capabilities."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.anonymize import anonymization_engine
from app.presidio_advanced import AdvancedAnonymizationEngine
from app.openai_synthesis import OpenAIParams, synthesize_text

logger = logging.getLogger(__name__)

# Create router for advanced endpoints
router = APIRouter()

# Initialize advanced engine
advanced_engine = AdvancedAnonymizationEngine(anonymization_engine.analyzer)


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for text analysis."""
    text: str = Field(..., description="Text to analyze for PII")
    entities: Optional[List[str]] = Field(None, description="Entity types to detect")
    score_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Minimum confidence score")
    allow_list: Optional[List[str]] = Field(None, description="Words to exclude from detection")
    deny_list: Optional[List[str]] = Field(None, description="Words to always detect as PII")
    return_decision_process: bool = Field(False, description="Include analysis explanation")


class AnalyzeResponse(BaseModel):
    """Response model for analysis results."""
    text: str
    findings: List[Dict[str, Any]]
    summary: Dict[str, int]


class AnonymizeAdvancedRequest(BaseModel):
    """Request model for advanced anonymization."""
    text: str = Field(..., description="Text to anonymize")
    operator: str = Field("replace", description="Anonymization operator: redact, replace, mask, hash, encrypt, highlight")
    entities: Optional[List[str]] = Field(None, description="Entity types to detect")
    score_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Minimum confidence score")
    allow_list: Optional[List[str]] = Field(None, description="Words to exclude from detection")
    deny_list: Optional[List[str]] = Field(None, description="Words to always detect as PII")
    mask_char: str = Field("*", max_length=1, description="Character for masking (mask operator)")
    number_of_chars: int = Field(15, ge=0, description="Number of characters to mask (mask operator)")
    encrypt_key: Optional[str] = Field(None, description="AES encryption key (encrypt operator)")


class AnonymizeAdvancedResponse(BaseModel):
    """Response model for advanced anonymization."""
    original_text: str
    anonymized_text: str
    operator: str
    findings: List[Dict[str, Any]]
    summary: Dict[str, int]


class AnnotateResponse(BaseModel):
    """Response model for text annotation."""
    text: str
    annotations: List[Dict[str, Any]]
    summary: Dict[str, int]


class SynthesizeRequest(BaseModel):
    """Request model for OpenAI synthesis."""
    text: str = Field(..., description="Text to synthesize")
    entities: Optional[List[str]] = Field(None, description="Entity types to detect")
    score_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Minimum confidence score")
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field("gpt-3.5-turbo-instruct", description="OpenAI model name")
    openai_api_type: str = Field("openai", description="API type: openai or azure")
    azure_endpoint: Optional[str] = Field(None, description="Azure OpenAI endpoint")
    azure_deployment: Optional[str] = Field(None, description="Azure OpenAI deployment name")
    api_version: Optional[str] = Field("2023-05-15", description="Azure OpenAI API version")


class SynthesizeResponse(BaseModel):
    """Response model for synthesis."""
    original_text: str
    synthetic_text: str
    findings: List[Dict[str, Any]]
    summary: Dict[str, int]


class EntitiesResponse(BaseModel):
    """Response model for supported entities."""
    entities: List[str]
    count: int


@router.post("/analyze", response_model=AnalyzeResponse, summary="Analyze text for PII")
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze text for PII without anonymization.

    This endpoint detects PII entities and returns detailed findings including:
    - Entity type (PERSON, EMAIL_ADDRESS, PHONE_NUMBER, etc.)
    - Text snippet
    - Start and end positions
    - Confidence score
    - Optional: Analysis decision process

    Supports custom allow/deny lists and configurable entity types.
    """
    try:
        results = advanced_engine.analyze_with_explanation(
            text=request.text,
            entities=request.entities,
            score_threshold=request.score_threshold,
            allow_list=request.allow_list,
            deny_list=request.deny_list,
            return_decision_process=request.return_decision_process
        )

        # Format findings
        findings = []
        summary = {}
        for result in results:
            finding = {
                "entity_type": result.entity_type,
                "text": request.text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "score": round(result.score, 3)
            }

            if request.return_decision_process and result.analysis_explanation:
                # Use to_dict() method to get all available fields
                if hasattr(result.analysis_explanation, 'to_dict'):
                    explanation = result.analysis_explanation.to_dict()
                else:
                    # Fallback for older versions
                    explanation = {
                        "recognizer": result.analysis_explanation.recognizer,
                        "original_score": result.analysis_explanation.original_score,
                    }

                    # Add all possible fields
                    optional_fields = {
                        'pattern_name': None,
                        'pattern': None,
                        'validation_result': None,
                        'score_context_improvement': None,
                        'score': None,
                        'supportive_context_word': None,
                        'textual_explanation': None
                    }

                    for field, default in optional_fields.items():
                        if hasattr(result.analysis_explanation, field):
                            value = getattr(result.analysis_explanation, field, default)
                            if value is not None:
                                explanation[field] = value

                # Generate textual_explanation if it's null or missing
                if not explanation.get('textual_explanation'):
                    recognizer = explanation.get('recognizer', 'Unknown')
                    pattern_name = explanation.get('pattern_name')

                    if pattern_name:
                        explanation['textual_explanation'] = f"Identified as {result.entity_type} by {recognizer} using pattern `{pattern_name}`"
                    else:
                        explanation['textual_explanation'] = f"Identified as {result.entity_type} by {recognizer}"

                finding["analysis_explanation"] = explanation

            findings.append(finding)
            summary[result.entity_type] = summary.get(result.entity_type, 0) + 1

        return AnalyzeResponse(
            text=request.text,
            findings=findings,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/anonymize-advanced", response_model=AnonymizeAdvancedResponse, summary="Anonymize text with advanced operators")
async def anonymize_advanced(request: AnonymizeAdvancedRequest):
    """
    Anonymize text using various operators.

    Supported operators:
    - **redact**: Completely remove PII text
    - **replace**: Replace with entity type placeholder (e.g., <PERSON>)
    - **mask**: Replace N characters with mask character (default: *)
    - **hash**: Replace with SHA-256 hash
    - **encrypt**: Replace with AES encryption (requires encrypt_key)
    - **highlight**: Return original text with PII positions for highlighting

    Supports custom allow/deny lists and configurable detection thresholds.
    """
    valid_operators = ["redact", "replace", "mask", "hash", "encrypt", "highlight"]
    if request.operator not in valid_operators:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operator. Must be one of: {', '.join(valid_operators)}"
        )

    if request.operator == "encrypt" and not request.encrypt_key:
        raise HTTPException(
            status_code=400,
            detail="encrypt_key is required for encrypt operator"
        )

    try:
        # Analyze text
        results = advanced_engine.analyze_with_explanation(
            text=request.text,
            entities=request.entities,
            score_threshold=request.score_threshold,
            allow_list=request.allow_list,
            deny_list=request.deny_list,
            return_decision_process=False
        )

        # Anonymize text
        anonymized_text = advanced_engine.anonymize_with_operator(
            text=request.text,
            results=results,
            operator=request.operator,
            mask_char=request.mask_char,
            number_of_chars=request.number_of_chars,
            encrypt_key=request.encrypt_key
        )

        # Format findings
        findings = []
        summary = {}
        for result in results:
            findings.append({
                "entity_type": result.entity_type,
                "text": request.text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "score": round(result.score, 3)
            })
            summary[result.entity_type] = summary.get(result.entity_type, 0) + 1

        return AnonymizeAdvancedResponse(
            original_text=request.text,
            anonymized_text=anonymized_text,
            operator=request.operator,
            findings=findings,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Anonymization failed: {str(e)}")


@router.post("/annotate", response_model=AnnotateResponse, summary="Annotate text with PII highlighting")
async def annotate_text(request: AnalyzeRequest):
    """
    Annotate text for PII highlighting.

    Returns the text broken into segments with entity type labels,
    suitable for frontend highlighting/visualization.

    Each annotation contains:
    - text: The text segment
    - entity_type: The PII entity type (or null for non-PII text)
    - start: Start position in original text
    - end: End position in original text
    """
    try:
        # Analyze text
        results = advanced_engine.analyze_with_explanation(
            text=request.text,
            entities=request.entities,
            score_threshold=request.score_threshold,
            allow_list=request.allow_list,
            deny_list=request.deny_list,
            return_decision_process=False
        )

        # Create annotations
        tokens = advanced_engine.annotate_text(request.text, results)

        # Format annotations with positions
        annotations = []
        position = 0
        for text_segment, entity_type in tokens:
            if text_segment:  # Skip empty segments
                annotations.append({
                    "text": text_segment,
                    "entity_type": entity_type,
                    "start": position,
                    "end": position + len(text_segment)
                })
                position += len(text_segment)

        # Create summary
        summary = {}
        for result in results:
            summary[result.entity_type] = summary.get(result.entity_type, 0) + 1

        return AnnotateResponse(
            text=request.text,
            annotations=annotations,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Annotation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Annotation failed: {str(e)}")


@router.post("/synthesize", response_model=SynthesizeResponse, summary="Generate synthetic text with OpenAI")
async def synthesize_text_endpoint(request: SynthesizeRequest):
    """
    Generate synthetic text using OpenAI.

    Detects PII in the original text, replaces it with placeholders,
    then uses OpenAI to generate realistic fake values.

    Requires OpenAI API key. Supports both OpenAI and Azure OpenAI.

    Example:
    - Original: "My name is John Smith and I live in Seattle"
    - Synthetic: "My name is Maria Rodriguez and I live in Toronto"
    """
    try:
        # Analyze text
        results = advanced_engine.analyze_with_explanation(
            text=request.text,
            entities=request.entities,
            score_threshold=request.score_threshold,
            allow_list=None,
            deny_list=None,
            return_decision_process=False
        )

        if not results:
            # No PII found, return original text
            return SynthesizeResponse(
                original_text=request.text,
                synthetic_text=request.text,
                findings=[],
                summary={}
            )

        # Create OpenAI params
        openai_params = OpenAIParams(
            api_key=request.openai_api_key,
            model=request.openai_model,
            api_base=request.azure_endpoint,
            deployment_id=request.azure_deployment,
            api_version=request.api_version,
            api_type=request.openai_api_type
        )

        # Generate synthetic text
        synthetic_text = synthesize_text(
            text=request.text,
            results=results,
            openai_params=openai_params
        )

        # Format findings
        findings = []
        summary = {}
        for result in results:
            findings.append({
                "entity_type": result.entity_type,
                "text": request.text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "score": round(result.score, 3)
            })
            summary[result.entity_type] = summary.get(result.entity_type, 0) + 1

        return SynthesizeResponse(
            original_text=request.text,
            synthetic_text=synthetic_text,
            findings=findings,
            summary=summary
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/entities", response_model=EntitiesResponse, summary="Get supported entity types")
async def get_entities():
    """
    Get list of supported PII entity types.

    Returns all entity types that can be detected by the analyzer,
    including standard Presidio entities and custom recognizers.

    Common entities include:
    - PERSON
    - EMAIL_ADDRESS
    - PHONE_NUMBER
    - CREDIT_CARD
    - LOCATION
    - DATE_TIME
    - IP_ADDRESS
    - And many more...
    """
    try:
        entities = advanced_engine.get_supported_entities()
        return EntitiesResponse(
            entities=sorted(entities),
            count=len(entities)
        )
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")
