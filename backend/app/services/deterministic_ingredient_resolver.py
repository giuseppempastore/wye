"""Pure decision logic for conservative deterministic ingredient resolution."""

from dataclasses import dataclass
from typing import Iterable

from app.services.ingredient_candidates import IngredientCandidate


EXACT_MATCH_TYPES = frozenset({"exact_canonical", "exact_accepted_alias"})


@dataclass(frozen=True)
class DeterministicResolutionResult:
    resolved: bool
    ingredient_id: int | None = None
    reason: str | None = None


class DeterministicIngredientResolver:
    """Resolve only one unique canonical ingredient supported by exact evidence."""

    def resolve(
        self, candidates: Iterable[IngredientCandidate]
    ) -> DeterministicResolutionResult:
        exact_by_ingredient: dict[int, set[str]] = {}
        for candidate in candidates:
            if candidate.match_type not in EXACT_MATCH_TYPES:
                continue
            exact_by_ingredient.setdefault(candidate.ingredient_id, set()).add(
                candidate.match_type
            )

        if len(exact_by_ingredient) != 1:
            return DeterministicResolutionResult(resolved=False)

        ingredient_id, evidence = next(iter(exact_by_ingredient.items()))
        reason = (
            "exact_canonical"
            if "exact_canonical" in evidence
            else "exact_accepted_alias"
        )
        return DeterministicResolutionResult(
            resolved=True,
            ingredient_id=ingredient_id,
            reason=reason,
        )
