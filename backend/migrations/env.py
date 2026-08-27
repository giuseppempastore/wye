import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from alembic import context

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import _parse_user_postgres_file

config = context.config
target_metadata = None


def database_url() -> str:
    """Build the migration URL using the backend's existing PG settings."""
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    database = os.environ.get("PGDATABASE", "wye")

    if not user or not password:
        file_user, file_password = _parse_user_postgres_file(
            REPOSITORY_ROOT / "postgres" / "user_postgres.txt"
        )
        user = user or file_user
        password = password or file_password
    if not user or not password:
        raise RuntimeError("Database credentials not found in env or user_postgres.txt")

    return (
        "postgresql+psycopg2://"
        + f"{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{quote_plus(database)}"
    )


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config.set_main_option("sqlalchemy.url", database_url())

    from sqlalchemy import engine_from_config, pool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

