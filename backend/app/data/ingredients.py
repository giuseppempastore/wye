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
    "nuci": "nuts",
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


def normalize_ingredient(raw_text: str) -> str:
    value = raw_text.strip().lower()
    value = value.replace("/", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace("-", " ")
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
    return cleaned or "unknown ingredient"


def parse_ingredient_list(raw_text: str):
    if not raw_text:
        return []

    chunk = raw_text.replace(";", ",").replace("\n", ",").replace("\r", ",")
    parts = [part.strip() for part in chunk.split(",")]
    return [part for part in parts if part and part.lower() not in {"ingredienti", "ingredients"}]
