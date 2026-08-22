"""
Simple seed runner: executes SQL files from `postgres/seeds` in alphabetical order.
Usage:
    python backend/scripts/seed_db.py

It reads DB credentials from environment variables or from `postgres/user_postgres.txt`.
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import get_connection

ROOT = Path(__file__).resolve().parents[2]
SEEDS_DIR = ROOT / 'postgres' / 'seeds'


def run():
    files = sorted([p for p in SEEDS_DIR.glob('*.sql')])
    if not files:
        print('No seed files found in', SEEDS_DIR)
        return
    conn = get_connection()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        for f in files:
            print('Applying', f.name)
            sql = f.read_text(encoding='utf-8')
            cur.execute(sql)
        cur.close()
    finally:
        conn.close()


if __name__ == '__main__':
    run()
