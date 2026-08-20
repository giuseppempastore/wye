from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.services.scoring import score_product

app = FastAPI(title="Wye MVP prototype")

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
