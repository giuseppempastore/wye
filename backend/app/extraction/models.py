import re
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
    value: float = Field(ge=0)
    unit: str = Field(min_length=1)
    basis: NutritionBasis | None

    @model_validator(mode="after")
    def validate_unit_for_nutrient(self):
        normalized_unit = self.unit.strip().lower()
        if self.nutrient == "energy":
            if normalized_unit not in {"kj", "kcal"}:
                raise ValueError("energy unit must be kJ or kcal")
        elif normalized_unit not in {"g", "mg"}:
            raise ValueError("nutrient unit must be g or mg")
        return self


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


LanguageCode = str


class CanonicalEnglishIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(min_length=1, max_length=500)
    english_candidate: str | None = Field(default=None, max_length=500)
    normalized_candidate: str | None = Field(default=None, max_length=255)
    confidence: float | None = Field(default=None, ge=0, le=1)
    needs_review: bool = True
    correction_reason: str | None = Field(
        default=None, pattern=r"^[a-z0-9_]{1,80}$"
    )
    allergen_emphasis: bool = False


class CanonicalNutritionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_key: Literal[
        "energy_kj",
        "energy_kcal",
        "fat_g",
        "saturated_fat_g",
        "carbohydrate_g",
        "sugars_g",
        "fibre_g",
        "protein_g",
        "salt_g",
        "sodium_mg",
    ]
    source_label: str = Field(min_length=1, max_length=255)
    source_value: str = Field(min_length=1, max_length=50)
    source_unit: str = Field(min_length=1, max_length=20)
    normalized_value: float = Field(ge=0)
    normalized_unit: Literal["kj", "kcal", "g", "mg"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    needs_review: bool = True

    @model_validator(mode="after")
    def validate_canonical_unit_and_bounds(self):
        expected_unit = (
            "kj" if self.canonical_key == "energy_kj"
            else "kcal" if self.canonical_key == "energy_kcal"
            else "mg" if self.canonical_key == "sodium_mg"
            else "g"
        )
        maximum = (
            4000 if self.canonical_key == "energy_kj"
            else 900 if self.canonical_key == "energy_kcal"
            else 100000 if self.canonical_key == "sodium_mg"
            else 100
        )
        if self.normalized_unit != expected_unit:
            raise ValueError("canonical nutrient unit does not match its key")
        if self.normalized_value > maximum:
            raise ValueError("canonical nutrient value exceeds its bound")
        return self


class TextNormalizationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_language: LanguageCode = Field(
        max_length=10,
        pattern=r"^(?:und|[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)$",
    )
    source_segment: str = Field(min_length=1, max_length=12000)
    canonical_english_items: list[CanonicalEnglishIngredient] = Field(
        default_factory=list, max_length=200
    )
    nutrition_items: list[CanonicalNutritionItem] = Field(
        default_factory=list, max_length=50
    )
    nutrition_basis: Literal[
        "per_100_g", "per_100_ml", "per_serving", "other"
    ] | None = None
    warnings: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_document_shape(self):
        if self.canonical_english_items and self.nutrition_items:
            raise ValueError("ingredient and nutrition outputs cannot be mixed")
        if any(
            not re.fullmatch(r"[a-z0-9_]{1,80}", value)
            for value in self.warnings
        ):
            raise ValueError("warnings must contain safe codes")
        return self


class IngredientTextNormalizationOutput(TextNormalizationOutput):
    nutrition_items: list[CanonicalNutritionItem] = Field(
        default_factory=list, max_length=0
    )
    nutrition_basis: None = None


class NutritionTextNormalizationOutput(TextNormalizationOutput):
    canonical_english_items: list[CanonicalEnglishIngredient] = Field(
        default_factory=list, max_length=0
    )


class TextNormalizationProviderRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    source_language: LanguageCode
    document_type: Literal["ingredients", "nutrition"]
    raw_text: str
    target_language: Literal["en"] = "en"
    schema_version: str
    parser_version: str
    prompt_version: str
    model: str
    instructions: str
    output_schema: dict[str, Any]
