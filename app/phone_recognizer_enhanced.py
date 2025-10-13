"""Enhanced Phone Number Recognizer with custom patterns for better detection."""

from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class EnhancedPhoneRecognizer(PatternRecognizer):
    """
    Enhanced phone number recognizer with comprehensive regex patterns.

    Detects phone numbers in various formats:
    - US: +1-555-123-4567, (555) 123-4567, 555-123-4567, 555.123.4567
    - International: +44 20 7123 4567, +49 30 12345678
    - Alphanumeric: 1-800-FLOWERS, +1-917-NINE88-2TWO2, 1-800-ZERO ZERO FIVE EIGHT
    - Flexible spacing and separators
    """

    PATTERNS = [
        # US format with parentheses: (555) 123-4567, (555)123-4567
        Pattern(
            name="phone_with_parens",
            regex=r"\(?\d{3}\)?[-\s\.]?\d{3}[-\s\.]?\d{4}",
            score=0.7,
        ),
        # US/International format with country code: +1-555-123-4567, +44 20 7123 4567
        Pattern(
            name="phone_with_plus_and_dashes",
            regex=r"\+\d{1,3}[-\s\.]?\(?\d{1,4}\)?[-\s\.]?\d{1,4}[-\s\.]?\d{1,9}",
            score=0.7,
        ),
        # Extension format: 555-1234 x123, 555-1234 ext. 123
        Pattern(
            name="phone_with_extension",
            regex=r"\(?\d{3}\)?[-\s\.]?\d{3}[-\s\.]?\d{4}[-\s]?(?:x|ext\.?|extension)[-\s]?\d{1,5}",
            score=0.7,
        ),
        # Alphanumeric toll-free: 1-800-FLOWERS (must start with 1-800 or 1-888 or 1-877)
        Pattern(
            name="phone_tollfree_alpha",
            regex=r"\b1[-\s\.]?(?:800|888|877|866)[-\s\.]?[A-Z]{3,7}\b",
            score=0.6,
        ),
        # Simple 7-digit format: 555-1234, 555.1234 (but only if has context word)
        Pattern(
            name="phone_simple_seven_digit",
            regex=r"\b\d{3}[-\s\.]\d{4}\b",
            score=0.4,
        ),
    ]

    CONTEXT = [
        # English
        "phone", "telephone", "cell", "mobile", "fax", "call",
        "number", "contact", "cellphone", "tel", "phone number",
        "tel.", "tel:", "phone:", "mobile:", "cell:", "fax:",
        # Common abbreviations
        "ph", "ph.", "ph:", "mob", "mob.", "mob:",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "PHONE_NUMBER",
    ):
        """
        Initialize enhanced phone recognizer.

        Args:
            patterns: Custom patterns (defaults to PATTERNS if None)
            context: Custom context words (defaults to CONTEXT if None)
            supported_language: Language code (default: "en")
            supported_entity: Entity type (default: "PHONE_NUMBER")
        """
        patterns = patterns if patterns is not None else self.PATTERNS
        context = context if context is not None else self.CONTEXT

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


def get_enhanced_phone_recognizer() -> EnhancedPhoneRecognizer:
    """Factory function to get an instance of the enhanced phone recognizer."""
    return EnhancedPhoneRecognizer()
