"""Orchestrate extraction-item materialization and mapping review creation."""

from dataclasses import dataclass
from typing import Callable

import psycopg2.extras

from app.db import get_connection
from app.repositories.ingredient_catalog import PostgresIngredientCatalogRepository
from app.repositories.ingredient_mappings import PostgresIngredientMappingRepository
from app.services.ingredient_candidates import (
    FUZZY_SIMILARITY_THRESHOLD,
    MAX_CANDIDATES,
    IngredientCandidateGenerator,
)
from app.services.deterministic_ingredient_resolver import (
    DeterministicIngredientResolver,
)
from app.services.ingredient_normalizer import IngredientNormalizer


INGREDIENT_CANDIDATE_GENERATION_VERSION = "ingredient_candidate_generation_v1"
DETERMINISTIC_RESOLUTION_VERSION = "ingredient_deterministic_resolution_v1"


class IngredientMappingError(RuntimeError):
    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


@dataclass(frozen=True)
class MaterializedIngredientMapping:
    label_extraction_item_id: int
    product_ingredient_id: int
    review_id: int
    review_status: str
    candidate_count: int
    created: bool


@dataclass(frozen=True)
class IngredientMappingRunResult:
    product_id: int
    extraction_run_id: int
    mappings: tuple[MaterializedIngredientMapping, ...]


class _RunCatalogCache:
    def __init__(self, repository):
        self.repository = repository
        self.catalog = None

    def load_catalog(self):
        if self.catalog is None:
            self.catalog = self.repository.load_catalog()
        return self.catalog


class IngredientMappingService:
    """Persist one extraction run atomically without deciding any mapping."""

    def __init__(
        self,
        normalizer=None,
        candidate_generator=None,
        resolver=None,
        mapping_repository=None,
        connection_factory: Callable = get_connection,
    ):
        self.normalizer = normalizer or IngredientNormalizer()
        self.candidate_generator = candidate_generator or IngredientCandidateGenerator(
            PostgresIngredientCatalogRepository(connection_factory)
        )
        self.resolver = resolver or DeterministicIngredientResolver()
        self.mapping_repository = (
            mapping_repository or PostgresIngredientMappingRepository()
        )
        self.connection_factory = connection_factory

    def map_run(self, product_id: int, extraction_run_id: int):
        connection = self.connection_factory()
        try:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                run = self.mapping_repository.load_run(cursor, extraction_run_id)
                self._validate_run(run, product_id)

                normalized = [
                    self.normalizer.normalize(item.raw_text) for item in run.items
                ]
                generator = self._run_scoped_generator()
                mappings = []
                for item, normalization in zip(run.items, normalized):
                    provenance = self._provenance(item, normalization)
                    product_ingredient, created = (
                        self.mapping_repository.get_or_create_product_ingredient(
                            cursor,
                            product_id,
                            item,
                            normalization.normalized_text,
                            provenance,
                        )
                    )
                    if product_ingredient is None:
                        raise RuntimeError("product ingredient conflict could not be resolved")
                    if product_ingredient.get("product_id", product_id) != product_id:
                        raise IngredientMappingError(
                            "mapping_ownership_conflict",
                            "Extraction item is already mapped to another product",
                            409,
                        )

                    review = self.mapping_repository.latest_review(
                        cursor, product_ingredient["id"]
                    )
                    review_created = False
                    if review is None:
                        candidates = generator.generate(
                            normalization.normalized_text,
                            item.detected_language,
                        )
                        review, review_created = (
                            self.mapping_repository.create_pending_review(
                                cursor,
                                product_ingredient["id"],
                                item,
                                normalization.normalized_text,
                                provenance,
                            )
                        )
                    if review is None:
                        raise RuntimeError("pending review conflict could not be resolved")

                    if review_created:
                        self.mapping_repository.insert_candidates(
                            cursor, review["id"], candidates.candidates
                        )
                        resolution = self.resolver.resolve(candidates.candidates)
                        if resolution.resolved:
                            resolution_provenance = {
                                "resolution_type": "deterministic_auto",
                                "resolution_version": DETERMINISTIC_RESOLUTION_VERSION,
                                "resolution_reason": resolution.reason,
                                "resolved_ingredient_id": resolution.ingredient_id,
                            }
                            self.mapping_repository.apply_deterministic_resolution(
                                cursor,
                                product_ingredient["id"],
                                review["id"],
                                resolution.ingredient_id,
                                resolution_provenance,
                            )
                            review["review_status"] = "accepted"
                    candidate_count = self.mapping_repository.candidate_count(
                        cursor, review["id"]
                    )
                    mappings.append(
                        MaterializedIngredientMapping(
                            label_extraction_item_id=item.item_id,
                            product_ingredient_id=product_ingredient["id"],
                            review_id=review["id"],
                            review_status=review["review_status"],
                            candidate_count=candidate_count,
                            created=created,
                        )
                    )
            connection.commit()
            return IngredientMappingRunResult(
                product_id=product_id,
                extraction_run_id=extraction_run_id,
                mappings=tuple(mappings),
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _run_scoped_generator(self):
        generator = self.candidate_generator
        if not isinstance(generator, IngredientCandidateGenerator):
            return generator
        return IngredientCandidateGenerator(
            _RunCatalogCache(generator.repository),
            normalizer=generator.normalizer,
            max_candidates=generator.max_candidates,
            fuzzy_threshold=generator.fuzzy_threshold,
        )

    @staticmethod
    def _validate_run(run, product_id):
        if run is None:
            raise IngredientMappingError(
                "extraction_not_found", "Ingredient extraction run not found", 404
            )
        if run.product_id != product_id:
            raise IngredientMappingError(
                "extraction_not_found", "Ingredient extraction run not found", 404
            )
        if run.run_status != "succeeded":
            raise IngredientMappingError(
                "extraction_not_mappable",
                "Only succeeded extraction runs can be mapped",
                409,
            )
        if run.document_type != "ingredients" or run.image_type != "ingredients":
            raise IngredientMappingError(
                "extraction_not_mappable",
                "Only ingredient extraction runs can be mapped",
                422,
            )

    @staticmethod
    def _provenance(item, normalization):
        provenance = {
            "label_extraction_item_id": item.item_id,
            "normalization_version": normalization.normalization_version,
            "candidate_generation_version": INGREDIENT_CANDIDATE_GENERATION_VERSION,
            "candidate_generation_config": {
                "fuzzy_threshold": FUZZY_SIMILARITY_THRESHOLD,
                "max_candidates": MAX_CANDIDATES,
            },
        }
        quantity = (item.structured_value or {}).get("quantity")
        if quantity is not None:
            provenance["extracted_quantity"] = quantity
        return provenance


