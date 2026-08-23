import json
import os
import re
from typing import Any

try:
    import openai
except Exception:  # pragma: no cover
    openai = None


def parse_ai_response(payload: Any) -> dict:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("AI payload must be a JSON object")

    ingredients = payload.get("ingredients", [])
    nutrition = payload.get("nutrition", {})

    if not isinstance(ingredients, list):
        ingredients = []
    if not isinstance(nutrition, dict):
        nutrition = {}

    cleaned_ingredients: list[str] = []
    for item in ingredients:
        if isinstance(item, str):
            text = item.strip()
            if text:
                cleaned_ingredients.append(text)

    cleaned_nutrition: dict[str, Any] = {}
    for key, value in nutrition.items():
        if value is None:
            continue
        cleaned_nutrition[str(key)] = value

    return {
        "ingredients": cleaned_ingredients,
        "nutrition": cleaned_nutrition,
    }


def _fallback_parse(raw_text: str) -> dict:
    cleaned = raw_text.replace("\r", "\n")
    lines = [line.strip() for line in cleaned.split("\n")]

    nutrition_block_keywords = {
        "nutrition",
        "nutrizione",
        "nutritional",
        "nutrition facts",
        "valori nutrizionali",
        "valori nutrizionali per",
        "informazioni nutrizionali",
        "per 100 g",
        "per 100g",
        "energy",
        "energia",
        "calories",
        "calorie",
        "kcal",
        "protein",
        "proteine",
        "carbohydrates",
        "carboidrati",
        "fat",
        "grassi",
        "sugar",
        "zuccheri",
        "fiber",
        "fibre",
        "sodium",
        "sodio",
    }

    ingredients: list[str] = []
    nutrition: dict[str, Any] = {}
    in_nutrition_section = False

    def parse_nutrition_values(text: str) -> None:
        matches = re.findall(
            r"(?i)(energia|energy|calorie|calories|kcal|protein|proteine|carbohydrates|carboidrati|carbs|fat|grassi|sugar|zuccheri|saturated fat|fiber|fibre|sodium|sodio)\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:g|mg|kcal)?",
            text,
        )
        for label, value in matches:
            key = label.lower().replace(" ", "_")
            if "energia" in key or "energy" in key or "calorie" in key:
                nutrition["energy_kcal"] = float(value.replace(",", "."))
            elif "protein" in key or "proteine" in key:
                nutrition["protein_g"] = float(value.replace(",", "."))
            elif "carbohydrate" in key or "carbs" in key or "carboidrati" in key:
                nutrition["carbs_g"] = float(value.replace(",", "."))
            elif ("fat" in key and "saturated" not in key) or "grassi" in key:
                nutrition["fat_g"] = float(value.replace(",", "."))
            elif "saturated" in key:
                nutrition["saturated_fat_g"] = float(value.replace(",", "."))
            elif "sugar" in key or "zuccheri" in key:
                nutrition["sugar_g"] = float(value.replace(",", "."))
            elif "fiber" in key or "fibre" in key:
                nutrition["fiber_g"] = float(value.replace(",", "."))
            elif "sodium" in key or "sodio" in key:
                nutrition["sodium_mg"] = float(value.replace(",", "."))

    for line in lines:
        lowered = line.lower().strip()
        if not lowered:
            continue

        if any(keyword in lowered for keyword in nutrition_block_keywords):
            in_nutrition_section = True
            parse_nutrition_values(line)
            continue

        if "ingredient" in lowered and re.fullmatch(r"[\W_]*ingredient[\W_]*", lowered):
            continue

        if in_nutrition_section:
            parse_nutrition_values(line)
            if any(keyword in lowered for keyword in ["kcal", "g", "mg", "%", "calorie", "proteine", "grassi", "carboidrati", "zuccheri", "sodio", "energia"]):
                continue

        if re.search(r"\d", lowered):
            if any(keyword in lowered for keyword in ["kcal", "g", "mg", "%"]):
                continue

        candidate = re.sub(r"\s+", " ", line).strip()
        if len(candidate) < 2:
            continue
        if candidate.lower() in {"ingredients", "ingredienti", "nutrition", "nutrizione", "nutrition facts", "valori nutrizionali"}:
            continue
        ingredients.append(candidate)

    return {"ingredients": ingredients, "nutrition": nutrition}


def normalize_label_text_with_ai(raw_text: str, label_type: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        return _fallback_parse(raw_text)

    client = openai.OpenAI(api_key=api_key)

    if label_type == "ingredients":
        prompt = """
        Extract only the ingredient list from the text below.
        Return valid JSON with a single key named "ingredients" whose value is an array of clean ingredient names in English.
        Ignore the rest of the label, remove duplicates, remove marketing text, and do not include measurements, units, or photo descriptions.
        Text:
        """ + raw_text
    else:
        prompt = """
        Extract the nutrition values from the text below.
        Return valid JSON with a single key named "nutrition" whose value is an object containing ONLY numeric values for:
        energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg.
        Use English keys and keep values as numbers (not strings). If a value is missing, omit it rather than guessing.
        Text:
        """ + raw_text

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a food label OCR normalization assistant. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    content = getattr(response, "output_text", None)
    if not content:
        raise RuntimeError("Empty AI response")

    return parse_ai_response(content)


def normalize_photo_text(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {"ingredients": [], "nutrition": {}}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        return _fallback_parse(raw_text)

    client = openai.OpenAI(api_key=api_key)
    prompt = """
    Extract from the full OCR text of the food product label below:
    1) the ingredient list, as a clean array of ingredient names in English
    2) the nutrition facts, as an object with numeric values for: energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg

    Rules:
    - Ignore the barcode, marketing copy, logos, and everything that is not part of the ingredients or nutrition section.
    - Keep only real ingredient names, in English.
    - Remove duplicates and units.
    - If a nutrition value is missing, omit it.
    - Return valid JSON with exactly two keys: "ingredients" and "nutrition".

    OCR text:
    """ + raw_text

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a food label OCR extraction assistant. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    content = getattr(response, "output_text", None)
    if not content:
        raise RuntimeError("Empty AI response")

    return parse_ai_response(content)
