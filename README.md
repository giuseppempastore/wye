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

## PostgreSQL + seed data

The project uses PostgreSQL for the canonical catalog.

### Database setup

The database must be created as `wye` and the schema loaded from:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "CREATE DATABASE wye;"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d wye -f "C:\Projects\wye\postgres\01_wye_schema.sql"
```

### Seed initial data

Seed files are stored in `postgres/seeds/` and can be run with:

```powershell
python .\backend\scripts\seed_db.py
```

This script reads PostgreSQL credentials from environment variables (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) or from `postgres/user_postgres.txt` if env vars are not set.

### Start the backend

From the repo root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or from the `backend` directory:

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Useful endpoints

- `GET /health`
- `GET /product/{barcode}`
- `POST /analyze`

This database layer is intentionally minimal: it connects to PostgreSQL and exposes product, score, and ingredient data for the first production-ready MVP iteration.

---
