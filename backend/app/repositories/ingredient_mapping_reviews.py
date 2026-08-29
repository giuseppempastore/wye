"""Read and decide persisted human ingredient mapping reviews."""

import json


class PostgresIngredientMappingReviewRepository:
    def lock_alias_approval_source(self, cursor, review_id):
        cursor.execute(
            """
            SELECT r.id AS review_id, r.review_status,
                   r.product_ingredient_id, pi.raw_name,
                   pi.normalized_text, pi.detected_language,
                   pi.label_extraction_item_id, pi.ingredient_id,
                   i.status AS ingredient_status,
                   (SELECT count(*)
                    FROM ingredient_mapping_review_candidates c
                    WHERE c.review_id = r.id AND c.is_selected) AS selected_count,
                   (SELECT c.ingredient_id
                    FROM ingredient_mapping_review_candidates c
                    WHERE c.review_id = r.id AND c.is_selected
                    LIMIT 1) AS selected_ingredient_id
            FROM ingredient_mapping_reviews r
            JOIN product_ingredients pi ON pi.id = r.product_ingredient_id
            LEFT JOIN ingredients i ON i.id = pi.ingredient_id
            WHERE r.id = %s
            FOR UPDATE OF r, pi
            """,
            (review_id,),
        )
        return cursor.fetchone()

    def lock_aliases(self, cursor, normalized_alias, language):
        cursor.execute(
            """
            SELECT id, ingredient_id, alias_name, normalized_alias, language,
                   alias_type, confidence, is_primary, mapping_method,
                   mapping_status, approved_at, review_provenance, created_at
            FROM ingredient_aliases
            WHERE normalized_alias = %s AND language = %s
            ORDER BY id
            FOR UPDATE
            """,
            (normalized_alias, language),
        )
        return cursor.fetchall()

    def insert_approved_alias(
        self, cursor, ingredient_id, alias_name, normalized_alias, language,
        provenance,
    ):
        provenance_json = json.dumps(provenance)
        cursor.execute(
            """
            INSERT INTO ingredient_aliases (
                ingredient_id, alias_name, normalized_alias, language,
                alias_type, confidence, is_primary, mapping_method,
                mapping_status, approved_at, review_provenance
            )
            VALUES (
                %s, %s, %s, %s, 'synonym', 1.0, FALSE, 'manual_review',
                'accepted', NOW(), %s::jsonb
            )
            ON CONFLICT (normalized_alias, language)
                WHERE mapping_status = 'accepted'
            DO NOTHING
            RETURNING id, ingredient_id, alias_name, normalized_alias, language,
                      alias_type, confidence, is_primary, mapping_method,
                      mapping_status, approved_at, review_provenance, created_at
            """,
            (
                ingredient_id, alias_name, normalized_alias, language,
                provenance_json,
            ),
        )
        return cursor.fetchone()

    def list_reviews(self, cursor, status):
        cursor.execute(
            """
            SELECT r.id AS review_id, r.product_ingredient_id, pi.product_id,
                   r.raw_text, r.normalized_text, r.detected_language,
                   r.review_status, r.created_at,
                   count(c.id) AS candidate_count
            FROM ingredient_mapping_reviews r
            JOIN product_ingredients pi ON pi.id = r.product_ingredient_id
            LEFT JOIN ingredient_mapping_review_candidates c ON c.review_id = r.id
            WHERE r.review_status = %s
            GROUP BY r.id, pi.id
            ORDER BY r.created_at, r.id
            """,
            (status,),
        )
        return cursor.fetchall()

    def review_detail(self, cursor, review_id):
        cursor.execute(
            """
            SELECT r.id AS review_id, r.review_status, r.requested_by_method,
                   r.review_provenance, r.created_at, r.reviewed_at,
                   r.reviewed_by, r.product_ingredient_id, pi.product_id,
                   pi.raw_name, pi.normalized_text, pi.detected_language,
                   pi.position_in_list, pi.mapping_status, pi.ingredient_id,
                   pi.mapping_provenance
            FROM ingredient_mapping_reviews r
            JOIN product_ingredients pi ON pi.id = r.product_ingredient_id
            WHERE r.id = %s
            """,
            (review_id,),
        )
        review = cursor.fetchone()
        if review is None:
            return None
        cursor.execute(
            """
            SELECT c.id AS candidate_id, c.ingredient_id, i.canonical_name,
                   c.candidate_method, c.candidate_confidence,
                   c.rationale, c.is_selected
            FROM ingredient_mapping_review_candidates c
            JOIN ingredients i ON i.id = c.ingredient_id
            WHERE c.review_id = %s AND c.ingredient_id IS NOT NULL
            ORDER BY c.is_selected DESC,
                     c.candidate_confidence DESC NULLS LAST,
                     i.canonical_name, c.ingredient_id, c.id
            """,
            (review_id,),
        )
        return review, cursor.fetchall()

    def lock_review(self, cursor, review_id):
        cursor.execute(
            """
            SELECT r.id AS review_id, r.review_status, r.product_ingredient_id,
                   pi.product_id, pi.mapping_status, pi.ingredient_id
            FROM ingredient_mapping_reviews r
            JOIN product_ingredients pi ON pi.id = r.product_ingredient_id
            WHERE r.id = %s
            FOR UPDATE OF r, pi
            """,
            (review_id,),
        )
        return cursor.fetchone()

    def lock_candidate(self, cursor, review_id, candidate_id):
        cursor.execute(
            """
            SELECT c.id AS candidate_id, c.ingredient_id
            FROM ingredient_mapping_review_candidates c
            JOIN ingredients i ON i.id = c.ingredient_id
            WHERE c.id = %s AND c.review_id = %s
              AND c.ingredient_id IS NOT NULL AND c.substance_id IS NULL
            FOR UPDATE OF c
            """,
            (candidate_id, review_id),
        )
        return cursor.fetchone()

    def apply_decision(
        self, cursor, review, decision, candidate, provenance
    ):
        review_id = review["review_id"]
        product_ingredient_id = review["product_ingredient_id"]
        cursor.execute(
            "UPDATE ingredient_mapping_review_candidates "
            "SET is_selected = FALSE WHERE review_id = %s",
            (review_id,),
        )
        ingredient_id = None
        if decision == "accepted":
            ingredient_id = candidate["ingredient_id"]
            cursor.execute(
                """
                UPDATE ingredient_mapping_review_candidates
                SET is_selected = TRUE
                WHERE id = %s AND review_id = %s
                RETURNING id
                """,
                (candidate["candidate_id"], review_id),
            )
            if cursor.fetchone() is None:
                raise RuntimeError("selected review candidate disappeared")

        provenance_json = json.dumps(provenance)
        cursor.execute(
            """
            UPDATE ingredient_mapping_reviews
            SET review_status = %s, reviewed_at = NOW(), reviewed_by = NULL,
                review_provenance = COALESCE(review_provenance, '{}'::jsonb)
                    || %s::jsonb
            WHERE id = %s AND review_status = 'pending'
            RETURNING id
            """,
            (decision, provenance_json, review_id),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("pending review decision lost its lock")

        cursor.execute(
            """
            UPDATE product_ingredients
            SET ingredient_id = %s, mapping_status = %s,
                mapping_method = 'manual_review',
                mapping_provenance = COALESCE(mapping_provenance, '{}'::jsonb)
                    || %s::jsonb
            WHERE id = %s
            RETURNING id
            """,
            (ingredient_id, decision, provenance_json, product_ingredient_id),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("review product ingredient disappeared")
