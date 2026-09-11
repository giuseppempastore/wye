import hashlib

from app.extraction.models import (
    IngredientTextNormalizationOutput,
    NutritionTextNormalizationOutput,
)


PROMPT_ID = "label_text_normalization_v1"
SCHEMA_VERSION = "2"
BASE_INSTRUCTIONS = """Normalize only the supplied OCR label segment into English.
Never add an ingredient or nutrient that is absent from the source segment.
Preserve source wording, percentages, allergen emphasis, values, and units.
Treat translations and OCR corrections as unverified candidates requiring review.
For an OCR correction, retain source_text and provide a conservative reason code.
Do not make scientific, health, hazard, scoring, or catalog-approval claims.
Return only data matching the supplied JSON schema."""
PROMPT_HASH = hashlib.sha256(BASE_INSTRUCTIONS.encode("utf-8")).hexdigest()
OUTPUT_SCHEMAS = {
    "ingredients": IngredientTextNormalizationOutput.model_json_schema(),
    "nutrition": NutritionTextNormalizationOutput.model_json_schema(),
}


def output_schema_for(document_type: str) -> dict:
    try:
        return OUTPUT_SCHEMAS[document_type]
    except KeyError as exc:
        raise ValueError("unsupported normalization document type") from exc


def instructions_for(document_type: str) -> str:
    focus = (
        "ingredient candidates and explicit allergen emphasis"
        if document_type == "ingredients"
        else "nutrition rows, canonical nutrient keys, values, units, and basis"
    )
    return f"{BASE_INSTRUCTIONS}\nDocument type: {document_type}. Return {focus}."
