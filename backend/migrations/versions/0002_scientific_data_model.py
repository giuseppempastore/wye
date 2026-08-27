"""Add scientific data and label provenance model.

Revision ID: 0002_scientific_data_model
Revises: 0001_initial_schema
Create Date: 2026-08-27
"""

from alembic import op

revision = "0002_scientific_data_model"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE source_datasets (
            id BIGSERIAL PRIMARY KEY,
            source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
            dataset_name VARCHAR(255) NOT NULL,
            dataset_key VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_id, dataset_key)
        )
    """)
    op.execute("""
        CREATE TABLE source_dataset_releases (
            id BIGSERIAL PRIMARY KEY,
            dataset_id BIGINT NOT NULL REFERENCES source_datasets(id) ON DELETE RESTRICT,
            version_label VARCHAR(255) NOT NULL,
            released_at TIMESTAMPTZ,
            acquired_at TIMESTAMPTZ,
            source_url TEXT,
            checksum VARCHAR(128),
            format VARCHAR(50),
            release_status VARCHAR(30) NOT NULL DEFAULT 'declared'
                CHECK (release_status IN ('declared', 'acquired', 'validated', 'superseded', 'rejected')),
            license_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (dataset_id, version_label)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_source_dataset_releases_checksum
        ON source_dataset_releases (checksum) WHERE checksum IS NOT NULL
    """)
    op.execute("""
        CREATE TABLE substances (
            id BIGSERIAL PRIMARY KEY,
            preferred_name VARCHAR(255) NOT NULL,
            normalized_name VARCHAR(255) NOT NULL UNIQUE,
            scientific_name VARCHAR(255),
            substance_type VARCHAR(50) NOT NULL DEFAULT 'unknown'
                CHECK (substance_type IN ('additive', 'chemical_substance', 'biological_substance',
                    'contaminant', 'nutrient', 'mixture', 'unknown')),
            status VARCHAR(30) NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'deprecated', 'review_pending')),
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE substance_identifiers (
            id BIGSERIAL PRIMARY KEY,
            substance_id BIGINT NOT NULL REFERENCES substances(id) ON DELETE RESTRICT,
            identifier_system VARCHAR(50) NOT NULL,
            identifier_value VARCHAR(255) NOT NULL,
            normalized_value VARCHAR(255) NOT NULL,
            is_primary BOOLEAN NOT NULL DEFAULT FALSE,
            verification_status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                CHECK (verification_status IN ('pending_review', 'verified', 'rejected', 'deprecated')),
            source_dataset_release_id BIGINT REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (identifier_system, normalized_value)
        )
    """)
    op.execute("""
        CREATE TABLE ingredient_substances (
            id BIGSERIAL PRIMARY KEY,
            ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
            substance_id BIGINT NOT NULL REFERENCES substances(id) ON DELETE RESTRICT,
            relationship_type VARCHAR(40) NOT NULL
                CHECK (relationship_type IN ('represents', 'contains', 'derived_from',
                    'mixture_component', 'equivalent_to')),
            mapping_method VARCHAR(30) NOT NULL DEFAULT 'manual_review'
                CHECK (mapping_method IN ('manual_review', 'dataset', 'deterministic', 'legacy')),
            mapping_status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                CHECK (mapping_status IN ('accepted', 'pending_review', 'ambiguous', 'rejected', 'legacy_unreviewed')),
            mapping_confidence NUMERIC(4,3) CHECK (mapping_confidence BETWEEN 0 AND 1),
            source_dataset_release_id BIGINT REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
            provenance JSONB,
            valid_from DATE,
            valid_to DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (ingredient_id, substance_id, relationship_type)
        )
    """)
    op.execute("""
        CREATE TABLE product_images (
            id BIGSERIAL PRIMARY KEY,
            product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            image_type VARCHAR(30) NOT NULL
                CHECK (image_type IN ('product_front', 'ingredients', 'nutrition', 'other')),
            storage_reference TEXT NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            byte_size BIGINT CHECK (byte_size IS NULL OR byte_size >= 0),
            checksum VARCHAR(128) NOT NULL,
            source VARCHAR(30) NOT NULL
                CHECK (source IN ('user_submission', 'catalog_import', 'manufacturer', 'reviewer_submission')),
            status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                CHECK (status IN ('pending_review', 'active', 'verified', 'rejected', 'superseded')),
            is_current BOOLEAN NOT NULL DEFAULT TRUE,
            captured_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            superseded_at TIMESTAMPTZ,
            superseded_by_image_id BIGINT REFERENCES product_images(id) ON DELETE RESTRICT,
            provenance JSONB
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_product_images_current_type
        ON product_images (product_id, image_type)
        WHERE is_current = TRUE
          AND status IN ('pending_review', 'active', 'verified')
    """)
    op.execute("CREATE INDEX idx_product_images_checksum ON product_images (checksum)")
    op.execute("CREATE INDEX idx_product_images_product_status ON product_images (product_id, status)")
    op.execute("""
        CREATE TABLE product_label_documents (
            id BIGSERIAL PRIMARY KEY,
            product_id BIGINT REFERENCES products(id) ON DELETE SET NULL,
            product_image_id BIGINT REFERENCES product_images(id) ON DELETE RESTRICT,
            raw_text TEXT NOT NULL,
            detected_language VARCHAR(10),
            source_type VARCHAR(30) NOT NULL
                CHECK (source_type IN ('image_derived', 'manual_input', 'catalog_import')),
            source_checksum VARCHAR(128),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (
                (source_type = 'image_derived' AND product_image_id IS NOT NULL)
                OR source_type IN ('manual_input', 'catalog_import')
            )
        )
    """)
    op.execute("CREATE INDEX idx_product_label_documents_image ON product_label_documents (product_image_id)")
    op.execute("""
        CREATE TABLE label_extraction_runs (
            id BIGSERIAL PRIMARY KEY,
            label_document_id BIGINT NOT NULL REFERENCES product_label_documents(id) ON DELETE CASCADE,
            extraction_method VARCHAR(30) NOT NULL
                CHECK (extraction_method IN ('manual', 'deterministic', 'ai')),
            provider VARCHAR(100),
            model_name VARCHAR(255),
            model_version VARCHAR(100),
            prompt_version VARCHAR(100),
            raw_response JSONB,
            run_status VARCHAR(30) NOT NULL DEFAULT 'completed'
                CHECK (run_status IN ('completed', 'failed', 'superseded')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE label_extraction_items (
            id BIGSERIAL PRIMARY KEY,
            extraction_run_id BIGINT NOT NULL REFERENCES label_extraction_runs(id) ON DELETE CASCADE,
            item_type VARCHAR(30) NOT NULL
                CHECK (item_type IN ('ingredient', 'ingredient_list', 'nutrition', 'allergen', 'quantity', 'unit', 'other')),
            raw_text TEXT NOT NULL,
            normalized_text TEXT,
            detected_language VARCHAR(10),
            structured_value JSONB,
            unit VARCHAR(30),
            position_in_document INTEGER,
            extraction_confidence NUMERIC(4,3) CHECK (extraction_confidence BETWEEN 0 AND 1),
            extraction_status VARCHAR(30) NOT NULL DEFAULT 'detected'
                CHECK (extraction_status IN ('detected', 'validated', 'rejected')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_label_extraction_items_type ON label_extraction_items (item_type, extraction_status)")
    op.execute("""
        CREATE TABLE scientific_assessments (
            id BIGSERIAL PRIMARY KEY,
            substance_id BIGINT NOT NULL REFERENCES substances(id) ON DELETE RESTRICT,
            source_dataset_release_id BIGINT NOT NULL REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
            assessment_type VARCHAR(100) NOT NULL,
            assessment_version VARCHAR(255) NOT NULL,
            external_assessment_id VARCHAR(255),
            assessment_status VARCHAR(30) NOT NULL DEFAULT 'pending_review'
                CHECK (assessment_status IN ('pending_review', 'published', 'superseded', 'withdrawn', 'rejected')),
            published_at DATE,
            valid_from DATE,
            valid_to DATE,
            document_reference TEXT,
            conclusion_text TEXT,
            assessment_data JSONB,
            checksum VARCHAR(128),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (substance_id, source_dataset_release_id, assessment_type, assessment_version)
        )
    """)
    op.execute("""
        CREATE TABLE scientific_assessment_findings (
            id BIGSERIAL PRIMARY KEY,
            assessment_id BIGINT NOT NULL REFERENCES scientific_assessments(id) ON DELETE CASCADE,
            finding_key VARCHAR(255),
            endpoint VARCHAR(255),
            value_numeric NUMERIC,
            value_text TEXT,
            unit VARCHAR(50),
            population_context TEXT,
            evidence_type VARCHAR(100),
            conclusion_text TEXT,
            source_locator TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_scientific_assessments_substance_status ON scientific_assessments (substance_id, assessment_status)")
    op.execute("""
        CREATE TABLE ingredient_mapping_reviews (
            id BIGSERIAL PRIMARY KEY,
            label_extraction_item_id BIGINT REFERENCES label_extraction_items(id) ON DELETE SET NULL,
            product_ingredient_id BIGINT REFERENCES product_ingredients(id) ON DELETE SET NULL,
            raw_text TEXT NOT NULL,
            normalized_text TEXT,
            detected_language VARCHAR(10),
            review_status VARCHAR(30) NOT NULL DEFAULT 'pending'
                CHECK (review_status IN ('pending', 'accepted', 'ambiguous', 'rejected')),
            requested_by_method VARCHAR(30) NOT NULL
                CHECK (requested_by_method IN ('deterministic', 'ai', 'manual', 'import')),
            reviewed_by VARCHAR(255),
            reviewed_at TIMESTAMPTZ,
            review_provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (label_extraction_item_id IS NOT NULL OR product_ingredient_id IS NOT NULL)
        )
    """)
    op.execute("""
        CREATE TABLE ingredient_mapping_review_candidates (
            id BIGSERIAL PRIMARY KEY,
            review_id BIGINT NOT NULL REFERENCES ingredient_mapping_reviews(id) ON DELETE CASCADE,
            ingredient_id BIGINT REFERENCES ingredients(id) ON DELETE RESTRICT,
            substance_id BIGINT REFERENCES substances(id) ON DELETE RESTRICT,
            candidate_method VARCHAR(30) NOT NULL
                CHECK (candidate_method IN ('deterministic', 'ai', 'manual_review', 'dataset')),
            candidate_confidence NUMERIC(4,3) CHECK (candidate_confidence BETWEEN 0 AND 1),
            rationale TEXT,
            is_selected BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (ingredient_id IS NOT NULL OR substance_id IS NOT NULL)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mapping_candidate_ingredient
        ON ingredient_mapping_review_candidates (review_id, ingredient_id)
        WHERE ingredient_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mapping_candidate_substance
        ON ingredient_mapping_review_candidates (review_id, substance_id)
        WHERE substance_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mapping_review_selected_candidate
        ON ingredient_mapping_review_candidates (review_id)
        WHERE is_selected = TRUE
    """)
    op.execute("CREATE INDEX idx_mapping_reviews_normalized_status ON ingredient_mapping_reviews (normalized_text, review_status)")

    op.execute("""
        ALTER TABLE ingredient_aliases
        ADD COLUMN mapping_method VARCHAR(30) NOT NULL DEFAULT 'legacy'
            CHECK (mapping_method IN ('manual_review', 'dataset', 'deterministic', 'legacy'))
    """)
    op.execute("""
        ALTER TABLE ingredient_aliases
        ADD COLUMN mapping_status VARCHAR(30) NOT NULL DEFAULT 'legacy_unreviewed'
            CHECK (mapping_status IN ('accepted', 'deprecated', 'legacy_unreviewed'))
    """)
    op.execute("ALTER TABLE ingredient_aliases ADD COLUMN approved_at TIMESTAMPTZ")
    op.execute("ALTER TABLE ingredient_aliases ADD COLUMN review_provenance JSONB")
    op.execute("""
        ALTER TABLE ingredient_aliases
        ADD COLUMN source_dataset_release_id BIGINT REFERENCES source_dataset_releases(id) ON DELETE RESTRICT
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_ingredient_aliases_accepted_normalized_language
        ON ingredient_aliases (normalized_alias, language)
        WHERE mapping_status = 'accepted'
    """)

    op.execute("ALTER TABLE product_ingredients ALTER COLUMN ingredient_id DROP NOT NULL")
    op.execute("""
        ALTER TABLE product_ingredients
        ADD COLUMN label_extraction_item_id BIGINT REFERENCES label_extraction_items(id) ON DELETE SET NULL
    """)
    op.execute("ALTER TABLE product_ingredients ADD COLUMN normalized_text TEXT")
    op.execute("ALTER TABLE product_ingredients ADD COLUMN detected_language VARCHAR(10)")
    op.execute("""
        ALTER TABLE product_ingredients
        ADD COLUMN mapping_method VARCHAR(30) NOT NULL DEFAULT 'legacy'
            CHECK (mapping_method IN ('deterministic_alias', 'ai_candidate', 'manual_review',
                'manual_input', 'unmapped', 'legacy'))
    """)
    op.execute("""
        ALTER TABLE product_ingredients
        ADD COLUMN mapping_status VARCHAR(30) NOT NULL DEFAULT 'legacy_unreviewed'
            CHECK (mapping_status IN ('accepted', 'needs_review', 'ambiguous', 'unmapped',
                'rejected', 'legacy_unreviewed'))
    """)
    op.execute("ALTER TABLE product_ingredients ADD COLUMN mapping_provenance JSONB")
    op.execute("""
        ALTER TABLE product_ingredients
        ADD COLUMN mapping_review_id BIGINT REFERENCES ingredient_mapping_reviews(id) ON DELETE SET NULL
    """)
    op.execute("CREATE INDEX idx_product_ingredients_mapping_status ON product_ingredients (mapping_status)")
    op.execute("CREATE INDEX idx_product_ingredients_label_item ON product_ingredients (label_extraction_item_id)")


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM product_ingredients WHERE ingredient_id IS NULL) THEN "
        "RAISE EXCEPTION 'Cannot downgrade 0002 while product_ingredients contains unresolved mappings'; "
        "END IF; "
        "END $$"
    )

    op.drop_index("idx_product_ingredients_label_item", table_name="product_ingredients")
    op.drop_index("idx_product_ingredients_mapping_status", table_name="product_ingredients")
    op.drop_column("product_ingredients", "mapping_review_id")
    op.drop_column("product_ingredients", "mapping_provenance")
    op.drop_column("product_ingredients", "mapping_status")
    op.drop_column("product_ingredients", "mapping_method")
    op.drop_column("product_ingredients", "detected_language")
    op.drop_column("product_ingredients", "normalized_text")
    op.drop_column("product_ingredients", "label_extraction_item_id")
    op.alter_column("product_ingredients", "ingredient_id", nullable=False)

    op.drop_index("uq_ingredient_aliases_accepted_normalized_language", table_name="ingredient_aliases")
    op.drop_column("ingredient_aliases", "source_dataset_release_id")
    op.drop_column("ingredient_aliases", "review_provenance")
    op.drop_column("ingredient_aliases", "approved_at")
    op.drop_column("ingredient_aliases", "mapping_status")
    op.drop_column("ingredient_aliases", "mapping_method")

    op.drop_index("idx_mapping_reviews_normalized_status", table_name="ingredient_mapping_reviews")
    op.drop_index("uq_mapping_review_selected_candidate", table_name="ingredient_mapping_review_candidates")
    op.drop_index("uq_mapping_candidate_substance", table_name="ingredient_mapping_review_candidates")
    op.drop_index("uq_mapping_candidate_ingredient", table_name="ingredient_mapping_review_candidates")
    op.drop_table("ingredient_mapping_review_candidates")
    op.drop_table("ingredient_mapping_reviews")
    op.drop_index("idx_scientific_assessments_substance_status", table_name="scientific_assessments")
    op.drop_table("scientific_assessment_findings")
    op.drop_table("scientific_assessments")
    op.drop_index("idx_label_extraction_items_type", table_name="label_extraction_items")
    op.drop_table("label_extraction_items")
    op.drop_table("label_extraction_runs")
    op.drop_index("idx_product_label_documents_image", table_name="product_label_documents")
    op.drop_table("product_label_documents")
    op.drop_index("idx_product_images_product_status", table_name="product_images")
    op.drop_index("idx_product_images_checksum", table_name="product_images")
    op.drop_index("uq_product_images_current_type", table_name="product_images")
    op.drop_table("product_images")
    op.drop_table("ingredient_substances")
    op.drop_table("substance_identifiers")
    op.drop_table("substances")
    op.drop_index("uq_source_dataset_releases_checksum", table_name="source_dataset_releases")
    op.drop_table("source_dataset_releases")
    op.drop_table("source_datasets")

