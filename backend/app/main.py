import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.services.scoring import score_product
from app.services.ai_normalizer import analyze_image_with_ai, normalize_photo_text
from app.barcodes import validate_product_barcode
from app.data.ingredients import normalize_ingredient, parse_ingredient_list
from app.db import get_connection
from app.routes.product_images import router as product_images_router
from app.routes.label_extractions import router as label_extractions_router
from app.routes.ingredient_mapping_reviews import router as ingredient_mapping_reviews_router
from app.routes.mobile_upload import router as mobile_upload_router
import psycopg2.extras
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

app = FastAPI(title="Wye MVP prototype")
app.include_router(product_images_router)
app.include_router(label_extractions_router)
app.include_router(ingredient_mapping_reviews_router)
app.include_router(mobile_upload_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "static" / "index.html"


class AnalyzeRequest(BaseModel):
    product_name: str = "Demo product"
    ingredients: str
    language: str = "it"


class PhotoNormalizationRequest(BaseModel):
    raw_text: str


class ImageAnalysisRequest(BaseModel):
    image_url: str | None = None
    raw_text: str = ""


class ProductCreateRequest(BaseModel):
    barcode: str
    brand_name: str = ""
    product_name: str
    category: str = "food"
    product_type: str = "snack"
    ingredients: str
    nutrition: dict | None = None
    source: str = "photo_submission"
    image_url: str | None = None
    ingredient_image_url: str | None = None
    nutrition_image_url: str | None = None


def _coerce_nutrition_values(nutrition: dict | None) -> dict:
    if not isinstance(nutrition, dict):
        return {}

    cleaned: dict[str, float | int | None] = {}
    allowed_keys = {
        'energy_kcal',
        'protein_g',
        'carbs_g',
        'sugar_g',
        'fat_g',
        'saturated_fat_g',
        'sodium_mg',
        'fiber_g',
    }

    for key, value in nutrition.items():
        if key not in allowed_keys:
            continue
        if value is None or str(value).strip() == '':
            continue
        try:
            parsed = float(str(value).replace(',', '.'))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f'Nutrition field {key} must be numeric')
        if parsed < 0:
            raise HTTPException(status_code=400, detail=f'Nutrition field {key} must not be negative')
        if key == 'energy_kcal' and parsed > 900:
            raise HTTPException(status_code=400, detail='Nutrition energy exceeds the physical per-100g limit')
        if key.endswith('_g') and parsed > 100:
            raise HTTPException(status_code=400, detail=f'Nutrition field {key} exceeds the per-100g limit')
        if key == 'sodium_mg' and parsed > 100000:
            raise HTTPException(status_code=400, detail='Nutrition sodium exceeds the per-100g limit')
        cleaned[key] = parsed

    return cleaned


