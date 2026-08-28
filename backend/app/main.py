from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.services.scoring import score_product
from app.services.ai_normalizer import analyze_image_with_ai, normalize_photo_text
from app.data.ingredients import normalize_barcode, normalize_ingredient, parse_ingredient_list
from app.db import get_connection
from app.routes.product_images import router as product_images_router
from app.routes.label_extractions import router as label_extractions_router
import psycopg2.extras

app = FastAPI(title="Wye MVP prototype")
app.include_router(product_images_router)
app.include_router(label_extractions_router)

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
            cleaned[key] = float(str(value).replace(',', '.'))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f'Nutrition field {key} must be numeric')

    required_keys = ['energy_kcal', 'protein_g', 'carbs_g', 'fat_g']
    missing = [key for key in required_keys if key not in cleaned]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f'Missing required nutrition values: {", ".join(missing)}',
        )

    return cleaned


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
    barcode = (payload.barcode or '').strip()
    product_name = (payload.product_name or '').strip()
    brand_name = (payload.brand_name or '').strip()
    if not barcode:
        derived_barcode = normalize_barcode(payload.product_name or payload.ingredients or '')
        if derived_barcode:
            barcode = derived_barcode
    if not barcode or not product_name or not brand_name:
        raise HTTPException(status_code=400, detail='barcode, product_name and brand_name are required')

    normalized_ingredients = parse_ingredient_list(payload.ingredients)
    normalized_ingredient_names = [normalize_ingredient(item) for item in normalized_ingredients]
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
                payload.category or 'food',
                payload.product_type or 'snack',
                payload.source or 'photo_submission',
                True,
                'active',
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

        for pos, ingredient in enumerate(normalized_ingredient_names, start=1):
            if not ingredient or ingredient == 'unknown ingredient':
                continue
            cur.execute(
                """
                SELECT id FROM ingredients WHERE canonical_name = %s LIMIT 1
                """,
                (ingredient,),
            )
            ingredient_row = cur.fetchone()
            if not ingredient_row:
                cur.execute(
                    """
                    INSERT INTO ingredients (canonical_name, ingredient_group, risk_level, allergen_flag, evidence_level, common_name, status)
                    VALUES (%s, 'unknown', 'moderate', FALSE, 1, %s, 'active')
                    RETURNING id
                    """,
                    (ingredient, ingredient),
                )
                ingredient_row = cur.fetchone()
            if not ingredient_row:
                continue

            cur.execute(
                """
                INSERT INTO product_ingredients (
                    product_id, ingredient_id, raw_name, canonical_name, position_in_list,
                    confidence, allergen_flag, risky_flag, is_unknown, manual_override
                )
                VALUES (%s, %s, %s, %s, %s, %s, FALSE, FALSE, FALSE, TRUE)
                """,
                (
                    product['id'],
                    ingredient_row['id'],
                    ingredient,
                    ingredient,
                    pos,
                    0.8,
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'photo_submission', TRUE, TRUE, %s)
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
            SELECT * FROM product_scores WHERE product_id = %s ORDER BY generated_at DESC LIMIT 1
            """,
            (product['id'],),
        )
        score = cur.fetchone()
        if not score:
            cur.execute(
                """
                INSERT INTO product_scores (
                    product_id, ingredient_score, nutrition_score, final_score, score_band,
                    ingredient_risk_summary, nutrition_summary, final_summary, calculation_version
                )
                VALUES (%s, 50.00, 80.00, 65.00, 'moderate', 'Photo-based entry created', 'Nutrition captured from image', 'Newly added product from photo submission', 'photo_submission_v1')
                """,
                (product['id'],),
            )

        cur.execute("SELECT * FROM products WHERE id = %s", (product['id'],))
        saved_product = cur.fetchone()
        conn.commit()
        cur.close()
        return {"message": "product created", "product": saved_product}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/product/{barcode}")
def get_product(barcode: str):
    """Return product, latest score and mapped ingredients for a barcode."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM products WHERE barcode = %s", (barcode,))
        product = cur.fetchone()
        if not product:
            return {"error": "not_found", "barcode": barcode}

        cur.execute("SELECT * FROM product_scores WHERE product_id = %s ORDER BY generated_at DESC LIMIT 1", (product['id'],))
        score = cur.fetchone()

        cur.execute(
            """
            SELECT pi.raw_name, pi.canonical_name, i.risk_level, i.allergen_flag, i.canonical_name as ingredient_name
            FROM product_ingredients pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.product_id = %s
            ORDER BY pi.position_in_list
            """, (product['id'],)
        )
        ingredients = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return {"product": product, "score": score, "ingredients": ingredients}
