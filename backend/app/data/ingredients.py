import re

# Configurabile: i pesi possono essere regolati in futuro senza toccare la logica.
SOURCE_AUTHORITY_WEIGHTS = {
    "efsa": 1.00,
    "who": 0.98,
    "fda": 0.95,
    "jecfa": 0.94,
    "iarc": 0.97,
    "ema": 0.92,
    "echa": 0.92,
    "pubmed": 0.80,
    "cochrane": 0.85,
    "cosing": 0.88,
    "sccs": 0.89,
    "cir": 0.85,
    "usda": 0.76,
    "generic": 0.45,
    "unknown": 0.10,
}

CRITICAL_HARMFUL_CATALOG = {
    "ethanol",
    "alcohol",
    "nicotine",
    "formaldehyde",
    "benzene",
    "acrolein",
    "phthalate",
    "phthalates",
    "paraben",
    "parabens",
    "lead",
    "mercury",
    "arsenic",
    "cadmium",
    "cancerogenic solvent",
    "toluene",
    "xylene",
}

SCORE_COLOR_RULES = [
    {"min": 0, "max": 19, "label": "rischio alto", "color": "#ef4444", "text_color": "#ffffff"},
    {"min": 20, "max": 39, "label": "rischio moderato", "color": "#f97316", "text_color": "#ffffff"},
    {"min": 40, "max": 59, "label": "basso rischio", "color": "#facc15", "text_color": "#ffffff"},
    {"min": 60, "max": 69, "label": "sufficiente", "color": "#2f7d32", "text_color": "#ffffff"},
    {"min": 70, "max": 79, "label": "buono", "color": "#1f7a3d", "text_color": "#ffffff"},
    {"min": 80, "max": 89, "label": "ottimo", "color": "#2f9e44", "text_color": "#ffffff"},
    {"min": 90, "max": 100, "label": "eccellente", "color": "#22c55e", "text_color": "#ffffff"},
]

TRANSLATIONS = {
    "sodio benzoato": "sodium benzoate",
    "benzoato di sodio": "sodium benzoate",
    "aspartame": "aspartame",
    "acesulfame k": "acesulfame potassium",
    "potassio acesulfame": "acesulfame potassium",
    "acido citrico": "citric acid",
    "e330": "citric acid",
    "sale": "sodium chloride",
    "sodio": "sodium chloride",
    "zucchero": "sugar",
    "sciroppo di glucosio": "glucose syrup",
    "glucosio": "glucose",
    "olio di palma": "palm oil",
    "palma": "palm oil",
    "acqua": "water",
    "farina di grano": "wheat flour",
    "farina integrale": "whole wheat flour",
    "olio di girasole": "sunflower oil",
    "maltodestrine": "maltodextrin",
    "lattosio": "lactose",
    "proteine del siero del latte": "whey protein",
    "amido di mais": "corn starch",
    "acido lattico": "lactic acid",
    "aroma naturale": "natural flavor",
    "aromi naturali": "natural flavor",
    "sorbitolo": "sorbitol",
    "fruttosio": "fructose",
    "olio di colza": "canola oil",
    "bicarbonato di sodio": "sodium bicarbonate",
    "ammonio bicarbonato": "ammonium bicarbonate",
    "noci": "nuts",
    "latte intero": "whole milk",
    "latte scremato": "skim milk",
    "proteina del latte": "milk protein",
    "cacao in polvere": "cocoa powder",
    "farina di avena": "oat flour",
    "olio extra vergine di oliva": "extra virgin olive oil",
    "olio di oliva": "olive oil",
    "xanthan gum": "xanthan gum",
    "gomma xantana": "xanthan gum",
    "alcool": "ethanol",
    "alcol": "ethanol",
    "etanolo": "ethanol",
    "nicotina": "nicotine",
    "tabacco": "nicotine",
    "formaldeide": "formaldehyde",
    "parabeni": "parabens",
    "ftalati": "phthalates",
    "latte": "milk",
    "cacao": "cocoa",
    "cacao powder": "cocoa powder",
    "cacao in polvere": "cocoa powder",
    "grano": "wheat",
    "farina di grano": "wheat flour",
    "farina": "flour",
    "olio": "oil",
    "benzene": "benzene",
    "benzeno": "benzene",
}

