"""Add persistent, retryable product-acquisition work items.

Revision ID: 0025_product_acquisition_jobs
Revises: 0024_phase9_on_device_ocr_origin
"""
from alembic import op


revision = "0025_product_acquisition_jobs"
down_revision = "0024_phase9_on_device_ocr_origin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE product_acquisitions (
          id UUID PRIMARY KEY,
          product_id BIGINT REFERENCES products(id) ON DELETE RESTRICT,
          acquisition_kind VARCHAR(40) NOT NULL CHECK (
            acquisition_kind IN ('public_registration','premium_label_analysis')
          ),
          status VARCHAR(30) NOT NULL CHECK (status IN (
            'queued','processing','extracted','needs_review','admin_validated',
            'rejected','correction_required','failed'
          )),
          barcode_hash VARCHAR(64) CHECK (
            barcode_hash IS NULL OR barcode_hash ~ '^[0-9a-f]{64}$'
          ),
          idempotency_key VARCHAR(128) NOT NULL,
          pipeline_version VARCHAR(80) NOT NULL,
          provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
          recoverable_error_code VARCHAR(100),
          submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          completed_at TIMESTAMPTZ,
          UNIQUE (idempotency_key),
          CHECK (status <> 'admin_validated' OR product_id IS NOT NULL)
        );
        CREATE INDEX idx_product_acquisitions_product_updated
          ON product_acquisitions(product_id,updated_at DESC);
        CREATE INDEX idx_product_acquisitions_status
          ON product_acquisitions(status,updated_at);

        CREATE TABLE product_acquisition_documents (
          id BIGSERIAL PRIMARY KEY,
          acquisition_id UUID NOT NULL REFERENCES product_acquisitions(id)
            ON DELETE CASCADE,
          product_image_id BIGINT REFERENCES product_images(id) ON DELETE RESTRICT,
          document_type VARCHAR(30) NOT NULL CHECK (
            document_type IN ('product_front','ingredients','nutrition')
          ),
          checksum_sha256 VARCHAR(64) NOT NULL CHECK (
            checksum_sha256 ~ '^[0-9a-f]{64}$'
          ),
          raw_ocr TEXT,
          source_language VARCHAR(10),
          structured_extraction JSONB NOT NULL DEFAULT '{}'::jsonb,
          extraction_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE(acquisition_id,document_type)
        );

        CREATE TABLE product_acquisition_jobs (
          id UUID PRIMARY KEY,
          acquisition_id UUID NOT NULL UNIQUE REFERENCES product_acquisitions(id)
            ON DELETE CASCADE,
          job_status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (
            job_status IN ('queued','processing','succeeded','failed')
          ),
          attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
          max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (
            max_attempts BETWEEN 1 AND 10
          ),
          available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          lease_token UUID,
          lease_expires_at TIMESTAMPTZ,
          last_error_code VARCHAR(100),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          completed_at TIMESTAMPTZ,
          CHECK ((lease_token IS NULL) = (lease_expires_at IS NULL)),
          CHECK (job_status <> 'processing' OR lease_token IS NOT NULL),
          CHECK (job_status <> 'succeeded' OR completed_at IS NOT NULL)
        );
        CREATE INDEX idx_product_acquisition_jobs_claim
          ON product_acquisition_jobs(job_status,available_at,created_at);

        CREATE TABLE product_acquisition_events (
          id BIGSERIAL PRIMARY KEY,
          acquisition_id UUID NOT NULL REFERENCES product_acquisitions(id)
            ON DELETE CASCADE,
          from_status VARCHAR(30),
          to_status VARCHAR(30) NOT NULL,
          actor_type VARCHAR(30) NOT NULL CHECK (
            actor_type IN ('mobile_client','worker','admin','system')
          ),
          safe_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_product_acquisition_events_acquisition
          ON product_acquisition_events(acquisition_id,id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM product_acquisitions) THEN
            RAISE EXCEPTION
              'Cannot downgrade while product acquisition audit data exists';
          END IF;
        END $$;
        DROP TABLE product_acquisition_events;
        DROP TABLE product_acquisition_jobs;
        DROP TABLE product_acquisition_documents;
        DROP TABLE product_acquisitions;
        """
    )
