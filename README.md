# Wye MVP Prototype

This is a minimal MVP prototype for an ingredient risk and nutrition analysis app.

## What it does

- accepts a product name and ingredient list
- normalizes ingredient names from Italian and common aliases
- matches them against a starter catalog
- calculates a simple risk score and verdict
- exposes a minimal web interface for demo purposes

## Run locally

From the `backend` folder:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open:

- http://127.0.0.1:8000/
- POST http://127.0.0.1:8000/analyze

## Example payload

```json
{
  "product_name": "Prodotto demo",
  "ingredients": "sodio benzoato, acqua, sciroppo di glucosio, acido citrico, olio di palma, zucchero",
  "language": "it"
}
```

## Notes

This is intentionally lightweight and meant to be a foundation for a larger system.
The scoring and ingredient catalog are intentionally simple and should evolve with validated scientific sources.
