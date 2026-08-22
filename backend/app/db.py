import os
from pathlib import Path
import re
import psycopg2

ROOT = Path(__file__).resolve().parents[2]


def _parse_user_postgres_file(path: Path):
    if not path.exists():
        return None, None
    text = path.read_text(encoding='utf-8')
    # Very small parser: looks for lines starting with username: and password:
    username = None
    password = None
    lines = [l.rstrip() for l in text.splitlines()]
    for i, l in enumerate(lines):
        if l.strip().lower().startswith('username:'):
            # next non-empty line
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                username = lines[j].strip()
        if l.strip().lower().startswith('password:'):
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                password = lines[j].strip()
    return username, password


def get_connection():
    host = os.environ.get('PGHOST', 'localhost')
    port = os.environ.get('PGPORT', '5432')
    user = os.environ.get('PGUSER')
    password = os.environ.get('PGPASSWORD')
    dbname = os.environ.get('PGDATABASE', 'wye')

    if (not user) or (not password):
        user_file = ROOT / 'postgres' / 'user_postgres.txt'
        u, p = _parse_user_postgres_file(user_file)
        if u and not user:
            user = u
        if p and not password:
            password = p

    if not user or not password:
        raise RuntimeError('Database credentials not found in env or user_postgres.txt')

    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
    return conn
