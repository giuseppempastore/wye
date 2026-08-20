from app.data.ingredients import (
    CATALOG,
    CRITICAL_HARMFUL_CATALOG,
    SCORE_COLOR_RULES,
    SOURCE_AUTHORITY_WEIGHTS,
    normalize_ingredient,
    parse_ingredient_list,
)


def get_score_band(score: int):
    for band in SCORE_COLOR_RULES:
        if band["min"] <= score <= band["max"]:
            return band
    return {"min": 0, "max": 100, "label": "non classificato", "color": "#9ca3af", "text_color": "#ffffff"}


def get_score_color(score: int, forced_zero: bool = False):
    if forced_zero:
        return {"label": "critico", "color": "#dc2626", "text_color": "#ffffff"}
    return get_score_band(score)


def weighted_risk_penalty(item):
    source_weight = 0.5
    evidence_count = max(1, len(item.get("evidence", [])))
    score = item.get("risk_score", 0)
    return round(score * source_weight / evidence_count, 2)


def score_product(product_name: str, ingredient_text: str, language: str = "it") -> dict:
    ingredients = parse_ingredient_list(ingredient_text)
    analyzed = []
    total_risk = 0
    warnings = []
    forced_zero = False

    for raw in ingredients:
        canonical = normalize_ingredient(raw)
        metadata = CATALOG.get(canonical, {
            "risk_level": "unknown",
            "risk_score": 8,
            "category": "unknown",
            "evidence": ["No catalog match"]
        })

        item = {
            "raw": raw,
            "canonical": canonical,
            "risk_level": metadata["risk_level"],
            "risk_score": metadata["risk_score"],
            "category": metadata["category"],
            "evidence": metadata["evidence"],
            "source_weight": SOURCE_AUTHORITY_WEIGHTS.get("generic", 0.45),
        }

        if canonical in CRITICAL_HARMFUL_CATALOG or canonical.lower() in CRITICAL_HARMFUL_CATALOG:
            forced_zero = True
            item["risk_level"] = "high"
            item["risk_score"] = 100
            warnings.append(f"{canonical} is classified as a critical harmful ingredient")

        analyzed.append(item)
        total_risk += weighted_risk_penalty(item)

        if item["risk_level"] in {"moderate", "high"}:
            warnings.append(f"{canonical} is marked as {item['risk_level']} risk")

    score = 100 - total_risk
    score = max(0, min(100, round(score)))

    if forced_zero:
        score = 0
        verdict = "Critical hazard"
    elif score >= 90:
        verdict = "Excellent"
    elif score >= 80:
        verdict = "Very good"
    elif score >= 70:
        verdict = "Good"
    elif score >= 60:
        verdict = "Fair"
    elif score >= 40:
        verdict = "Low risk"
    elif score >= 20:
        verdict = "Moderate risk"
    else:
        verdict = "High risk"

    color_info = get_score_color(score, forced_zero)

    return {
        "product_name": product_name or "Unnamed product",
        "language": language,
        "score": score,
        "verdict": verdict,
        "score_label": color_info["label"],
        "score_color": color_info["color"],
        "score_text_color": color_info["text_color"],
        "ingredients_count": len(analyzed),
        "warnings": warnings,
        "forced_zero": forced_zero,
        "ingredients": analyzed,
        "summary": {
            "total_risk": round(total_risk, 2),
            "risk_breakdown": {
                "low": sum(1 for i in analyzed if i["risk_level"] == "low"),
                "moderate": sum(1 for i in analyzed if i["risk_level"] == "moderate"),
                "high": sum(1 for i in analyzed if i["risk_level"] == "high"),
                "unknown": sum(1 for i in analyzed if i["risk_level"] == "unknown"),
            }
        }
    }
