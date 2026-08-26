import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any

from app.data.ingredients import normalize_ingredient

try:
    import openai
except Exception:  # pragma: no cover
    openai = None


def _get_ai_key() -> str | None:
    for env_name in ("WYE_AI_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(env_name)
        if value and value.strip():
            return value.strip()
    return None


def _call_gemini_api(prompt: str, image_url: str | None = None, raw_text: str | None = None) -> str | None:
    api_key = _get_ai_key()
    if not api_key or not api_key.startswith(("AIza", "AQ.")):
        return None

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={urllib.parse.quote(api_key)}"

    parts: list[dict[str, Any]] = [{"text": prompt}]
    if image_url:
        header, _, data = image_url.partition(",")
        mime_type = "image/jpeg"
        if "image/png" in header:
            mime_type = "image/png"
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": data,
            }
        })
    if raw_text and raw_text.strip():
        parts.append({"text": "Additional OCR text for context:\n" + raw_text.strip()})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "product_name": {"type": "STRING"},
                    "brand_name": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "product_type": {"type": "STRING"},
                    "ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "nutrition": {
                        "type": "OBJECT",
                        "properties": {
                            "energy_kcal": {"type": "NUMBER"},
                            "protein_g": {"type": "NUMBER"},
                            "carbs_g": {"type": "NUMBER"},
                            "fat_g": {"type": "NUMBER"},
                            "sugar_g": {"type": "NUMBER"},
                            "saturated_fat_g": {"type": "NUMBER"},
                            "fiber_g": {"type": "NUMBER"},
                            "sodium_mg": {"type": "NUMBER"},
                        },
                        "required": ["energy_kcal", "protein_g", "carbs_g", "fat_g"],
                    },
                },
                "required": ["ingredients", "nutrition"],
            },
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    candidates = body.get("candidates") or []
    if not candidates:
        return None
    text = candidates[0].get("content", {}).get("parts", [])
    for part in text:
        if isinstance(part, dict) and part.get("text"):
            return part.get("text")
    return None


def _normalize_nutrition_keys(key: str) -> str:
    alias_map = {
        "energy": "energy_kcal",
        "energy_kcal": "energy_kcal",
        "kcal": "energy_kcal",
        "calorie": "energy_kcal",
        "calories": "energy_kcal",
        "energia": "energy_kcal",
        "proteine": "protein_g",
        "protein": "protein_g",
        "proteins": "protein_g",
        "proteins_g": "protein_g",
        "carboidrati": "carbs_g",
        "carbohydrates": "carbs_g",
        "carbs": "carbs_g",
        "carbohydrate": "carbs_g",
        "fat": "fat_g",
        "grassi": "fat_g",
        "saturated_fat": "saturated_fat_g",
        "grassi_saturi": "saturated_fat_g",
        "sugar": "sugar_g",
        "zuccheri": "sugar_g",
        "fiber": "fiber_g",
        "fibre": "fiber_g",
        "sodium": "sodium_mg",
        "sodio": "sodium_mg",
    }
    normalized = str(key).strip().lower().replace(" ", "_").replace("-", "_")
    return alias_map.get(normalized, normalized)


def parse_ai_response(payload: Any) -> dict:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("AI payload must be a JSON object")

    ingredients = payload.get("ingredients", [])
    nutrition = payload.get("nutrition", {})
    product_name = payload.get("product_name") or payload.get("name")
    brand_name = payload.get("brand_name") or payload.get("brand")
    category = payload.get("category")
    product_type = payload.get("product_type") or payload.get("type")

    if not isinstance(ingredients, list):
        ingredients = []
    if not isinstance(nutrition, dict):
        nutrition = {}

    cleaned_ingredients: list[str] = []
    seen: set[str] = set()
    for item in ingredients:
        if isinstance(item, str):
            text = item.strip()
            if text:
                normalized = normalize_ingredient(text)
                if normalized == "unknown ingredient":
                    continue
                key = normalized.lower()
                if key not in seen:
                    seen.add(key)
                    cleaned_ingredients.append(normalized)

    cleaned_nutrition: dict[str, Any] = {}
    for key, value in nutrition.items():
        if value is None:
            continue
        normalized_key = _normalize_nutrition_keys(str(key))
        numeric_value = value
        if isinstance(value, str):
            text = value.strip().replace(",", ".")
            if text:
                try:
                    numeric_value = float(text)
                except ValueError:
                    continue
        if isinstance(numeric_value, (int, float)):
            cleaned_nutrition[normalized_key] = float(numeric_value)

    result: dict[str, Any] = {
        "ingredients": cleaned_ingredients,
        "nutrition": cleaned_nutrition,
    }

    if isinstance(product_name, str) and product_name.strip():
        result["product_name"] = product_name.strip()
    if isinstance(brand_name, str) and brand_name.strip():
        result["brand_name"] = brand_name.strip()
    if isinstance(category, str) and category.strip():
        result["category"] = category.strip().lower()
    if isinstance(product_type, str) and product_type.strip():
        result["product_type"] = product_type.strip().lower()

    return result


