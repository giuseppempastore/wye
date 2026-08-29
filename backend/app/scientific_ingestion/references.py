"""Canonical provider references that never derive from internal WYE keys."""

import re
from urllib.parse import quote


def canonical_doi_url(value: str) -> str:
    """Validate a provider DOI and produce its canonical resolver URL."""
    if not isinstance(value, str) or not re.fullmatch(
        r"10\.\d{4,9}/[^\s/]+(?:/[^\s/]+)*", value
    ):
        raise ValueError("record DOI is missing or malformed")
    return "https://doi.org/" + quote(value, safe="/:._-()")


def canonical_source_doi_url(value: str) -> str:
    """Accept the explicit `doi:` form used by IUCLID source metadata."""
    if not isinstance(value, str) or not value.lower().startswith("doi:"):
        raise ValueError("provider document reference is not an explicit DOI")
    return canonical_doi_url(value[4:].strip())
