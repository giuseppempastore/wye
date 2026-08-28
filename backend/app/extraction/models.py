from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class IngredientEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_text: str = Field(min_length=1)
    quantity: str | None


class AllergenEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_text: str = Field(min_length=1)


class NutritionBasis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["per_100_g", "per_100_ml", "per_serving", "other"]
    quantity: float | None = Field(gt=0)
    unit: str | None
    raw_text: str | None


class NutritionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nutrient: Literal["energy", "fat", "saturated_fat", "carbohydrate", "sugars", "protein", "salt", "fiber"]
    raw_label: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    basis: NutritionBasis | None


class LabelExtractionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type: Literal["ingredients", "nutrition"]
    raw_text: str = Field(min_length=1)
    detected_languages: list[str]
    ingredient_list_text: str | None
    ingredients: list[IngredientEntry]
    allergens: list[AllergenEntry]
    nutrition: list[NutritionEntry]

    @model_validator(mode="after")
    def validate_document_content(self):
        if self.document_type == "ingredients":
            if not self.ingredient_list_text or not self.ingredient_list_text.strip():
                raise ValueError("ingredient_list_text is required for ingredients documents")
            if self.nutrition:
                raise ValueError("nutrition rows are not allowed in ingredients documents")
        elif self.ingredients or self.allergens or self.ingredient_list_text is not None:
            raise ValueError("ingredient fields are not allowed in nutrition documents")
        return self


class ExtractionRequest(BaseModel):
    image_bytes: bytes
    mime_type: str
    document_type: Literal["ingredients", "nutrition"]
    model: str
    prompt_version: str
    schema_version: str
    instructions: str
    output_schema: dict[str, Any]


class ProviderResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    output: Any
    raw_response: dict[str, Any] | None = None
    provider_request_id: str | None = None
    model_name: str
    model_version: str | None = None
