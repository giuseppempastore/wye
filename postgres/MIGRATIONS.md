# Wye PostgreSQL migrations

Alembic is the mechanism for schema changes from revision
`0001_initial_schema` onward. `postgres/01_wye_schema.sql` remains a bootstrap
reference and is kept aligned with additive columns introduced for new local
databases; existing databases must still be upgraded with Alembic.

## New database

From `backend`, install dependencies and run against an empty database selected by `PGDATABASE`:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
```

The environment uses `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and `PGDATABASE`, with the existing local fallback to `postgres/user_postgres.txt`.

## Existing pre-Alembic database

Do not run `upgrade head`. First perform the read-only validation:

```powershell
python scripts/baseline_existing_db.py --dry-run
```

It checks all baseline tables, columns, indexes, and any existing Alembic revision. A mismatch exits before writing anything.

If validation succeeds, adopt the database:

```powershell
python scripts/baseline_existing_db.py
```

This runs `alembic stamp 0001_initial_schema`: only the Alembic version record is written; no Wye rows, seeds, or application behaviour are changed.

## Phase 9.3A head

`0023_phase9_photo_first_acquisition` adds nullable `nutrition_facts.salt_g`
with a 0–100 declared-basis check. Salt remains distinct from sodium. Downgrade
is fail-safe and refuses to drop the column while any salt value is present.

`0024_phase9_on_device_ocr_origin` permits the explicit `on_device_ocr`
origin on label documents. This distinguishes text recognized locally on the
phone from manually typed text without treating either source as verified.
Downgrade refuses to erase that distinction while such documents exist.

`0027_nutrition_energy_kj` aggiunge `nutrition_facts.energy_kj` con limite
0–4000 e mantiene l'energia dichiarata in kJ separata dalle kcal. Il downgrade
rimuove soltanto questa colonna.

