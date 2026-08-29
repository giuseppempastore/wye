"""Pure, deterministic normalization of ingredient label text.

Version ``ingredient_normalization_v1`` performs syntax-only normalization. It
does not translate, resolve aliases, query the database, or select a canonical
ingredient.
"""

from dataclasses import dataclass
import re
import unicodedata


INGREDIENT_NORMALIZATION_VERSION = "ingredient_normalization_v1"

_APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "\u02bc": "'",  # modifier letter apostrophe
        "\u2018": "'",  # left single quotation mark
        "\u2019": "'",  # right single quotation mark
        "\uff07": "'",  # fullwidth apostrophe
    }
)
_DASH_TRANSLATION = str.maketrans(
    {
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\ufe63": "-",  # small hyphen-minus
        "\uff0d": "-",  # fullwidth hyphen-minus
    }
)
_WHITESPACE_RE = re.compile(r"\s+")
_E_NUMBER_RE = re.compile(r"(?<!\w)e[\s-]*(\d{3,4})[\s-]*([a-z])?(?!\w)")


@dataclass(frozen=True)
class NormalizationResult:
    raw_text: str
    normalized_text: str
    normalization_version: str


class IngredientNormalizer:
    """Normalize one ingredient string without interpreting its meaning."""

    version = INGREDIENT_NORMALIZATION_VERSION

    def normalize(self, text: str) -> NormalizationResult:
        """Return the v1 normalized form, rejecting missing or blank inputs."""
        if text is None:
            raise ValueError("ingredient text must not be None")
        if not isinstance(text, str):
            raise TypeError("ingredient text must be a string")

        normalized = unicodedata.normalize("NFC", text)
        normalized = normalized.translate(_APOSTROPHE_TRANSLATION)
        normalized = normalized.translate(_DASH_TRANSLATION)
        normalized = normalized.casefold()
        normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
        if not normalized:
            raise ValueError("ingredient text must not be empty")

        normalized = _E_NUMBER_RE.sub(
            lambda match: f"e{match.group(1)}{match.group(2) or ''}",
            normalized,
        )
        return NormalizationResult(
            raw_text=text,
            normalized_text=normalized,
            normalization_version=self.version,
        )
