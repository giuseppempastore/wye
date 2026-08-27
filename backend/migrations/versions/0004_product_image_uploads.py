"""Track direct-to-object-storage image uploads.

Revision ID: 0004_product_image_uploads
Revises: 0003_data_integrity_hardening
"""
from alembic import op

revision = "0004_product_image_uploads"
down_revision = "0003_data_integrity_hardening"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    CREATE TABLE product_image_uploads (
      id UUID PRIMARY KEY, product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
      image_type VARCHAR(30) NOT NULL CHECK (image_type IN ('product_front','ingredients','nutrition','other')),
      status VARCHAR(20) NOT NULL DEFAULT 'initiated' CHECK (status IN ('initiated','verifying','finalized','failed','abandoned')),
      storage_provider VARCHAR(100) NOT NULL, bucket VARCHAR(255) NOT NULL, staging_object_key TEXT NOT NULL,
      declared_mime_type VARCHAR(100) NOT NULL, declared_byte_size BIGINT NOT NULL CHECK (declared_byte_size > 0),
      declared_checksum_algorithm VARCHAR(50) NOT NULL DEFAULT 'sha256' CHECK (declared_checksum_algorithm='sha256'),
      declared_checksum_value VARCHAR(64) NOT NULL CHECK (declared_checksum_value ~ '^[0-9a-f]{64}$'),
      verified_mime_type VARCHAR(100), verified_byte_size BIGINT, verified_checksum_algorithm VARCHAR(50), verified_checksum_value VARCHAR(64),
      verification_started_at TIMESTAMPTZ, verified_at TIMESTAMPTZ, expires_at TIMESTAMPTZ NOT NULL,
      storage_object_id BIGINT REFERENCES storage_objects(id) ON DELETE RESTRICT,
      product_image_id BIGINT REFERENCES product_images(id) ON DELETE RESTRICT,
      failure_code VARCHAR(100), failure_detail TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), finalized_at TIMESTAMPTZ,
      UNIQUE(storage_provider,bucket,staging_object_key),
      CHECK ((verified_checksum_algorithm IS NULL)=(verified_checksum_value IS NULL)),
      CHECK (status <> 'finalized' OR (storage_object_id IS NOT NULL AND product_image_id IS NOT NULL AND verified_at IS NOT NULL AND finalized_at IS NOT NULL)),
      CHECK (status = 'finalized' OR (storage_object_id IS NULL AND product_image_id IS NULL)),
      CHECK (status <> 'failed' OR failure_code IS NOT NULL),
      CHECK (status <> 'verifying' OR verification_started_at IS NOT NULL)
    );
    CREATE INDEX idx_product_image_uploads_cleanup ON product_image_uploads(status,expires_at);
    CREATE INDEX idx_product_image_uploads_product_type ON product_image_uploads(product_id,image_type,status);
    """)

def downgrade() -> None:
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM product_image_uploads) THEN RAISE EXCEPTION 'Cannot downgrade 0004 while product image upload audit records exist'; END IF; END $$""")
    op.execute("DROP TABLE product_image_uploads")
