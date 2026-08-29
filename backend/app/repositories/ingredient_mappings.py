"""PostgreSQL persistence for ingredient mapping orchestration."""

import json
from dataclasses import dataclass

from psycopg2.extras import execute_values


@dataclass(frozen=True)
class MappingExtractionItem:
    item_id: int
    raw_text: str
    detected_language: str | None
    position_in_document: int | None
    structured_value: dict | None


@dataclass(frozen=True)
class MappingExtractionRun:
    run_id: int
    product_id: int
    run_status: str
    document_type: str
    image_type: str
    items: tuple[MappingExtractionItem, ...]


class PostgresIngredientMappingRepository:
    """Keep mapping SQL behind a transaction supplied by the service."""

    def load_run(self, cursor, run_id: int) -> MappingExtractionRun | None:
        cursor.execute(
            """
            SELECT r.id, i.product_id, r.run_status, d.document_type, i.image_type
            FROM label_extraction_runs r
            JOIN product_label_documents d ON d.id = r.label_document_id
            JOIN product_images i ON i.id = d.product_image_id
            WHERE r.id = %s AND d.source_type = 'image_derived'
            FOR SHARE OF r, d, i
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        cursor.execute(
            """
            SELECT id, raw_text, detected_language, position_in_document,
                   structured_value
            FROM label_extraction_items
            WHERE extraction_run_id = %s AND item_type = 'ingredient'
            ORDER BY position_in_document NULLS LAST, id
            """,
            (run_id,),
        )
        items = tuple(
            MappingExtractionItem(
                item_id=item["id"],
                raw_text=item["raw_text"],
                detected_language=item["detected_language"],
                position_in_document=item["position_in_document"],
                structured_value=item["structured_value"],
            )
            for item in cursor.fetchall()
        )
        return MappingExtractionRun(
            run_id=row["id"],
            product_id=row["product_id"],
            run_status=row["run_status"],
            document_type=row["document_type"],
            image_type=row["image_type"],
            items=items,
        )

    def get_or_create_product_ingredient(
        self, cursor, product_id, item, normalized_text, provenance
    ):
        cursor.execute(
            """
            INSERT INTO product_ingredients (
                product_id, ingredient_id, label_extraction_item_id, raw_name,
                normalized_text, detected_language, position_in_list,
                mapping_method, mapping_status, mapping_provenance
            )
            VALUES (%s, NULL, %s, %s, %s, %s, %s, 'unmapped',
                    'needs_review', %s::jsonb)
            ON CONFLICT (label_extraction_item_id)
                WHERE label_extraction_item_id IS NOT NULL
            DO NOTHING
            RETURNING id, mapping_status
            """,
            (
                product_id,
                item.item_id,
                item.raw_text,
                normalized_text,
                item.detected_language,
                item.position_in_document or 0,
                json.dumps(provenance),
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            return row, True
        cursor.execute(
            """
            SELECT id, product_id, mapping_status
            FROM product_ingredients
            WHERE label_extraction_item_id = %s
            FOR UPDATE
            """,
            (item.item_id,),
        )
        return cursor.fetchone(), False

    def latest_review(self, cursor, product_ingredient_id):
        cursor.execute(
            """
            SELECT id, review_status
            FROM ingredient_mapping_reviews
            WHERE product_ingredient_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            FOR UPDATE
            """,
            (product_ingredient_id,),
        )
        return cursor.fetchone()

    def create_pending_review(
        self, cursor, product_ingredient_id, item, normalized_text, provenance
    ):
        cursor.execute(
            """
            INSERT INTO ingredient_mapping_reviews (
                product_ingredient_id, raw_text, normalized_text,
                detected_language, review_status, requested_by_method,
                review_provenance
            )
            VALUES (%s, %s, %s, %s, 'pending', 'deterministic', %s::jsonb)
            ON CONFLICT (product_ingredient_id) WHERE review_status = 'pending'
            DO NOTHING
            RETURNING id, review_status
            """,
            (
                product_ingredient_id,
                item.raw_text,
                normalized_text,
                item.detected_language,
                json.dumps(provenance),
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            return row, True
        cursor.execute(
            """
            SELECT id, review_status
            FROM ingredient_mapping_reviews
            WHERE product_ingredient_id = %s AND review_status = 'pending'
            FOR UPDATE
            """,
            (product_ingredient_id,),
        )
        return cursor.fetchone(), False

    def insert_candidates(self, cursor, review_id, candidates):
        if not candidates:
            return
        execute_values(
            cursor,
            """
            INSERT INTO ingredient_mapping_review_candidates (
                review_id, ingredient_id, candidate_method,
                candidate_confidence, rationale, is_selected
            ) VALUES %s
            ON CONFLICT (review_id, ingredient_id) WHERE ingredient_id IS NOT NULL
            DO NOTHING
            """,
            [
                (
                    review_id,
                    candidate.ingredient_id,
                    candidate.candidate_method,
                    candidate.candidate_confidence,
                    candidate.rationale,
                    False,
                )
                for candidate in candidates
            ],
        )

    def candidate_count(self, cursor, review_id):
        cursor.execute(
            "SELECT count(*) FROM ingredient_mapping_review_candidates WHERE review_id = %s",
            (review_id,),
        )
        return cursor.fetchone()["count"]

    def apply_deterministic_resolution(
        self, cursor, product_ingredient_id, review_id, ingredient_id,
        resolution_provenance,
    ):
        cursor.execute(
            """
            UPDATE ingredient_mapping_review_candidates SET is_selected = TRUE
            WHERE review_id = %s AND ingredient_id = %s AND is_selected = FALSE
            RETURNING id
            """,
            (review_id, ingredient_id),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("deterministic resolution candidate is not persisted")

        provenance_json = json.dumps(resolution_provenance)
        cursor.execute(
            """
            UPDATE ingredient_mapping_reviews
            SET review_status = 'accepted', reviewed_at = NOW(), reviewed_by = NULL,
                review_provenance = COALESCE(review_provenance, '{}'::jsonb) || %s::jsonb
            WHERE id = %s AND product_ingredient_id = %s AND review_status = 'pending'
            RETURNING id
            """,
            (provenance_json, review_id, product_ingredient_id),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("pending mapping review could not be auto-accepted")

        cursor.execute(
            """
            UPDATE product_ingredients
            SET ingredient_id = %s, mapping_status = 'accepted',
                mapping_method = 'deterministic_alias',
                mapping_provenance = COALESCE(mapping_provenance, '{}'::jsonb) || %s::jsonb
            WHERE id = %s AND ingredient_id IS NULL AND mapping_status = 'needs_review'
            RETURNING id
            """,
            (ingredient_id, provenance_json, product_ingredient_id),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("product ingredient could not be auto-resolved")
