"""Presidio-based anonymization engine with deterministic replacement."""

import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Union

from presidio_analyzer import AnalyzerEngine, RecognizerResult, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.config import get_settings
from app.phone_recognizer_enhanced import get_enhanced_phone_recognizer

logger = logging.getLogger(__name__)


class DeterministicCache:
    """Per-request cache for deterministic entity replacement."""

    def __init__(self) -> None:
        """Initialize empty cache."""
        self._cache: Dict[Tuple[str, str], str] = {}
        self._counters: Dict[str, int] = {}

    def get_replacement(self, entity_type: str, original_value: str) -> str:
        """Get deterministic replacement for an entity value."""
        # Normalize the original value for consistent caching
        normalized_value = original_value.strip().lower()
        cache_key = (entity_type, normalized_value)

        if cache_key not in self._cache:
            # Generate new replacement token
            self._counters[entity_type] = self._counters.get(entity_type, 0) + 1
            counter = self._counters[entity_type]
            replacement = f"<{entity_type}_{counter}>"
            self._cache[cache_key] = replacement
            logger.debug(f"New replacement: {original_value} -> {replacement}")

        return self._cache[cache_key]

    def get_hash_replacement(self, entity_type: str, original_value: str) -> str:
        """Get hash-based replacement for an entity value."""
        # Create a deterministic hash
        hash_input = f"{entity_type}:{original_value}".encode('utf-8')
        hash_value = hashlib.sha256(hash_input).hexdigest()[:8]
        return f"<{entity_type}_{hash_value}>"


class AnonymizationEngine:
    """Presidio-based anonymization engine with caching."""

    def __init__(self) -> None:
        """Initialize Presidio engines with enhanced phone recognizer."""
        self.settings = get_settings()

        # Create recognizer registry with predefined recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()

        # Replace default PhoneRecognizer with enhanced version
        try:
            # Remove default PhoneRecognizer if it exists
            registry.remove_recognizer("PhoneRecognizer")
            logger.info("Removed default PhoneRecognizer")
        except Exception as e:
            logger.warning(f"Could not remove default PhoneRecognizer: {e}")

        # Add enhanced phone recognizer
        enhanced_phone = get_enhanced_phone_recognizer()
        registry.add_recognizer(enhanced_phone)
        logger.info("Added enhanced PhoneRecognizer with custom patterns")

        # Initialize Presidio analyzer with custom registry
        self.analyzer = AnalyzerEngine(registry=registry)

        # Initialize Presidio anonymizer
        self.anonymizer = AnonymizerEngine()

        logger.info("Presidio engines initialized successfully with enhanced phone detection")

    def analyze_text(
        self,
        text: str,
        entities: Optional[List[str]] = None
    ) -> List[RecognizerResult]:
        """Analyze text for PII entities."""
        if entities is None:
            entities = self.settings.default_entities

        try:
            results = self.analyzer.analyze(
                text=text,
                entities=entities,
                language='en'
            )
            return results
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return []

    def anonymize_text_with_cache(
        self,
        text: str,
        cache: DeterministicCache,
        strategy: str = "replace",
        entities: Optional[List[str]] = None
    ) -> Tuple[str, Dict[str, int]]:
        """Anonymize text using deterministic cache."""
        if not isinstance(text, str):
            return text, {}

        # Analyze for PII
        results = self.analyze_text(text, entities)

        if not results:
            return text, {}

        # Count entities by type
        pii_counts: Dict[str, int] = {}
        for result in results:
            entity_type = result.entity_type
            pii_counts[entity_type] = pii_counts.get(entity_type, 0) + 1

        # Sort results by start position (reverse order for replacement)
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)

        # Apply replacements
        anonymized_text = text
        for result in sorted_results:
            original_value = text[result.start:result.end]

            if strategy == "hash":
                replacement = cache.get_hash_replacement(result.entity_type, original_value)
            else:  # default "replace"
                replacement = cache.get_replacement(result.entity_type, original_value)

            # Replace in the text
            anonymized_text = (
                anonymized_text[:result.start] +
                replacement +
                anonymized_text[result.end:]
            )

        return anonymized_text, pii_counts

    def anonymize_with_operators(
        self,
        text: str,
        strategy: str = "replace",
        entities: Optional[List[str]] = None
    ) -> Tuple[str, Dict[str, int]]:
        """Anonymize using Presidio operators (non-deterministic)."""
        if not isinstance(text, str):
            return text, {}

        results = self.analyze_text(text, entities)

        if not results:
            return text, {}

        # Count entities
        pii_counts: Dict[str, int] = {}
        for result in results:
            pii_counts[result.entity_type] = pii_counts.get(result.entity_type, 0) + 1

        # Configure operators based on strategy
        if strategy == "hash":
            operators = {entity: OperatorConfig("hash") for entity in self.settings.default_entities}
        else:
            operators = {entity: OperatorConfig("replace") for entity in self.settings.default_entities}

        try:
            # Anonymize text
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            return anonymized_result.text, pii_counts
        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return text, pii_counts


# Global anonymization engine instance
anonymization_engine = AnonymizationEngine()