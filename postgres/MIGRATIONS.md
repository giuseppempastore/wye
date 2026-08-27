# Wye PostgreSQL migrations

Alembic is the mechanism for schema changes from revision `0001_initial_schema` onward. `postgres/01_wye_schema.sql` is intentionally unchanged in this phase.

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

