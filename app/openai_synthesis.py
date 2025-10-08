"""OpenAI integration for synthetic data generation."""

import logging
from typing import List, Optional
from collections import namedtuple
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

OpenAIParams = namedtuple(
    "OpenAIParams",
    ["api_key", "model", "api_base", "deployment_id", "api_version", "api_type"]
)


def create_synthesis_prompt(anonymized_text: str) -> str:
    """
    Create prompt for OpenAI to generate synthetic data.

    Args:
        anonymized_text: Text with PII placeholders like <PERSON>, <LOCATION>

    Returns:
        Formatted prompt for OpenAI
    """
    prompt = f"""
Your role is to create synthetic text based on de-identified text with placeholders instead of Personally Identifiable Information (PII).
Replace the placeholders (e.g., <PERSON>, <DATE>, <EMAIL_ADDRESS>) with fake values.

Instructions:

a. Use completely random numbers, so every digit is drawn between 0 and 9.
b. Use realistic names that come from diverse genders, ethnicities and countries.
c. If there are no placeholders, return the text as is.
d. Keep the formatting as close to the original as possible.
e. If PII exists in the input, replace it with fake values in the output.
f. Remove whitespace before and after the generated text

Examples:
input: [[TEXT STARTS]] How do I change the limit on my credit card <CREDIT_CARD>?[[TEXT ENDS]]
output: How do I change the limit on my credit card 2539 3519 2345 1555?

input: [[TEXT STARTS]]<PERSON> was the chief science officer at <ORGANIZATION>.[[TEXT ENDS]]
output: Katherine Buckjov was the chief science officer at NASA.

input: [[TEXT STARTS]]Cameroon lives in <LOCATION>.[[TEXT ENDS]]
output: Vladimir lives in Moscow.

input: [[TEXT STARTS]]{anonymized_text}[[TEXT ENDS]]
output:"""
    return prompt


def call_openai_completion(
    prompt: str,
    openai_params: OpenAIParams,
    max_tokens: int = 256
) -> str:
    """
    Call OpenAI completion API.

    Args:
        prompt: The prompt for completion
        openai_params: OpenAI configuration
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text from OpenAI
    """
    try:
        if openai_params.api_type.lower() == "azure":
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_version=openai_params.api_version,
                api_key=openai_params.api_key,
                azure_endpoint=openai_params.api_base,
                azure_deployment=openai_params.deployment_id,
            )
        else:
            from openai import OpenAI
            client = OpenAI(api_key=openai_params.api_key)

        response = client.completions.create(
            model=openai_params.model,
            prompt=prompt,
            max_tokens=max_tokens,
        )

        return response.choices[0].text.strip()

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


def synthesize_text(
    text: str,
    results: List[RecognizerResult],
    openai_params: OpenAIParams
) -> str:
    """
    Generate synthetic text using OpenAI.

    Args:
        text: Original text
        results: PII detection results
        openai_params: OpenAI configuration

    Returns:
        Synthetic text with fake PII values
    """
    if not openai_params.api_key:
        raise ValueError("OpenAI API key is required for synthesis")

    # First anonymize with placeholders
    anonymizer = AnonymizerEngine()
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace")}
    )

    # Create prompt and call OpenAI
    prompt = create_synthesis_prompt(anonymized.text)
    logger.info(f"Synthesis prompt created, length: {len(prompt)}")

    synthetic_text = call_openai_completion(prompt, openai_params)
    return synthetic_text
