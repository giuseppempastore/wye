"""Harden integrity constraints for the scientific data model.

Revision ID: 0003_data_integrity_hardening
Revises: 0002_scientific_data_model
Create Date: 2026-08-27
"""

from alembic import op


revision = "0003_data_integrity_hardening"
down_revision = "0002_scientific_data_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Run all checks before DDL or data changes.  Where a legacy relationship is
    # redundant and agrees with the canonical one, it is consolidated below; any
    # ambiguity aborts the Alembic transaction.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM product_label_documents d
                LEFT JOIN product_images i ON i.id = d.product_image_id
                WHERE d.source_type = 'image_derived'
                  AND (
                    d.product_image_id IS NULL
                    OR (d.product_id IS NOT NULL AND (i.id IS NULL OR i.product_id <> d.product_id))
                  )
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: image-derived label document has no image or conflicts with its image product';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM ingredient_mapping_review_candidates
                WHERE ingredient_id IS NULL OR substance_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: label mapping candidate is not exactly one canonical ingredient';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM ingredient_mapping_reviews r
                LEFT JOIN product_ingredients pi ON pi.mapping_review_id = r.id
                WHERE r.product_ingredient_id IS NULL AND pi.id IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: mapping review has no deterministic product ingredient';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM product_ingredients pi
                JOIN ingredient_mapping_reviews r ON r.id = pi.mapping_review_id
                WHERE r.product_ingredient_id IS NOT NULL AND r.product_ingredient_id <> pi.id
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: product ingredient and review links diverge';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM ingredient_mapping_reviews r
                JOIN product_ingredients pi ON pi.id = COALESCE(r.product_ingredient_id, pi.id)
                WHERE (r.product_ingredient_id IS NOT NULL OR pi.mapping_review_id = r.id)
                  AND r.label_extraction_item_id IS NOT NULL
                  AND r.label_extraction_item_id IS DISTINCT FROM pi.label_extraction_item_id
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: review source item is not the product ingredient source item';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM product_images i
                LEFT JOIN product_images successor ON successor.id = i.superseded_by_image_id
                WHERE NOT (
                    (i.is_current = TRUE
                     AND i.status IN ('pending_review', 'active', 'verified')
                     AND i.superseded_at IS NULL
                     AND i.superseded_by_image_id IS NULL)
                    OR (i.is_current = FALSE
                        AND i.status = 'superseded'
                        AND i.superseded_at IS NOT NULL
                        AND i.superseded_by_image_id IS NOT NULL
                        AND successor.id IS NOT NULL
                        AND successor.product_id = i.product_id
                        AND successor.image_type = i.image_type)
                    OR (i.is_current = FALSE
                        AND i.status = 'rejected'
                        AND i.superseded_at IS NULL
                        AND i.superseded_by_image_id IS NULL)
                )
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: product image version state is invalid';
            END IF;

            IF EXISTS (
                WITH RECURSIVE chain AS (
                    SELECT id AS origin, id, superseded_by_image_id, ARRAY[id] AS path, FALSE AS cycle
                    FROM product_images
                    UNION ALL
                    SELECT chain.origin, successor.id, successor.superseded_by_image_id,
                           chain.path || successor.id, successor.id = ANY(chain.path)
                    FROM chain
                    JOIN product_images successor ON successor.id = chain.superseded_by_image_id
                    WHERE NOT chain.cycle
                )
                SELECT 1 FROM chain WHERE cycle
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: product image supersession cycle exists';
            END IF;

            IF EXISTS (
                SELECT 1 FROM source_dataset_releases
                WHERE checksum IS NOT NULL AND btrim(checksum) = ''
            ) THEN
                RAISE EXCEPTION 'Cannot migrate: scientific release has an empty checksum';
            END IF;
        END $$
        """
    )

    op.execute("ALTER TABLE source_dataset_releases ADD COLUMN checksum_algorithm VARCHAR(50) NOT NULL DEFAULT 'unknown'")
    op.execute("DROP INDEX uq_source_dataset_releases_checksum")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_source_dataset_releases_dataset_checksum
        ON source_dataset_releases (dataset_id, checksum_algorithm, checksum)
        WHERE checksum IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE TABLE storage_objects (
            id BIGSERIAL PRIMARY KEY,
            storage_provider VARCHAR(100) NOT NULL,
            bucket VARCHAR(255) NOT NULL,
            object_key TEXT NOT NULL,
            object_version VARCHAR(255),
            checksum_algorithm VARCHAR(50),
            checksum_value VARCHAR(128),
            mime_type VARCHAR(100),
            byte_size BIGINT CHECK (byte_size IS NULL OR byte_size >= 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK ((checksum_algorithm IS NULL) = (checksum_value IS NULL)),
            CHECK (object_version IS NULL OR object_version <> '')
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_storage_objects_identity
        ON storage_objects (storage_provider, bucket, object_key, COALESCE(object_version, ''))
        """
    )
    op.execute(
        """
        CREATE INDEX idx_storage_objects_checksum
        ON storage_objects (checksum_algorithm, checksum_value)
        WHERE checksum_value IS NOT NULL
        """
    )
    op.execute("ALTER TABLE product_images ADD COLUMN storage_object_id BIGINT REFERENCES storage_objects(id) ON DELETE RESTRICT")
    op.execute("ALTER TABLE product_images ALTER COLUMN storage_reference DROP NOT NULL")
    op.execute("ALTER TABLE product_images ADD CONSTRAINT ck_product_images_storage_reference_or_object CHECK (storage_reference IS NOT NULL OR storage_object_id IS NOT NULL)")
    op.execute("CREATE INDEX idx_product_images_storage_object ON product_images (storage_object_id)")

    # A matching legacy product_id is redundant for image-derived documents and
    # can therefore be removed deterministically.
    op.execute(
        """
        UPDATE product_label_documents d
        SET product_id = NULL
        FROM product_images i
        WHERE d.source_type = 'image_derived'
          AND d.product_image_id = i.id
          AND d.product_id = i.product_id
        """
    )
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
            FOR constraint_name IN
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'product_label_documents'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) LIKE '%source_type%'
                  AND pg_get_constraintdef(oid) LIKE '%product_image_id%'
            LOOP
                EXECUTE format('ALTER TABLE product_label_documents DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$
        """
    )
    op.execute(
        """
        ALTER TABLE product_label_documents
        ADD CONSTRAINT ck_product_label_documents_image_derived_origin
        CHECK (
            (source_type = 'image_derived' AND product_image_id IS NOT NULL AND product_id IS NULL)
            OR source_type IN ('manual_input', 'catalog_import')
        )
        """
    )

    # Consolidate the only deterministic legacy direction before removing it.
    op.execute(
        """
        UPDATE ingredient_mapping_reviews r
        SET product_ingredient_id = pi.id
        FROM product_ingredients pi
        WHERE r.product_ingredient_id IS NULL
          AND pi.mapping_review_id = r.id
        """
    )
    op.execute("ALTER TABLE ingredient_mapping_reviews ALTER COLUMN product_ingredient_id SET NOT NULL")
    op.execute("ALTER TABLE ingredient_mapping_reviews DROP COLUMN label_extraction_item_id")
    op.execute("ALTER TABLE product_ingredients DROP COLUMN mapping_review_id")
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
            FOR constraint_name IN
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'ingredient_mapping_reviews'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) LIKE '%label_extraction_item_id%'
            LOOP
                EXECUTE format('ALTER TABLE ingredient_mapping_reviews DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$
        """
    )
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
            FOR constraint_name IN
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'ingredient_mapping_review_candidates'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) LIKE '%ingredient_id%'
                  AND pg_get_constraintdef(oid) LIKE '%substance_id%'
            LOOP
                EXECUTE format('ALTER TABLE ingredient_mapping_review_candidates DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$
        """
    )
    op.execute(
        """
        ALTER TABLE ingredient_mapping_review_candidates
        ADD CONSTRAINT ck_mapping_candidate_canonical_ingredient_only
        CHECK (ingredient_id IS NOT NULL AND substance_id IS NULL)
        """
    )
    op.execute("DROP INDEX uq_mapping_candidate_substance")

    op.execute("ALTER TABLE product_images ADD CONSTRAINT uq_product_images_id_product_type UNIQUE (id, product_id, image_type)")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT product_images_superseded_by_image_id_fkey")
    op.execute(
        """
        ALTER TABLE product_images
        ADD CONSTRAINT fk_product_images_superseded_same_product_type
        FOREIGN KEY (superseded_by_image_id, product_id, image_type)
        REFERENCES product_images (id, product_id, image_type)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED
        """
    )
    op.execute("ALTER TABLE product_images ADD CONSTRAINT ck_product_images_no_self_supersession CHECK (superseded_by_image_id IS NULL OR superseded_by_image_id <> id)")
    op.execute(
        """
        ALTER TABLE product_images
        ADD CONSTRAINT ck_product_images_version_state
        CHECK (
            (is_current = TRUE
             AND status IN ('pending_review', 'active', 'verified')
             AND superseded_at IS NULL
             AND superseded_by_image_id IS NULL)
            OR (is_current = FALSE
                AND status = 'superseded'
                AND superseded_at IS NOT NULL
                AND superseded_by_image_id IS NOT NULL)
            OR (is_current = FALSE
                AND status = 'rejected'
                AND superseded_at IS NULL
                AND superseded_by_image_id IS NULL)
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION assert_product_image_supersession_acyclic()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.superseded_by_image_id IS NULL THEN
                RETURN NULL;
            END IF;
            IF EXISTS (
                WITH RECURSIVE chain AS (
                    SELECT NEW.id AS id, ARRAY[NEW.id] AS path, FALSE AS cycle
                    UNION ALL
                    SELECT successor.id, chain.path || successor.id,
                           successor.id = ANY(chain.path)
                    FROM chain
                    JOIN product_images current_image ON current_image.id = chain.id
                    JOIN product_images successor ON successor.id = current_image.superseded_by_image_id
                    WHERE NOT chain.cycle
                )
                SELECT 1 FROM chain WHERE cycle
            ) THEN
                RAISE EXCEPTION 'Product image supersession cycle detected' USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_product_images_supersession_acyclic
        AFTER INSERT OR UPDATE OF superseded_by_image_id ON product_images
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION assert_product_image_supersession_acyclic()
        """
    )

    op.execute(
        """
        CREATE FUNCTION assert_accepted_mapping_review_has_selected_candidate()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE checked_review_id BIGINT;
                checked_review_ids BIGINT[];
        BEGIN
            IF TG_TABLE_NAME = 'ingredient_mapping_reviews' THEN
                checked_review_ids := ARRAY[NEW.id];
            ELSIF TG_OP = 'DELETE' THEN
                checked_review_ids := ARRAY[OLD.review_id];
            ELSIF TG_OP = 'UPDATE' THEN
                checked_review_ids := ARRAY[OLD.review_id, NEW.review_id];
            ELSE
                checked_review_ids := ARRAY[NEW.review_id];
            END IF;
            FOREACH checked_review_id IN ARRAY checked_review_ids
            LOOP
                IF EXISTS (
                    SELECT 1
                    FROM ingredient_mapping_reviews r
                    WHERE r.id = checked_review_id
                      AND r.review_status = 'accepted'
                      AND 1 <> (
                          SELECT count(*)
                          FROM ingredient_mapping_review_candidates c
                          WHERE c.review_id = r.id AND c.is_selected = TRUE
                      )
                ) THEN
                    RAISE EXCEPTION 'Accepted mapping review requires exactly one selected candidate' USING ERRCODE = '23514';
                END IF;
            END LOOP;
            RETURN NULL;
        END $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_mapping_reviews_accepted_candidate
        AFTER INSERT OR UPDATE OF review_status ON ingredient_mapping_reviews
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION assert_accepted_mapping_review_has_selected_candidate()
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_mapping_candidates_accepted_review
        AFTER INSERT OR UPDATE OR DELETE ON ingredient_mapping_review_candidates
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION assert_accepted_mapping_review_has_selected_candidate()
        """
    )


def downgrade() -> None:
    # Do not silently discard 0003-only storage identity or checksum provenance.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM product_images WHERE storage_object_id IS NOT NULL OR storage_reference IS NULL) THEN
                RAISE EXCEPTION 'Cannot downgrade 0003 while product images use storage_objects';
            END IF;
            IF EXISTS (SELECT 1 FROM source_dataset_releases WHERE checksum_algorithm <> 'unknown') THEN
                RAISE EXCEPTION 'Cannot downgrade 0003 while checksum algorithms carry non-legacy provenance';
            END IF;
            IF EXISTS (
                SELECT checksum
                FROM source_dataset_releases
                WHERE checksum IS NOT NULL
                GROUP BY checksum HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0003 while release checksums are duplicated across datasets';
            END IF;
        END $$
        """
    )

    op.execute("DROP TRIGGER trg_mapping_candidates_accepted_review ON ingredient_mapping_review_candidates")
    op.execute("DROP TRIGGER trg_mapping_reviews_accepted_candidate ON ingredient_mapping_reviews")
    op.execute("DROP FUNCTION assert_accepted_mapping_review_has_selected_candidate()")
    op.execute("DROP TRIGGER trg_product_images_supersession_acyclic ON product_images")
    op.execute("DROP FUNCTION assert_product_image_supersession_acyclic()")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT ck_product_images_version_state")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT ck_product_images_no_self_supersession")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT fk_product_images_superseded_same_product_type")
    op.execute("ALTER TABLE product_images ADD CONSTRAINT product_images_superseded_by_image_id_fkey FOREIGN KEY (superseded_by_image_id) REFERENCES product_images(id) ON DELETE RESTRICT")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT uq_product_images_id_product_type")

    op.execute("CREATE UNIQUE INDEX uq_mapping_candidate_substance ON ingredient_mapping_review_candidates (review_id, substance_id) WHERE substance_id IS NOT NULL")
    op.execute("ALTER TABLE ingredient_mapping_review_candidates DROP CONSTRAINT ck_mapping_candidate_canonical_ingredient_only")
    op.execute("ALTER TABLE ingredient_mapping_review_candidates ADD CONSTRAINT ingredient_mapping_review_candidates_check CHECK (ingredient_id IS NOT NULL OR substance_id IS NOT NULL)")
    op.execute("ALTER TABLE product_ingredients ADD COLUMN mapping_review_id BIGINT REFERENCES ingredient_mapping_reviews(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE ingredient_mapping_reviews ADD COLUMN label_extraction_item_id BIGINT REFERENCES label_extraction_items(id) ON DELETE SET NULL")
    op.execute("UPDATE ingredient_mapping_reviews r SET label_extraction_item_id = pi.label_extraction_item_id FROM product_ingredients pi WHERE pi.id = r.product_ingredient_id")
    op.execute("ALTER TABLE ingredient_mapping_reviews ALTER COLUMN product_ingredient_id DROP NOT NULL")
    op.execute("ALTER TABLE ingredient_mapping_reviews ADD CONSTRAINT ingredient_mapping_reviews_check CHECK (label_extraction_item_id IS NOT NULL OR product_ingredient_id IS NOT NULL)")

    op.execute("ALTER TABLE product_label_documents DROP CONSTRAINT ck_product_label_documents_image_derived_origin")
    op.execute("ALTER TABLE product_label_documents ADD CONSTRAINT product_label_documents_check CHECK ((source_type = 'image_derived' AND product_image_id IS NOT NULL) OR source_type IN ('manual_input', 'catalog_import'))")

    op.execute("DROP INDEX idx_product_images_storage_object")
    op.execute("ALTER TABLE product_images DROP CONSTRAINT ck_product_images_storage_reference_or_object")
    op.execute("ALTER TABLE product_images ALTER COLUMN storage_reference SET NOT NULL")
    op.execute("ALTER TABLE product_images DROP COLUMN storage_object_id")
    op.execute("DROP INDEX idx_storage_objects_checksum")
    op.execute("DROP INDEX uq_storage_objects_identity")
    op.execute("DROP TABLE storage_objects")

    op.execute("DROP INDEX uq_source_dataset_releases_dataset_checksum")
    op.execute("ALTER TABLE source_dataset_releases DROP COLUMN checksum_algorithm")
    op.execute("CREATE UNIQUE INDEX uq_source_dataset_releases_checksum ON source_dataset_releases (checksum) WHERE checksum IS NOT NULL")
