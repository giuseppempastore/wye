import hashlib
from app.extraction.models import LabelExtractionOutput

PROMPT_ID = "label_extraction_v1"
SCHEMA_VERSION = "1"
BASE_INSTRUCTIONS = """Transcribe only information visibly present on this food label image.
Do not guess, translate, normalize to a catalog, infer missing values, or add scientific or risk claims.
Preserve the original wording and order. Omit or use null for information that is not readable.
Return data matching the supplied JSON schema exactly."""
PROMPT_HASH = hashlib.sha256(BASE_INSTRUCTIONS.encode("utf-8")).hexdigest()


def instructions_for(document_type: str) -> str:
    focus = "ingredient list and explicitly stated allergens" if document_type == "ingredients" else "nutrition table rows and their visible basis"
    return f"{BASE_INSTRUCTIONS}\nDocument type: {document_type}. Extract only the {focus}."


OUTPUT_SCHEMA = LabelExtractionOutput.model_json_schema()
