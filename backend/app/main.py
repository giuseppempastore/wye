from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.services.scoring import score_product
from app.db import get_connection
import psycopg2.extras

app = FastAPI(title="Wye MVP prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "static" / "index.html"


class AnalyzeRequest(BaseModel):
    product_name: str = "Demo product"
    ingredients: str
    language: str = "it"


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
            SELECT pi.raw_name, pi.canonical_name, i.risk_level, i.allergen_flag
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
