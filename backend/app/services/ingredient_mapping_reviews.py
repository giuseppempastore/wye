"""Transactional human decisions over persisted ingredient mapping reviews."""

from typing import Callable

import psycopg2.extras

from app.db import get_connection
from app.repositories.ingredient_mapping_reviews import (
    PostgresIngredientMappingReviewRepository,
)
from app.services.ingredient_normalizer import (
    INGREDIENT_NORMALIZATION_VERSION,
    IngredientNormalizer,
)


HUMAN_REVIEW_VERSION = "ingredient_human_review_v1"


class IngredientMappingReviewError(RuntimeError):
    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class IngredientMappingReviewService:
    def __init__(
        self,
        repository=None,
        connection_factory: Callable = get_connection,
        normalizer=None,
    ):
        self.repository = repository or PostgresIngredientMappingReviewRepository()
        self.connection_factory = connection_factory
        self.normalizer = normalizer or IngredientNormalizer()

    @staticmethod
    def _alias_result(alias, created):
        return {"alias": dict(alias), "created": created}

    def approve_alias(self, review_id):
        connection = self.connection_factory()
        try:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                source = self.repository.lock_alias_approval_source(
                    cursor, review_id
                )
                if source is None:
                    raise IngredientMappingReviewError(
                        "review_not_found", "Ingredient mapping review not found", 404
                    )
                if source["review_status"] != "accepted":
                    raise IngredientMappingReviewError(
                        "review_not_accepted",
                        "Only an accepted review can approve an alias",
                        409,
                    )
                if (
                    source["ingredient_id"] is None
                    or source["ingredient_status"] != "active"
                    or source["selected_count"] != 1
                    or source["selected_ingredient_id"] != source["ingredient_id"]
                ):
                    raise IngredientMappingReviewError(
                        "inconsistent_accepted_review",
                        "Accepted review has no coherent canonical ingredient",
                        409,
                    )
                raw_name = source["raw_name"]
                normalized_alias = source["normalized_text"]
                language = source["detected_language"]
                if not normalized_alias or not normalized_alias.strip():
                    raise IngredientMappingReviewError(
                        "normalized_alias_missing",
                        "Accepted mapping has no normalized ingredient text",
                        422,
                    )
                if not language or not language.strip():
                    raise IngredientMappingReviewError(
                        "alias_language_missing",
                        "Detected language is required to approve an alias",
                        422,
                    )
                try:
                    recomputed = self.normalizer.normalize(raw_name)
                except (TypeError, ValueError) as exc:
                    raise IngredientMappingReviewError(
                        "alias_text_invalid", str(exc), 422
                    ) from exc
                if recomputed.normalized_text != normalized_alias:
                    raise IngredientMappingReviewError(
                        "normalization_mismatch",
                        "Persisted normalized text does not match normalization v1",
                        409,
                    )

                existing = self.repository.lock_aliases(
                    cursor, normalized_alias, language
                )
                if existing:
                    accepted = [
                        alias for alias in existing
                        if alias["mapping_status"] == "accepted"
                    ]
                    nonaccepted = [
                        alias for alias in existing
                        if alias["mapping_status"] != "accepted"
                    ]
                    if nonaccepted:
                        raise IngredientMappingReviewError(
                            "alias_historical_collision",
                            "A deprecated or legacy alias already uses this text and language",
                            409,
                        )
                    if (
                        len(accepted) == 1
                        and accepted[0]["ingredient_id"] == source["ingredient_id"]
                    ):
                        connection.commit()
                        return self._alias_result(accepted[0], False)
                    raise IngredientMappingReviewError(
                        "alias_collision",
                        "Accepted alias already maps this text and language elsewhere",
                        409,
                    )

                provenance = {
                    "source": "human_mapping_review",
                    "review_id": source["review_id"],
                    "product_ingredient_id": source["product_ingredient_id"],
                    "label_extraction_item_id": source[
                        "label_extraction_item_id"
                    ],
                    "normalization_version": INGREDIENT_NORMALIZATION_VERSION,
                }
                alias = self.repository.insert_approved_alias(
                    cursor,
                    source["ingredient_id"],
                    raw_name,
                    normalized_alias,
                    language,
                    provenance,
                )
                if alias is None:
                    concurrent = self.repository.lock_aliases(
                        cursor, normalized_alias, language
                    )
                    if (
                        len(concurrent) == 1
                        and concurrent[0]["mapping_status"] == "accepted"
                        and concurrent[0]["ingredient_id"] == source["ingredient_id"]
                    ):
                        connection.commit()
                        return self._alias_result(concurrent[0], False)
                    raise IngredientMappingReviewError(
                        "alias_collision",
                        "Accepted alias was concurrently assigned elsewhere",
                        409,
                    )
            connection.commit()
            return self._alias_result(alias, True)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list(self, status="pending"):
        connection = self.connection_factory()
        try:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                rows = self.repository.list_reviews(cursor, status)
                return {"reviews": [dict(row) for row in rows]}
        finally:
            connection.close()

    def detail(self, review_id):
        connection = self.connection_factory()
        try:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                result = self.repository.review_detail(cursor, review_id)
                if result is None:
                    raise IngredientMappingReviewError(
                        "review_not_found", "Ingredient mapping review not found", 404
                    )
                review, candidates = result
                review = dict(review)
                mapping_provenance = review.pop("mapping_provenance") or {}
                product_ingredient = {
                    "id": review.pop("product_ingredient_id"),
                    "product_id": review.pop("product_id"),
                    "raw_name": review.pop("raw_name"),
                    "normalized_text": review.pop("normalized_text"),
                    "detected_language": review.pop("detected_language"),
                    "position_in_list": review.pop("position_in_list"),
                    "mapping_status": review.pop("mapping_status"),
                    "ingredient_id": review.pop("ingredient_id"),
                    "extracted_quantity": mapping_provenance.get(
                        "extracted_quantity"
                    ),
                }
                return {
                    "review": review,
                    "product_ingredient": product_ingredient,
                    "candidates": [dict(candidate) for candidate in candidates],
                }
        finally:
            connection.close()

    def decide(self, review_id, status, candidate_id=None):
        if status not in {"accepted", "ambiguous", "rejected"}:
            raise IngredientMappingReviewError(
                "invalid_decision", "Unsupported review decision", 422
            )
        if status == "accepted" and candidate_id is None:
            raise IngredientMappingReviewError(
                "candidate_required",
                "candidate_id is required for accepted decisions",
                422,
            )
        if status != "accepted" and candidate_id is not None:
            raise IngredientMappingReviewError(
                "candidate_not_allowed",
                "candidate_id is only allowed for accepted decisions",
                422,
            )
        connection = self.connection_factory()
        try:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                review = self.repository.lock_review(cursor, review_id)
                if review is None:
                    raise IngredientMappingReviewError(
                        "review_not_found", "Ingredient mapping review not found", 404
                    )
                if review["review_status"] != "pending":
                    raise IngredientMappingReviewError(
                        "review_already_decided",
                        "Ingredient mapping review is already terminal",
                        409,
                    )

                candidate = None
                if status == "accepted":
                    candidate = self.repository.lock_candidate(
                        cursor, review_id, candidate_id
                    )
                    if candidate is None:
                        raise IngredientMappingReviewError(
                            "candidate_not_found",
                            "Candidate does not belong to this review",
                            404,
                        )

                provenance = {
                    "resolution_type": "human_review",
                    "resolution_version": HUMAN_REVIEW_VERSION,
                    "decision": status,
                }
                if candidate is not None:
                    provenance.update(
                        {
                            "selected_candidate_id": candidate["candidate_id"],
                            "resolved_ingredient_id": candidate["ingredient_id"],
                        }
                    )
                self.repository.apply_decision(
                    cursor, review, status, candidate, provenance
                )
            connection.commit()
            return self.detail(review_id)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
