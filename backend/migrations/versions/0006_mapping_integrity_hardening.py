"""Harden label-item materialization and mapping-review integrity.

Revision ID: 0006_mapping_integrity_hardening
Revises: 0005_label_extraction_pipeline
"""

from alembic import op


revision = "0006_mapping_integrity_hardening"
down_revision = "0005_label_extraction_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT label_extraction_item_id
                FROM product_ingredients
                WHERE label_extraction_item_id IS NOT NULL
                GROUP BY label_extraction_item_id
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: a label extraction item is materialized more than once';
            END IF;

            IF EXISTS (
                SELECT product_ingredient_id
                FROM ingredient_mapping_reviews
                WHERE review_status = 'pending'
                GROUP BY product_ingredient_id
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: a product ingredient has multiple pending reviews';
            END IF;
        END $$
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_product_ingredients_label_extraction_item
        ON product_ingredients (label_extraction_item_id)
        WHERE label_extraction_item_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_mapping_reviews_pending_product_ingredient
        ON ingredient_mapping_reviews (product_ingredient_id)
        WHERE review_status = 'pending'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_mapping_reviews_pending_product_ingredient")
    op.execute("DROP INDEX uq_product_ingredients_label_extraction_item")
