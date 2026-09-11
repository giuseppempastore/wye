"""Record on-device OCR as an explicit label-document origin.

Revision ID: 0024_phase9_on_device_ocr_origin
Revises: 0023_phase9_photo_first_acquisition
"""
from alembic import op


revision = "0024_phase9_on_device_ocr_origin"
down_revision = "0023_phase9_photo_first_acquisition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE product_label_documents "
        "DROP CONSTRAINT product_label_documents_source_type_check"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "ADD CONSTRAINT product_label_documents_source_type_check "
        "CHECK (source_type IN "
        "('image_derived', 'manual_input', 'catalog_import', 'on_device_ocr'))"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "DROP CONSTRAINT ck_product_label_documents_image_derived_origin"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "ADD CONSTRAINT ck_product_label_documents_image_derived_origin "
        "CHECK ((source_type = 'image_derived' AND product_image_id IS NOT NULL "
        "AND product_id IS NULL) OR source_type IN "
        "('manual_input', 'catalog_import', 'on_device_ocr'))"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM product_label_documents
            WHERE source_type = 'on_device_ocr'
          ) THEN
            RAISE EXCEPTION
              'Cannot downgrade while on-device OCR label documents exist';
          END IF;
        END $$
        """
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "DROP CONSTRAINT ck_product_label_documents_image_derived_origin"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "DROP CONSTRAINT product_label_documents_source_type_check"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "ADD CONSTRAINT product_label_documents_source_type_check "
        "CHECK (source_type IN "
        "('image_derived', 'manual_input', 'catalog_import'))"
    )
    op.execute(
        "ALTER TABLE product_label_documents "
        "ADD CONSTRAINT ck_product_label_documents_image_derived_origin "
        "CHECK ((source_type = 'image_derived' AND product_image_id IS NOT NULL "
        "AND product_id IS NULL) OR source_type IN "
        "('manual_input', 'catalog_import'))"
    )
