"""Advanced Presidio capabilities with multiple anonymization operators."""

import logging
from typing import Dict, List, Optional, Tuple
from presidio_analyzer import AnalyzerEngine, RecognizerResult, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from app.config import get_settings

logger = logging.getLogger(__name__)


class AdvancedAnonymizationEngine:
    """Extended anonymization engine with all Presidio operators."""

    def __init__(self, analyzer: AnalyzerEngine):
        """Initialize with existing analyzer engine."""
        self.analyzer = analyzer
        self.anonymizer = AnonymizerEngine()
        self.settings = get_settings()
        logger.info("Advanced anonymization engine initialized")

    def analyze_with_explanation(
        self,
        text: str,
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.35,
        allow_list: Optional[List[str]] = None,
        deny_list: Optional[List[str]] = None,
        return_decision_process: bool = False
    ) -> List[RecognizerResult]:
        """
        Analyze text for PII with optional allow/deny lists.

        Args:
            text: Text to analyze
            entities: List of entity types to detect
            score_threshold: Minimum confidence score (0.0-1.0)
            allow_list: Words to exclude from detection
            deny_list: Words to always detect as PII
            return_decision_process: Include analysis explanation

        Returns:
            List of RecognizerResult objects
        """
        if entities is None:
            entities = self.settings.default_entities

        # Create ad-hoc recognizers for deny list
        ad_hoc_recognizers = []
        if deny_list:
            deny_recognizer = self._create_deny_list_recognizer(deny_list)
            if deny_recognizer:
                ad_hoc_recognizers.append(deny_recognizer)

        try:
            results = self.analyzer.analyze(
                text=text,
                entities=entities,
                language='en',
                score_threshold=score_threshold,
                allow_list=allow_list,
                ad_hoc_recognizers=ad_hoc_recognizers if ad_hoc_recognizers else None,
                return_decision_process=return_decision_process
            )
            return results
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return []

    def anonymize_with_operator(
        self,
        text: str,
        results: List[RecognizerResult],
        operator: str,
        mask_char: str = "*",
        number_of_chars: int = 15,
        encrypt_key: Optional[str] = None
    ) -> str:
        """
        Anonymize text using specified operator.

        Args:
            text: Original text
            results: Analysis results from analyze_with_explanation
            operator: One of: redact, replace, mask, hash, encrypt, highlight
            mask_char: Character for masking (mask operator only)
            number_of_chars: Number of chars to mask (mask operator only)
            encrypt_key: AES encryption key (encrypt operator only)

        Returns:
            Anonymized text
        """
        if not results:
            return text

        # Configure operator
        operator_config = None
        if operator == "mask":
            operator_config = {
                "type": "mask",
                "masking_char": mask_char,
                "chars_to_mask": number_of_chars,
                "from_end": False
            }
        elif operator == "encrypt":
            if not encrypt_key:
                raise ValueError("encrypt_key required for encrypt operator")
            operator_config = {"key": encrypt_key}
        elif operator == "highlight":
            # Highlight uses custom operator with identity function
            operator = "custom"
            operator_config = {"lambda": lambda x: x}

        try:
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={"DEFAULT": OperatorConfig(operator, operator_config)}
            )
            return anonymized_result.text
        except Exception as e:
            logger.error(f"Anonymization error: {e}")
            return text

    def annotate_text(
        self,
        text: str,
        results: List[RecognizerResult]
    ) -> List[Tuple[str, Optional[str]]]:
        """
        Create annotated tokens for highlighting.

        Args:
            text: Original text
            results: Analysis results

        Returns:
            List of tuples: (text, entity_type or None)
        """
        if not results:
            return [(text, None)]

        # Use anonymizer to resolve overlaps
        highlighted = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("custom", {"lambda": lambda x: x})}
        )

        # Sort by start position
        sorted_items = sorted(highlighted.items, key=lambda x: x.start)

        tokens = []
        for i, item in enumerate(sorted_items):
            if i == 0:
                # Add text before first entity
                tokens.append((text[:item.start], None))

            # Add entity with its type
            tokens.append((text[item.start:item.end], item.entity_type))

            # Add text between entities or after last entity
            if i < len(sorted_items) - 1:
                tokens.append((text[item.end:sorted_items[i + 1].start], None))
            else:
                tokens.append((text[item.end:], None))

        return tokens

    def _create_deny_list_recognizer(
        self,
        deny_list: List[str]
    ) -> Optional[PatternRecognizer]:
        """Create ad-hoc recognizer for deny list words."""
        if not deny_list:
            return None

        return PatternRecognizer(
            supported_entity="GENERIC_PII",
            deny_list=deny_list
        )

    def create_regex_recognizer(
        self,
        regex: str,
        entity_type: str,
        score: float = 0.5,
        context: Optional[List[str]] = None
    ) -> Optional[PatternRecognizer]:
        """
        Create ad-hoc regex recognizer.

        Args:
            regex: Regular expression pattern
            entity_type: Entity type name
            score: Confidence score for matches
            context: Context words to boost confidence

        Returns:
            PatternRecognizer instance
        """
        if not regex:
            return None

        pattern = Pattern(name="Custom regex", regex=regex, score=score)
        return PatternRecognizer(
            supported_entity=entity_type,
            patterns=[pattern],
            context=context
        )

    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types."""
        return self.analyzer.get_supported_entities() + ["GENERIC_PII"]
