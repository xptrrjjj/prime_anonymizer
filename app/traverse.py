"""Recursive JSON traversal and anonymization utilities."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.anonymize import DeterministicCache, anonymization_engine

logger = logging.getLogger(__name__)

JsonValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


def anonymize_json_recursive(
    data: JsonValue,
    cache: DeterministicCache,
    strategy: str = "replace",
    entities: Optional[List[str]] = None
) -> Tuple[JsonValue, Dict[str, int]]:
    """
    Recursively anonymize JSON data while preserving structure.

    Args:
        data: The JSON data to anonymize (dict, list, or primitive)
        cache: Deterministic cache for consistent replacements within request
        strategy: Anonymization strategy ("replace" or "hash")
        entities: List of entity types to detect (uses defaults if None)

    Returns:
        Tuple of (anonymized_data, aggregated_pii_counts)
    """
    total_pii_counts: Dict[str, int] = {}

    def merge_counts(counts: Dict[str, int]) -> None:
        """Merge PII counts into the total."""
        for entity_type, count in counts.items():
            total_pii_counts[entity_type] = total_pii_counts.get(entity_type, 0) + count

    def traverse(obj: JsonValue) -> JsonValue:
        """Recursively traverse and anonymize the object."""
        if obj is None:
            return None
        elif isinstance(obj, bool):
            return obj
        elif isinstance(obj, (int, float)):
            return obj
        elif isinstance(obj, str):
            # Only anonymize string leaf values
            anonymized_text, pii_counts = anonymization_engine.anonymize_text_with_cache(
                obj, cache, strategy, entities
            )
            merge_counts(pii_counts)
            return anonymized_text
        elif isinstance(obj, dict):
            # Recursively process dictionary values, preserve keys
            result = {}
            for key, value in obj.items():
                # Keys are never anonymized, only values
                result[key] = traverse(value)
            return result
        elif isinstance(obj, list):
            # Recursively process list items, preserve order
            return [traverse(item) for item in obj]
        else:
            # For any other type (shouldn't happen with valid JSON)
            logger.warning(f"Unexpected data type during traversal: {type(obj)}")
            return obj

    try:
        anonymized_data = traverse(data)
        logger.debug(f"Anonymization completed. Total PII found: {sum(total_pii_counts.values())}")
        return anonymized_data, total_pii_counts
    except Exception as e:
        logger.error(f"Error during JSON traversal: {e}")
        return data, total_pii_counts


def validate_json_structure(data: Any) -> bool:
    """
    Validate that the data represents a valid JSON structure.

    Args:
        data: Data to validate

    Returns:
        True if valid JSON structure, False otherwise
    """
    def is_valid_json_value(obj: Any) -> bool:
        """Check if object is a valid JSON value."""
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return True
        elif isinstance(obj, dict):
            return all(
                isinstance(key, str) and is_valid_json_value(value)
                for key, value in obj.items()
            )
        elif isinstance(obj, list):
            return all(is_valid_json_value(item) for item in obj)
        else:
            return False

    return is_valid_json_value(data)


def get_payload_stats(data: JsonValue) -> Dict[str, int]:
    """
    Get statistics about the JSON payload structure.

    Args:
        data: JSON data to analyze

    Returns:
        Dictionary with payload statistics
    """
    stats = {
        "total_strings": 0,
        "total_objects": 0,
        "total_arrays": 0,
        "total_primitives": 0,
        "max_depth": 0
    }

    def analyze(obj: JsonValue, depth: int = 0) -> None:
        """Recursively analyze structure."""
        stats["max_depth"] = max(stats["max_depth"], depth)

        if isinstance(obj, str):
            stats["total_strings"] += 1
        elif isinstance(obj, (int, float, bool)) or obj is None:
            stats["total_primitives"] += 1
        elif isinstance(obj, dict):
            stats["total_objects"] += 1
            for value in obj.values():
                analyze(value, depth + 1)
        elif isinstance(obj, list):
            stats["total_arrays"] += 1
            for item in obj:
                analyze(item, depth + 1)

    analyze(data)
    return stats