def _infer_product_metadata(raw_text: str) -> dict:
    cleaned = raw_text.replace("\r", "\n")
    lines = [re.sub(r"^\s*\d+[\.)\-]*\s*", "", line).strip() for line in cleaned.split("\n")]
    lines = [line for line in lines if line and not line.lower().startswith("ingredient") and not line.lower().startswith("nutrizione")]

    metadata = {
        "product_name": "",
        "brand_name": "",
        "category": "food",
        "product_type": "snack",
    }

    if not lines:
        return metadata

    def score_line(line: str) -> int:
        score = 0
        text = line.strip()
        if len(text) < 3:
            return -999
        lowered = text.lower()
        if re.search(r"\d{8,14}", text):
            return -999
        if re.search(r"\d+[.,]\d+", text):
            return -999
        if any(token in lowered for token in ["ingredient", "nutrition", "nutrizional", "valori nutrizionali", "calories", "kcal", "made in", "lot", "batch", "barcode", "ean", "gtin", "net weight", "weight", "www.", "www", "italy", "italia", "contains", "contains:", "of which", "di cui", "saturat", "saturi", "sodium", "sodio", "fiber", "fibre", "protein", "proteine", "carboidrati", "carbohydrate", "grassi", "zuccheri"]):
            return -999
        words = [w for w in re.split(r"\s+", text) if w]
        if len(words) == 1:
            # single-word titles (e.g. "Nutella") are valid but ranked lower than multi-word ones
            return -50
        score += len(words) * 8
        score += len(text) * 2
        if any(ch.isupper() for ch in text):
            score += 10
        if any(word[0].isupper() for word in words if word):
            score += 15
        return score

    candidates: list[tuple[int, str]] = []
    for line in lines:
        s = score_line(line)
        if s > -100:
            candidates.append((s, line.strip()))

    if candidates:
        scored_candidates = sorted(candidates, key=lambda item: (item[0], len(item[1])), reverse=True)
        product_candidate = scored_candidates[0][1].strip()
        product_lower = product_candidate.lower()

        if product_candidate and re.search(r"[,;]", product_candidate) and any(token in product_lower for token in ["farina", "zucchero", "latte", "cacao", "milk", "sugar", "wheat", "flour", "oil", "water", "salt", "ingredient", "grassi", "proteine", "carboidrati"]):
            product_candidate = ""

        if product_candidate:
            metadata["product_name"] = product_candidate

        brand_candidate = None
        for _, line in scored_candidates:
            candidate = line.strip()
            if not candidate or candidate.lower() == product_candidate.lower():
                continue
            lowered = candidate.lower()
            if re.search(r"\d{8,14}", candidate):
                continue
            if re.search(r"[,;]", candidate) and any(token in lowered for token in ["farina", "zucchero", "latte", "cacao", "milk", "sugar", "wheat", "flour", "oil", "water", "salt", "ingredient", "grassi", "proteine", "carboidrati"]):
                continue
            if any(token in lowered for token in ["ingredient", "nutrition", "made in", "via ", "street", "road", "address", "lot", "batch", "barcode", "ean", "gtin", "www.", "www", "contains", "calories", "kcal"]):
                continue
            if re.search(r"\b(via|street|road|avenue|through|address)\b", lowered):
                continue
            if len(candidate) <= 60 and len(re.split(r"\s+", candidate)) >= 2 and not re.search(r"\d", candidate):
                brand_candidate = candidate
                break

        if brand_candidate:
            metadata["brand_name"] = brand_candidate.strip()
        elif product_candidate:
            metadata["brand_name"] = product_candidate

    lowered_text = raw_text.lower()
    if any(term in lowered_text for term in ["water", "drink", "juice", "tea", "coffee", "cola", "milkshake", "soda"]):
        metadata["product_type"] = "beverage"
    elif any(term in lowered_text for term in ["shampoo", "soap", "cream", "lotion", "perfume", "cosmetic", "gel", "serum"]):
        metadata["product_type"] = "cosmetic"
    elif any(term in lowered_text for term in ["bread", "cracker", "cookie", "biscuit", "cake", "cereal", "toast"]):
        metadata["product_type"] = "bakery"
    elif any(term in lowered_text for term in ["yogurt", "milk", "cheese", "butter", "cream", "dairy"]):
        metadata["product_type"] = "dairy"

    return metadata


