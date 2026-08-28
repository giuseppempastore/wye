"""Deterministic canonical ingredient candidate generation."""

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from app.repositories.ingredient_catalog import IngredientCatalogRepository
from app.services.ingredient_normalizer import IngredientNormalizer


MAX_CANDIDATES = 5
FUZZY_SIMILARITY_THRESHOLD = 0.86

MatchType = Literal[
    "exact_canonical",
    "exact_accepted_alias",
    "fuzzy_canonical",
    "fuzzy_accepted_alias",
]

_MATCH_PRIORITY: dict[MatchType, int] = {
    "exact_canonical": 4,
    "exact_accepted_alias": 4,
    "fuzzy_canonical": 2,
    "fuzzy_accepted_alias": 1,
}
_RATIONALE: dict[MatchType, str] = {
    "exact_canonical": "exact canonical normalized match",
    "exact_accepted_alias": "exact accepted alias match",
    "fuzzy_canonical": "fuzzy canonical name similarity",
    "fuzzy_accepted_alias": "fuzzy accepted alias similarity",
}


@dataclass(frozen=True)
class IngredientCandidate:
    ingredient_id: int
    canonical_name: str
    candidate_method: str
    candidate_confidence: float
    rationale: str
    match_type: MatchType


@dataclass(frozen=True)
class CandidateGenerationResult:
    normalized_text: str
    candidates: tuple[IngredientCandidate, ...]


@dataclass(frozen=True)
class _Evidence:
    candidate: IngredientCandidate
    language_match: int


class IngredientCandidateGenerator:
    """Generate, rank, and deduplicate read-only catalog candidates.

    Fuzzy confidence is ``SequenceMatcher.ratio() * 0.95``. Exact matches use
    1.0, keeping every fuzzy result strictly below exact evidence.
    """

    def __init__(
        self,
        repository: IngredientCatalogRepository,
        normalizer: IngredientNormalizer | None = None,
        max_candidates: int = MAX_CANDIDATES,
        fuzzy_threshold: float = FUZZY_SIMILARITY_THRESHOLD,
    ):
        if max_candidates < 1:
            raise ValueError("max_candidates must be at least 1")
        if not 0.0 <= fuzzy_threshold <= 1.0:
            raise ValueError("fuzzy_threshold must be between 0 and 1")
        self.repository = repository
        self.normalizer = normalizer or IngredientNormalizer()
        self.max_candidates = max_candidates
        self.fuzzy_threshold = fuzzy_threshold

    def generate(
        self, normalized_text: str, detected_language: str | None = None
    ) -> CandidateGenerationResult:
        query = self.normalizer.normalize(normalized_text).normalized_text
        language = detected_language.casefold() if detected_language else None
        catalog = self.repository.load_catalog()

        active = {
            item.ingredient_id: item
            for item in catalog.ingredients
            if item.status == "active"
        }
        normalized_names = {}
        for ingredient_id, item in active.items():
            try:
                normalized_names[ingredient_id] = self.normalizer.normalize(
                    item.canonical_name
                ).normalized_text
            except (TypeError, ValueError):
                continue

        evidence: list[_Evidence] = []
        for ingredient_id, canonical_normalized in normalized_names.items():
            if query == canonical_normalized:
                evidence.append(
                    self._evidence(active[ingredient_id], "exact_canonical", 1.0)
                )
            else:
                similarity = SequenceMatcher(
                    None, query, canonical_normalized, autojunk=False
                ).ratio()
                if similarity >= self.fuzzy_threshold:
                    evidence.append(
                        self._evidence(
                            active[ingredient_id],
                            "fuzzy_canonical",
                            round(similarity * 0.95, 3),
                        )
                    )

        for alias in catalog.aliases:
            if alias.mapping_status != "accepted" or alias.ingredient_id not in active:
                continue
            try:
                alias_normalized = self.normalizer.normalize(
                    alias.normalized_alias
                ).normalized_text
            except (TypeError, ValueError):
                continue
            language_match = int(
                language is not None and alias.language.casefold() == language
            )
            if query == alias_normalized:
                evidence.append(
                    self._evidence(
                        active[alias.ingredient_id],
                        "exact_accepted_alias",
                        1.0,
                        language_match,
                    )
                )
            else:
                similarity = SequenceMatcher(
                    None, query, alias_normalized, autojunk=False
                ).ratio()
                if similarity >= self.fuzzy_threshold:
                    evidence.append(
                        self._evidence(
                            active[alias.ingredient_id],
                            "fuzzy_accepted_alias",
                            round(similarity * 0.95, 3),
                            language_match,
                        )
                    )

        best_by_ingredient: dict[int, _Evidence] = {}
        for item in evidence:
            current = best_by_ingredient.get(item.candidate.ingredient_id)
            if current is None or self._evidence_key(item) > self._evidence_key(current):
                best_by_ingredient[item.candidate.ingredient_id] = item

        ordered = sorted(best_by_ingredient.values(), key=self._sort_key)
        return CandidateGenerationResult(
            normalized_text=query,
            candidates=tuple(item.candidate for item in ordered[: self.max_candidates]),
        )

    @staticmethod
    def _evidence(ingredient, match_type, confidence, language_match=0):
        return _Evidence(
            candidate=IngredientCandidate(
                ingredient_id=ingredient.ingredient_id,
                canonical_name=ingredient.canonical_name,
                candidate_method="deterministic",
                candidate_confidence=confidence,
                rationale=_RATIONALE[match_type],
                match_type=match_type,
            ),
            language_match=language_match,
        )

    @staticmethod
    def _evidence_key(item: _Evidence):
        candidate = item.candidate
        return (
            candidate.candidate_confidence,
            _MATCH_PRIORITY[candidate.match_type],
            item.language_match,
            candidate.match_type == "exact_canonical",
        )

    def _sort_key(self, item: _Evidence):
        candidate = item.candidate
        canonical_normalized = self.normalizer.normalize(
            candidate.canonical_name
        ).normalized_text
        return (
            -candidate.candidate_confidence,
            -_MATCH_PRIORITY[candidate.match_type],
            -item.language_match,
            canonical_normalized,
            candidate.ingredient_id,
        )