CATALOG = {
    "sodium benzoate": {
        "risk_level": "moderate",
        "risk_score": 18,
        "category": "preservative",
        "evidence": ["EFSA guidance on food additives", "WHO food additives overview"]
    },
    "aspartame": {
        "risk_level": "moderate",
        "risk_score": 16,
        "category": "sweetener",
        "evidence": ["EFSA sweeteners assessment", "WHO artificial sweeteners review"]
    },
    "acesulfame potassium": {
        "risk_level": "moderate",
        "risk_score": 14,
        "category": "sweetener",
        "evidence": ["EFSA sweeteners assessment"]
    },
    "citric acid": {
        "risk_level": "low",
        "risk_score": 4,
        "category": "acidifier",
        "evidence": ["EFSA food additive database"]
    },
    "sodium chloride": {
        "risk_level": "moderate",
        "risk_score": 12,
        "category": "salt",
        "evidence": ["WHO sodium intake guidance", "EFSA sodium overview"]
    },
    "sugar": {
        "risk_level": "moderate",
        "risk_score": 20,
        "category": "sweetener",
        "evidence": ["WHO sugar intake guidelines", "USDA food guidance"]
    },
    "glucose syrup": {
        "risk_level": "moderate",
        "risk_score": 14,
        "category": "sweetener",
        "evidence": ["WHO sugar intake guidelines"]
    },
    "palm oil": {
        "risk_level": "moderate",
        "risk_score": 15,
        "category": "fat",
        "evidence": ["WHO saturated fat guidance"]
    },
    "water": {
        "risk_level": "low",
        "risk_score": 0,
        "category": "base",
        "evidence": []
    },
    "wheat flour": {
        "risk_level": "low",
        "risk_score": 4,
        "category": "grain",
        "evidence": ["USDA grain composition database"]
    },
    "whole wheat flour": {
        "risk_level": "low",
        "risk_score": 2,
        "category": "grain",
        "evidence": ["USDA grain composition database"]
    },
    "sunflower oil": {
        "risk_level": "low",
        "risk_score": 5,
        "category": "fat",
        "evidence": ["USDA nutrition database"]
    },
    "maltodextrin": {
        "risk_level": "moderate",
        "risk_score": 12,
        "category": "starch",
        "evidence": ["WHO and nutrition reviews"]
    },
    "lactose": {
        "risk_level": "low",
        "risk_score": 6,
        "category": "milk sugar",
        "evidence": ["USDA milk nutrition database"]
    },
    "whey protein": {
        "risk_level": "low",
        "risk_score": 2,
        "category": "protein",
        "evidence": ["USDA protein database"]
    },
    "corn starch": {
        "risk_level": "low",
        "risk_score": 4,
        "category": "starch",
        "evidence": ["USDA starch database"]
    },
    "lactic acid": {
        "risk_level": "low",
        "risk_score": 4,
        "category": "acidifier",
        "evidence": ["EFSA food additive database"]
    },
    "natural flavor": {
        "risk_level": "low",
        "risk_score": 5,
        "category": "flavor",
        "evidence": ["FDA flavor guidance"]
    },
    "sorbitol": {
        "risk_level": "low",
        "risk_score": 7,
        "category": "sweetener",
        "evidence": ["EFSA sweeteners assessment"]
    },
    "fructose": {
        "risk_level": "moderate",
        "risk_score": 10,
        "category": "sweetener",
        "evidence": ["WHO sugar intake guidance"]
    },
    "olive oil": {
        "risk_level": "low",
        "risk_score": 2,
        "category": "fat",
        "evidence": ["WHO dietary fat guidance"]
    },
    "extra virgin olive oil": {
        "risk_level": "low",
        "risk_score": 2,
        "category": "fat",
        "evidence": ["WHO dietary fat guidance"]
    },
    "xanthan gum": {
        "risk_level": "low",
        "risk_score": 3,
        "category": "stabilizer",
        "evidence": ["FDA food additive database"]
    },
    "canola oil": {
        "risk_level": "low",
        "risk_score": 3,
        "category": "fat",
        "evidence": ["USDA nutrition database"]
    },
    "ethanol": {
        "risk_level": "high",
        "risk_score": 100,
        "category": "alcohol",
        "evidence": ["WHO alcohol health effects", "EFSA alcohol guidelines"]
    },
    "nicotine": {
        "risk_level": "high",
        "risk_score": 100,
        "category": "nicotine",
        "evidence": ["WHO tobacco and nicotine health effects"]
    },
    "formaldehyde": {
        "risk_level": "high",
        "risk_score": 100,
        "category": "cosmetic ingredient",
        "evidence": ["IARC formaldehyde classification", "ECHA hazard profile"]
    },
    "parabens": {
        "risk_level": "high",
        "risk_score": 100,
        "category": "cosmetic ingredient",
        "evidence": ["ECHA and cosmetic review"]
    },
    "phthalates": {
        "risk_level": "high",
        "risk_score": 100,
        "category": "cosmetic ingredient",
        "evidence": ["ECHA chemical hazard assessments"]
    },
}