def _fallback_parse(raw_text: str) -> dict:
    cleaned = raw_text.replace("\r", "\n")
    lines = [line.strip() for line in cleaned.split("\n")]

    ingredients: list[str] = []
    nutrition: dict[str, Any] = {}
    in_nutrition_section = False
    in_ingredient_section = False

    def parse_nutrition_values(text: str) -> None:
        matches = re.findall(
            r"(?i)(energia|energy|calories?|kcal|proteins?|proteine|carbohydrates?|carboidrati|carbs|saturated\s*fats?|grassi\s*saturi|saturates?|saturi|fats?|grassi|sugars?|zuccheri|fibers?|fibre|sodium|sodio)\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:g|mg|kcal|kj)?",
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
            elif "satur" in key:
                nutrition["saturated_fat_g"] = float(value.replace(",", "."))
            elif "fat" in key or "grassi" in key:
                nutrition["fat_g"] = float(value.replace(",", "."))
            elif "sugar" in key or "zuccheri" in key:
                nutrition["sugar_g"] = float(value.replace(",", "."))
            elif "fiber" in key or "fibre" in key:
                nutrition["fiber_g"] = float(value.replace(",", "."))
            elif "sodium" in key or "sodio" in key:
                nutrition["sodium_mg"] = float(value.replace(",", "."))

    def add_candidates(raw_value: str) -> None:
        if not raw_value:
            return
        parts = [part.strip() for part in re.split(r"[,;\n]", raw_value)]
        for candidate in parts:
            candidate = re.sub(r"\s+", " ", candidate).strip()
            # strip trailing/parenthetical percentages and quantities (e.g. "Hazelnuts 13%") without dropping the ingredient
            candidate = re.sub(r"\(?\b[0-9]+(?:[.,][0-9]+)?\s*%\)?", "", candidate)
            candidate = re.sub(r"\(?\b[0-9]+(?:[.,][0-9]+)?\s*(?:g|mg|kg|ml|l)\b\)?", "", candidate, flags=re.IGNORECASE)
            candidate = re.sub(r"\s+", " ", candidate).strip(" -:")
            if not candidate:
                continue
            lowered = candidate.lower()
            if lowered in {"ingredients", "ingredienti", "nutrition", "nutrizione", "nutrition facts", "valori nutrizionali"}:
                continue
            if any(token in lowered for token in ["ingredient", "nutriz", "calorie", "kcal", "proteine", "grassi", "carboidrati", "sodio", "energia"]):
                continue
            if re.search(r"\d", candidate):
                continue
            if candidate.count(" ") == 0 and len(candidate) <= 3:
                continue
            if any(unit in lowered for unit in ["g ", "mg", "kcal", "ml", "%", "per 100"]):
                continue
            ingredients.append(candidate)

    inferred = _infer_product_metadata(raw_text)
    product_name = (inferred.get("product_name") or "").strip().lower()
    brand_name = (inferred.get("brand_name") or "").strip().lower()
    has_ingredient_label = any("ingredient" in (line or "").lower() for line in lines)

    for line in lines:
        lowered = line.lower().strip()
        if not lowered:
            continue

        if lowered == product_name or lowered == brand_name:
            continue

        if "nutrition" in lowered or "nutrizione" in lowered or "per 100" in lowered or re.search(r"\b(?:energia|calorie|proteine|grassi|carboidrati|zuccheri|sodio|fiber|fibre)\b", lowered):
            in_nutrition_section = True
            in_ingredient_section = False
            parse_nutrition_values(line)
            continue

        if in_nutrition_section:
            parse_nutrition_values(line)
            if any(keyword in lowered for keyword in ["kcal", "g", "mg", "%", "calorie", "proteine", "grassi", "carboidrati", "zuccheri", "sodio", "energia"]):
                continue
            if re.search(r"\d", lowered):
                continue

        if "ingredient" in lowered:
            in_ingredient_section = True
            remainder = line.split(":", 1)[1].strip() if ":" in line else ""
            add_candidates(remainder)
            continue

        if in_ingredient_section:
            add_candidates(line)
            continue

        if re.search(r"\d", lowered) and any(keyword in lowered for keyword in ["kcal", "g", "mg", "%"]):
            continue

        if re.search(r"\b(?:milk|sugar|wheat|flour|salt|oil|water|cocoa|rice|oat|corn|seed|grain|bean|fruit|nut|honey|butter|yeast)\b", lowered):
            add_candidates(line)
            continue

        if not has_ingredient_label:
            add_candidates(line)

    result = {"ingredients": ingredients, "nutrition": nutrition}
    if product_name:
        result["product_name"] = inferred["product_name"]
    if brand_name:
        result["brand_name"] = inferred["brand_name"]
    if inferred["category"]:
        result["category"] = inferred["category"]
    if inferred["product_type"]:
        result["product_type"] = inferred["product_type"]

    filtered_ingredients: list[str] = []
    seen: set[str] = set()
    for item in result.get("ingredients", []):
        candidate = str(item).strip()
        candidate_lower = candidate.lower()
        if not candidate_lower:
            continue
        if candidate_lower == product_name or candidate_lower == brand_name:
            continue
        if candidate_lower in {"ingredients", "ingredienti", "nutrition", "nutrizione", "nutrition facts", "valori nutrizionali"}:
            continue
        if candidate_lower in seen:
            continue
        seen.add(candidate_lower)
        filtered_ingredients.append(candidate)
    result["ingredients"] = filtered_ingredients
    return parse_ai_response(result)


def normalize_label_text_with_ai(raw_text: str, label_type: str) -> dict:
    api_key = _get_ai_key()
    if api_key and (api_key.startswith("AQ.") or api_key.startswith("AIza")):
        gemini_response = _call_gemini_api(raw_text, raw_text=raw_text)
        if gemini_response:
            return parse_ai_response(gemini_response)
        return _fallback_parse(raw_text)

    if not api_key or openai is None:
        return _fallback_parse(raw_text)

    client = openai.OpenAI(api_key=api_key)

    if label_type == "ingredients":
        prompt = """
        Extract the product metadata and ingredient list from the text below.
        Return valid JSON with keys: "product_name", "brand_name", "category", "product_type", and "ingredients".
        "product_name" and "brand_name" must be strings. "category" should be a single word like "food" or "beverage". "product_type" can be values like "snack", "drink", "cereal", etc.
        Ingredients must be an array of clean ingredient names in English. Ignore barcode, marketing text, and units.
        Text:
        """ + raw_text
    else:
        prompt = """
        Extract the product metadata and nutrition values from the text below.
        Return valid JSON with keys: "product_name", "brand_name", "category", "product_type", and "nutrition".
        "product_name" and "brand_name" must be strings. "category" should be a single word like "food" or "beverage". "product_type" can be values like "snack", "drink", "cereal", etc.
        "nutrition" must be an object containing ONLY numeric values for: energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg.
        Use English keys and keep values as numbers (not strings). If a value is missing, omit it rather than guessing.
        Text:
        """ + raw_text

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a food label OCR normalization assistant. Return only valid JSON that matches the requested schema."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        text={
            "format": {
                "type": "json_schema",
                "name": "food_label_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "nutrition": {
                            "type": "object",
                            "properties": {
                                "energy_kcal": {"type": "number"},
                                "protein_g": {"type": "number"},
                                "carbs_g": {"type": "number"},
                                "fat_g": {"type": "number"},
                                "sugar_g": {"type": "number"},
                                "saturated_fat_g": {"type": "number"},
                                "fiber_g": {"type": "number"},
                                "sodium_mg": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["ingredients", "nutrition"],
                    "additionalProperties": False,
                },
            }
        },
    )

    content = getattr(response, "output_text", None)
    if not content:
        raise RuntimeError("Empty AI response")

    return parse_ai_response(content)