def _unavailable_score_view() -> dict[str, Any]:
    component = {
        "evaluability_status": "not_computable",
        "score_value": None,
        "assessment_coverage_percent": None,
        "confidence_state": None,
        "missing_inputs": [],
        "uncertainties": [],
        "explanations": [],
        "disclosures": [],
    }
    return {
        "ingredient_goodness_percent": dict(component),
        "nutrition_goodness_percent": dict(component),
        "overall_score": {
            "availability": "deferred",
            "explanations": [{"code": "score_not_yet_computed", "context": {}}],
            "disclosures": [],
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML.read_text(encoding="utf-8")


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    result = score_product(payload.product_name, payload.ingredients, payload.language)
    return result


@app.post("/normalize-photo")
def normalize_photo(payload: PhotoNormalizationRequest):
    if not payload.raw_text or not payload.raw_text.strip():
        return {"ingredients": [], "nutrition": {}}
    return normalize_photo_text(payload.raw_text)


@app.post("/analyze-image")
def analyze_image(payload: ImageAnalysisRequest):
    if not payload.image_url and not payload.raw_text.strip():
        return {"ingredients": [], "nutrition": {}}
    return analyze_image_with_ai(payload.image_url, payload.raw_text)


@app.post("/products")
def create_product(payload: ProductCreateRequest):
    barcode_validation = validate_product_barcode(payload.barcode)
    logger.info("barcode_validation %s", barcode_validation.safe_log_fields)
    if not barcode_validation.valid:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_product_barcode", "reason": barcode_validation.reason},
        )
    barcode = barcode_validation.value
    product_name = (payload.product_name or '').strip()
    brand_name = (payload.brand_name or '').strip()
    if not barcode or not product_name or not brand_name:
        raise HTTPException(status_code=400, detail='barcode, product_name and brand_name are required')
    category = (payload.category or '').strip().lower()
    if category not in {'food', 'foods'}:
        raise HTTPException(status_code=422, detail={"code": "unsupported_product_category"})
    if (payload.product_type or '').strip().lower() == 'cosmetic':
        raise HTTPException(status_code=422, detail={"code": "unsupported_product_type"})
    if any((payload.image_url, payload.ingredient_image_url, payload.nutrition_image_url)):
        raise HTTPException(
            status_code=422,
            detail={"code": "embedded_image_payload_forbidden"},
        )

    normalized_ingredients = parse_ingredient_list(payload.ingredients)
    ingredient_pairs = [
        (item, normalize_ingredient(item)) for item in normalized_ingredients
    ]
    nutrition = _coerce_nutrition_values(payload.nutrition)
    image_url = (payload.image_url or '').strip() or None
    ingredient_image_url = (payload.ingredient_image_url or '').strip() or None
    nutrition_image_url = (payload.nutrition_image_url or '').strip() or None

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name IN ('image_url', 'ingredient_image_url', 'nutrition_image_url')
            """
        )
        available_product_columns = {row['column_name'] for row in cur.fetchall()}

        cur.execute(
            """
            SELECT * FROM products WHERE barcode = %s LIMIT 1
            """,
            (barcode,),
        )
        product = cur.fetchone()

        if product:
            raise HTTPException(status_code=409, detail='A product with this barcode already exists')

        if not product:
            insert_columns = [
                'barcode', 'brand_name', 'product_name', 'category', 'product_type', 'source', 'verified', 'status'
            ]
            insert_values: list[Any] = [
                barcode,
                payload.brand_name or 'Unknown Brand',
                product_name,
                category,
                payload.product_type or 'snack',
                payload.source or 'photo_submission',
                False,
                'needs_review',
            ]

            if 'image_url' in available_product_columns:
                insert_columns.append('image_url')
                insert_values.append(image_url)
            if 'ingredient_image_url' in available_product_columns:
                insert_columns.append('ingredient_image_url')
                insert_values.append(ingredient_image_url)
            if 'nutrition_image_url' in available_product_columns:
                insert_columns.append('nutrition_image_url')
                insert_values.append(nutrition_image_url)

            placeholders = ', '.join(['%s'] * len(insert_values))
            column_sql = ', '.join(insert_columns)
            cur.execute(
                f"""
                INSERT INTO products ({column_sql})
                VALUES ({placeholders})
                RETURNING *
                """,
                tuple(insert_values),
            )
            product = cur.fetchone()

        if product:
            update_values: list[Any] = []
            update_fields: list[str] = []
            if image_url and 'image_url' in available_product_columns and product.get('image_url') is None:
                update_fields.append('image_url = %s')
                update_values.append(image_url)
            if ingredient_image_url and 'ingredient_image_url' in available_product_columns and product.get('ingredient_image_url') is None:
                update_fields.append('ingredient_image_url = %s')
                update_values.append(ingredient_image_url)
            if nutrition_image_url and 'nutrition_image_url' in available_product_columns and product.get('nutrition_image_url') is None:
                update_fields.append('nutrition_image_url = %s')
                update_values.append(nutrition_image_url)
            if update_fields:
                update_fields.append('updated_at = NOW()')
                cur.execute(
                    f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s",
                    (*update_values, product['id']),
                )
                if image_url and 'image_url' in available_product_columns:
                    product['image_url'] = image_url
                if ingredient_image_url and 'ingredient_image_url' in available_product_columns:
                    product['ingredient_image_url'] = ingredient_image_url
                if nutrition_image_url and 'nutrition_image_url' in available_product_columns:
                    product['nutrition_image_url'] = nutrition_image_url

        if not product:
            raise HTTPException(status_code=500, detail='Product could not be created')

        cur.execute("DELETE FROM product_ingredients WHERE product_id = %s", (product['id'],))

        if normalized_ingredients:
            cur.execute(
                """
                INSERT INTO product_label_documents(
                    product_id, raw_text, source_type, document_type
                )
                VALUES (%s, %s, 'manual_input', 'other')
                """,
                (product['id'], payload.ingredients),
            )

        for pos, (raw_ingredient, ingredient) in enumerate(ingredient_pairs, start=1):
            if not ingredient or ingredient == 'unknown ingredient':
                continue
            cur.execute(
                """
                SELECT i.id
                FROM ingredients i
                WHERE lower(i.canonical_name) = lower(%s) AND i.status = 'active'
                UNION ALL
                SELECT i.id
                FROM ingredient_aliases a
                JOIN ingredients i ON i.id = a.ingredient_id
                WHERE a.normalized_alias = %s
                  AND a.mapping_status = 'accepted'
                  AND i.status = 'active'
                LIMIT 1
                """,
                (ingredient, ingredient),
            )
            ingredient_row = cur.fetchone()

            cur.execute(
                """
                INSERT INTO product_ingredients (
                    product_id, ingredient_id, raw_name, canonical_name, position_in_list,
                    confidence, allergen_flag, risky_flag, is_unknown, manual_override,
                    normalized_text, mapping_method, mapping_status, mapping_provenance
                )
                VALUES (%s, %s, %s, %s, %s, NULL, FALSE, FALSE, %s, FALSE,
                        %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    product['id'],
                    ingredient_row['id'] if ingredient_row else None,
                    raw_ingredient,
                    ingredient if ingredient_row else None,
                    pos,
                    ingredient_row is None,
                    ingredient,
                    'deterministic_alias' if ingredient_row else 'unmapped',
                    'accepted' if ingredient_row else 'needs_review',
                    Json({
                        'source_type': 'manual_input',
                        'user_confirmed': True,
                        'authoritative': False,
                    }),
                ),
            )
            product_ingredient = cur.fetchone()
            if not ingredient_row:
                cur.execute(
                    """
                    INSERT INTO ingredient_mapping_reviews(
                        product_ingredient_id, raw_text, normalized_text,
                        review_status, requested_by_method, review_provenance
                    ) VALUES (%s, %s, %s, 'pending', 'manual', %s)
                    """,
                    (
                        product_ingredient['id'],
                        raw_ingredient,
                        ingredient,
                        Json({'source': 'product_submission', 'authoritative': False}),
                    ),
                )

        nutrition_fields = {
            'energy_kcal': nutrition.get('energy_kcal'),
            'protein_g': nutrition.get('protein_g'),
            'carbs_g': nutrition.get('carbs_g'),
            'sugar_g': nutrition.get('sugar_g'),
            'fat_g': nutrition.get('fat_g'),
            'saturated_fat_g': nutrition.get('saturated_fat_g'),
            'sodium_mg': nutrition.get('sodium_mg'),
            'fiber_g': nutrition.get('fiber_g'),
        }

        has_nutrition = any(v is not None and str(v).strip() != '' for v in nutrition_fields.values())
        if has_nutrition:
            cur.execute(
                """
                DELETE FROM nutrition_facts WHERE product_id = %s
                """,
                (product['id'],),
            )
            cur.execute(
                """
                INSERT INTO nutrition_facts (
                    product_id, serving_size, energy_kcal, protein_g, carbs_g, sugar_g,
                    fat_g, saturated_fat_g, sodium_mg, fiber_g, source, declared_by_manufacturer, verified, raw_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'photo_submission', TRUE, FALSE, %s)
                """,
                (
                    product['id'],
                    '100g',
                    nutrition_fields['energy_kcal'],
                    nutrition_fields['protein_g'],
                    nutrition_fields['carbs_g'],
                    nutrition_fields['sugar_g'],
                    nutrition_fields['fat_g'],
                    nutrition_fields['saturated_fat_g'],
                    nutrition_fields['sodium_mg'],
                    nutrition_fields['fiber_g'],
                    str(nutrition),
                ),
            )

        cur.execute(
            """
            INSERT INTO product_reviews(product_id, review_status, source_type, reason)
            VALUES (%s, 'pending', 'manual_input', 'user_product_submission')
            """,
            (product['id'],),
        )

        cur.execute("SELECT * FROM products WHERE id = %s", (product['id'],))
        saved_product = cur.fetchone()
        conn.commit()
        cur.close()
        return {
            "message": "product created",
            "product": saved_product,
            "score_view": _unavailable_score_view(),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/product/{barcode}")
def get_product(barcode: str):
    """Return product data plus canonical image reference and score state."""
    barcode_validation = validate_product_barcode(barcode)
    logger.info("barcode_validation %s", barcode_validation.safe_log_fields)
    if not barcode_validation.valid:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_product_barcode", "reason": barcode_validation.reason},
        )
    barcode = barcode_validation.value
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM products WHERE barcode = %s", (barcode,))
        product = cur.fetchone()
        if not product:
            return {"error": "not_found", "barcode": barcode}

        cur.execute(
            """
            SELECT pi.raw_name, pi.canonical_name, pi.mapping_status,
                   COALESCE(i.allergen_flag, FALSE) AS allergen_flag,
                   i.canonical_name as ingredient_name
            FROM product_ingredients pi
            LEFT JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.product_id = %s
            ORDER BY pi.position_in_list
            """, (product['id'],)
        )
        ingredients = cur.fetchall()

        cur.execute(
            """
            SELECT serving_size, energy_kcal, protein_g, carbs_g, sugar_g,
                   fat_g, saturated_fat_g, sodium_mg, fiber_g
            FROM nutrition_facts
            WHERE product_id = %s
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (product['id'],),
        )
        nutrition_facts = cur.fetchone()

        cur.execute(
            """
            SELECT id, mime_type
            FROM product_images
            WHERE product_id = %s
              AND image_type = 'product_front'
              AND status = 'active'
              AND is_current = TRUE
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (product['id'],),
        )
        product_image = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    return {
        "product": product,
        "product_image": product_image,
        "score_view": _unavailable_score_view(),
        "ingredients": ingredients,
        "nutrition_facts": nutrition_facts,
    }
