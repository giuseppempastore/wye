"""Add the auditable label extraction lifecycle.

Revision ID: 0005_label_extraction_pipeline
Revises: 0004_product_image_uploads
"""
from alembic import op

revision = "0005_label_extraction_pipeline"
down_revision = "0004_product_image_uploads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (
        SELECT 1 FROM product_label_documents d
        JOIN product_images i ON i.id=d.product_image_id
        WHERE d.source_type='image_derived' AND i.image_type NOT IN ('ingredients','nutrition')
      ) THEN
        RAISE EXCEPTION 'Cannot migrate: image-derived documents exist for unsupported image types';
      END IF;
    END $$;
    ALTER TABLE product_label_documents ADD COLUMN document_type VARCHAR(30);
    UPDATE product_label_documents d SET document_type = CASE
      WHEN d.source_type='image_derived' THEN i.image_type ELSE 'other' END
    FROM product_images i WHERE i.id=d.product_image_id;
    UPDATE product_label_documents SET document_type='other' WHERE document_type IS NULL;
    ALTER TABLE product_label_documents ALTER COLUMN document_type SET NOT NULL;
    ALTER TABLE product_label_documents ADD CONSTRAINT ck_product_label_documents_type
      CHECK (document_type IN ('ingredients','nutrition','other'));
    ALTER TABLE product_label_documents ALTER COLUMN raw_text DROP NOT NULL;
    CREATE UNIQUE INDEX uq_product_label_documents_image_type
      ON product_label_documents(product_image_id, document_type)
      WHERE source_type='image_derived';

    CREATE FUNCTION assert_label_document_matches_image_type()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    DECLARE actual_type VARCHAR(30);
    BEGIN
      IF NEW.source_type <> 'image_derived' THEN RETURN NEW; END IF;
      SELECT image_type INTO actual_type FROM product_images WHERE id=NEW.product_image_id;
      IF actual_type IS NULL OR actual_type NOT IN ('ingredients','nutrition') OR actual_type <> NEW.document_type THEN
        RAISE EXCEPTION 'Image-derived label document type must match a supported source image type'
          USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_label_document_matches_image_type
      BEFORE INSERT OR UPDATE OF product_image_id,document_type,source_type ON product_label_documents
      FOR EACH ROW EXECUTE FUNCTION assert_label_document_matches_image_type();

    ALTER TABLE label_extraction_runs DROP CONSTRAINT label_extraction_runs_run_status_check;
    UPDATE label_extraction_runs SET run_status='succeeded' WHERE run_status='completed';
    ALTER TABLE label_extraction_runs ALTER COLUMN run_status SET DEFAULT 'pending';
    ALTER TABLE label_extraction_runs ADD CONSTRAINT ck_label_extraction_runs_status
      CHECK (run_status IN ('pending','running','succeeded','failed','superseded'));
    ALTER TABLE label_extraction_runs ADD COLUMN extracted_raw_text TEXT;
    ALTER TABLE label_extraction_runs ADD COLUMN error_code VARCHAR(100);
    ALTER TABLE label_extraction_runs ADD COLUMN error_detail TEXT;
    ALTER TABLE label_extraction_runs ADD COLUMN provider_request_id VARCHAR(255);
    ALTER TABLE label_extraction_runs ADD COLUMN schema_version VARCHAR(100);
    ALTER TABLE label_extraction_runs ADD COLUMN prompt_hash VARCHAR(64);
    ALTER TABLE label_extraction_runs ADD COLUMN idempotency_key VARCHAR(255);
    ALTER TABLE label_extraction_runs ADD COLUMN request_fingerprint VARCHAR(64);
    ALTER TABLE label_extraction_runs ADD COLUMN started_at TIMESTAMPTZ;
    ALTER TABLE label_extraction_runs ADD COLUMN completed_at TIMESTAMPTZ;
    UPDATE label_extraction_runs SET completed_at=created_at
      WHERE run_status IN ('succeeded','failed','superseded');
    UPDATE label_extraction_runs SET error_code='legacy_failure'
      WHERE run_status='failed' AND error_code IS NULL;
    ALTER TABLE label_extraction_runs ADD CONSTRAINT ck_label_extraction_runs_error
      CHECK (run_status <> 'failed' OR error_code IS NOT NULL);
    ALTER TABLE label_extraction_runs ADD CONSTRAINT ck_label_extraction_runs_completion
      CHECK ((run_status IN ('succeeded','failed','superseded')) = (completed_at IS NOT NULL));
    ALTER TABLE label_extraction_runs ADD CONSTRAINT ck_label_extraction_runs_idempotency
      CHECK ((idempotency_key IS NULL) = (request_fingerprint IS NULL));
    CREATE UNIQUE INDEX uq_label_extraction_runs_document_idempotency
      ON label_extraction_runs(label_document_id,idempotency_key) WHERE idempotency_key IS NOT NULL;
    CREATE INDEX idx_label_extraction_runs_document_created
      ON label_extraction_runs(label_document_id,created_at DESC,id DESC);
    CREATE INDEX idx_label_extraction_runs_status ON label_extraction_runs(run_status);
    """)


def downgrade() -> None:
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM label_extraction_runs WHERE run_status IN ('pending','running')) THEN
        RAISE EXCEPTION 'Cannot downgrade 0005 while extraction runs are active';
      END IF;
      IF EXISTS (SELECT 1 FROM product_label_documents WHERE raw_text IS NULL) THEN
        RAISE EXCEPTION 'Cannot downgrade 0005 while label documents have no legacy raw_text';
      END IF;
    END $$;
    DROP INDEX idx_label_extraction_runs_status;
    DROP INDEX idx_label_extraction_runs_document_created;
    DROP INDEX uq_label_extraction_runs_document_idempotency;
    ALTER TABLE label_extraction_runs DROP CONSTRAINT ck_label_extraction_runs_idempotency;
    ALTER TABLE label_extraction_runs DROP CONSTRAINT ck_label_extraction_runs_completion;
    ALTER TABLE label_extraction_runs DROP CONSTRAINT ck_label_extraction_runs_error;
    ALTER TABLE label_extraction_runs DROP COLUMN completed_at;
    ALTER TABLE label_extraction_runs DROP COLUMN started_at;
    ALTER TABLE label_extraction_runs DROP COLUMN request_fingerprint;
    ALTER TABLE label_extraction_runs DROP COLUMN idempotency_key;
    ALTER TABLE label_extraction_runs DROP COLUMN prompt_hash;
    ALTER TABLE label_extraction_runs DROP COLUMN schema_version;
    ALTER TABLE label_extraction_runs DROP COLUMN provider_request_id;
    ALTER TABLE label_extraction_runs DROP COLUMN error_detail;
    ALTER TABLE label_extraction_runs DROP COLUMN error_code;
    ALTER TABLE label_extraction_runs DROP COLUMN extracted_raw_text;
    ALTER TABLE label_extraction_runs DROP CONSTRAINT ck_label_extraction_runs_status;
    UPDATE label_extraction_runs SET run_status='completed' WHERE run_status='succeeded';
    ALTER TABLE label_extraction_runs ALTER COLUMN run_status SET DEFAULT 'completed';
    ALTER TABLE label_extraction_runs ADD CONSTRAINT label_extraction_runs_run_status_check
      CHECK (run_status IN ('completed','failed','superseded'));
    DROP TRIGGER trg_label_document_matches_image_type ON product_label_documents;
    DROP FUNCTION assert_label_document_matches_image_type();
    DROP INDEX uq_product_label_documents_image_type;
    ALTER TABLE product_label_documents ALTER COLUMN raw_text SET NOT NULL;
    ALTER TABLE product_label_documents DROP CONSTRAINT ck_product_label_documents_type;
    ALTER TABLE product_label_documents DROP COLUMN document_type;
    """)