def analyze_image_with_ai(image_url: str | None, raw_text: str = "") -> dict:
    if not image_url and not raw_text:
        return {"ingredients": [], "nutrition": {}}

    api_key = _get_ai_key()
    if api_key and (api_key.startswith("AQ.") or api_key.startswith("AIza")):
        prompt = (
            "Extract from the product image the ingredient list and the nutrition facts. "
            "Return valid JSON with keys 'ingredients' and 'nutrition'. "
            "Ingredients must be English names only. Nutrition must be numeric values for energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg."
        )
        gemini_response = _call_gemini_api(prompt, image_url=image_url, raw_text=raw_text)
        if gemini_response:
            return parse_ai_response(gemini_response)
        if raw_text:
            return normalize_photo_text(raw_text)
        return {"ingredients": [], "nutrition": {}}

    if not api_key or openai is None:
        if raw_text:
            return normalize_photo_text(raw_text)
        return {"ingredients": [], "nutrition": {}}

    client = openai.OpenAI(api_key=api_key)

    instruction = (
        "Extract from the product image the product metadata, ingredient list, and nutrition facts. "
        "Return valid JSON with keys: 'product_name', 'brand_name', 'category', 'product_type', 'ingredients', and 'nutrition'. "
        "'product_name' and 'brand_name' must be strings. 'category' should be a single word like 'food' or 'beverage'. 'product_type' can be values like 'snack', 'drink', or 'cereal'. "
        "Ingredients must be clean names in English, one per array item. "
        "Nutrition must be an object with numeric values for energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg. "
        "If a value is missing, omit it. Ignore barcode, logo, marketing text and unrelated text."
    )

    content: list[dict[str, Any]] = [{"type": "input_text", "text": instruction}]
    if image_url:
        content.append({"type": "input_image", "image_url": image_url})
    if raw_text and raw_text.strip():
        content.append({"type": "input_text", "text": "Additional OCR text for context:\n" + raw_text})

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "user", "content": content},
        ],
        temperature=0,
        text={
            "format": {
                "type": "json_schema",
                "name": "food_label_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "nutrition": {
                            "type": "object",
                            "properties": {
                                "energy_kcal": {"type": "number"},
                                "protein_g": {"type": "number"},
                                "carbs_g": {"type": "number"},
                                "fat_g": {"type": "number"},
                                "sugar_g": {"type": "number"},
                                "saturated_fat_g": {"type": "number"},
                                "fiber_g": {"type": "number"},
                                "sodium_mg": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["ingredients", "nutrition"],
                    "additionalProperties": False,
                },
            }
        },
    )

    content_text = getattr(response, "output_text", None)
    if not content_text:
        if raw_text:
            return normalize_photo_text(raw_text)
        raise RuntimeError("Empty AI response")

    return parse_ai_response(content_text)