def normalize_barcode(raw_text: str) -> str | None:
    if not raw_text:
        return None

    digits_only = re.sub(r"\D+", " ", raw_text)
    candidates = re.findall(r"\b\d{8,14}\b", digits_only)
    if not candidates:
        return None

    cleaned = [candidate for candidate in candidates if candidate.isdigit()]
    if not cleaned:
        return None

    best = max(cleaned, key=lambda value: (len(value), value))
    if len(best) == 14 and best.startswith("0"):
        best = best[1:]
    if len(best) >= 13:
        return best[:13]
    return best


def normalize_ingredient(raw_text: str) -> str:
    value = (raw_text or '').strip().lower()
    for wrong, right in {"0": "o", "1": "i", "5": "s", "8": "b"}.items():
        value = value.replace(wrong, right)
    value = value.replace("/", " ")
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.strip()

    if not value:
        return "unknown ingredient"

    if value in TRANSLATIONS:
        return TRANSLATIONS[value]

    for alias, canonical in TRANSLATIONS.items():
        if alias in value:
            return canonical

    cleaned = re.sub(r"[^a-z0-9\s]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for wrong, right in {"0": "o", "1": "i", "5": "s", "8": "b"}.items():
        cleaned = cleaned.replace(wrong, right)

    if cleaned in {"milk", "water", "sugar", "wheat flour", "cocoa powder", "salt", "oil"}:
        return cleaned

    return cleaned or "unknown ingredient"


def parse_ingredient_list(raw_text: str):
    if not raw_text:
        return []

    chunk = raw_text.replace(";", ",").replace("\n", ",").replace("\r", ",")
    parts = [part.strip() for part in chunk.split(",")]
    cleaned = []
    noise_words = {
        "ingredienti", "ingredients", "ingredient list", "lista ingredienti", "ingredient",
        "dichiarazione nutrizionale", "nutrizione", "confezione", "biscotti", "sostenibile",
        "specifica", "consun", "allergeni", "dichiarazione", "c r a", "cra", "cara"
    }

    for part in parts:
        if not part:
            continue
        normalized = re.sub(r"^\s*\d+[\.)\-]*\s*", "", part)
        normalized = re.sub(r"^\s*[-•*]\s*", "", normalized)
        normalized = re.sub(r"\s*[:\-]\s*", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized:
            continue

        lowered = normalized.lower()
        for wrong, right in {"0": "o", "1": "i", "5": "s", "8": "b"}.items():
            lowered = lowered.replace(wrong, right)

        if lowered in noise_words:
            continue
        if any(token in lowered for token in ["ingredient", "nutriz", "biscotti", "confezione", "dichiarazione", "allergen"]):
            continue
        if any(word in lowered for word in ["sosteni", "specifica", "consun", "cultivazione", "icooki", "cocol", "l e c e s"]):
            continue
        if re.search(r"\d", normalized):
            continue
        single_tokens = normalized.split()
        if len(single_tokens) == 1:
            token = single_tokens[0]
            if len(token) <= 3 and token.lower() not in {"oil", "tea", "egg", "jam"}:
                continue
        cleaned.append(normalized)

    unique = []
    seen = set()
    for item in cleaned:
        key = item.lower()
        for wrong, right in {"0": "o", "1": "i", "5": "s", "8": "b"}.items():
            key = key.replace(wrong, right)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique
