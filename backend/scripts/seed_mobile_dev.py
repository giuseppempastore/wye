"""Create the single idempotent product fixture used by local mobile tests."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import get_connection


BARCODE = "9876543210987"


def run() -> None:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE barcode = %s", (BARCODE,))
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO products (
                        barcode, brand_name, product_name, category,
                        product_type, source, verified, status
                    )
                    VALUES (%s, %s, %s, 'food', 'snack', 'mobile_dev_fixture', FALSE, 'active')
                    RETURNING id
                    """,
                    (BARCODE, "WYE Dev", "Mobile upload test product"),
                )
                row = cursor.fetchone()
        connection.commit()
        print(f"mobile_fixture_ready product_id={row[0]} barcode={BARCODE}")
    finally:
        connection.close()


if __name__ == "__main__":
    run()