def normalize_photo_text(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {"ingredients": [], "nutrition": {}}

    api_key = _get_ai_key()
    if api_key and (api_key.startswith("AQ.") or api_key.startswith("AIza")):
        gemini_response = _call_gemini_api(
            "Extract the ingredient list and nutrition facts from this product label. Return JSON with keys 'ingredients' and 'nutrition'. Ingredients in English only.",
            raw_text=raw_text,
        )
        if gemini_response:
            return parse_ai_response(gemini_response)
        return _fallback_parse(raw_text)

    if not api_key or openai is None:
        return _fallback_parse(raw_text)

    client = openai.OpenAI(api_key=api_key)
    prompt = """
    Extract from the full OCR text of the food product label below:
    1) the product metadata: product_name, brand_name, category, product_type
    2) the ingredient list, as a clean array of ingredient names in English
    3) the nutrition facts, as an object with numeric values for: energy_kcal, protein_g, carbs_g, fat_g, sugar_g, saturated_fat_g, fiber_g, sodium_mg

    Rules:
    - Ignore the barcode, marketing copy, logos, and everything that is not part of the ingredients or nutrition section.
    - Keep only real ingredient names, in English.
    - Remove duplicates and units.
    - If a nutrition value is missing, omit it.
    - Return valid JSON with keys: "product_name", "brand_name", "category", "product_type", "ingredients", and "nutrition".

    OCR text:
    """ + raw_text

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a food label OCR extraction assistant. Return only valid JSON that matches the requested schema."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        text={
            "format": {
                "type": "json_schema",
                "name": "food_label_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "nutrition": {
                            "type": "object",
                            "properties": {
                                "energy_kcal": {"type": "number"},
                                "protein_g": {"type": "number"},
                                "carbs_g": {"type": "number"},
                                "fat_g": {"type": "number"},
                                "sugar_g": {"type": "number"},
                                "saturated_fat_g": {"type": "number"},
                                "fiber_g": {"type": "number"},
                                "sodium_mg": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["ingredients", "nutrition"],
                    "additionalProperties": False,
                },
            }
        },
    )

    content = getattr(response, "output_text", None)
    if not content:
        raise RuntimeError("Empty AI response")

    return parse_ai_response(content)
