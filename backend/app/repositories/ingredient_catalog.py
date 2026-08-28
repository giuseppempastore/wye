"""Read-only access to the canonical ingredient and alias catalog."""

from dataclasses import dataclass
from typing import Callable, Protocol

from app.db import get_connection


@dataclass(frozen=True)
class CatalogIngredient:
    ingredient_id: int
    canonical_name: str
    status: str


@dataclass(frozen=True)
class CatalogAlias:
    ingredient_id: int
    normalized_alias: str
    language: str
    mapping_status: str


@dataclass(frozen=True)
class IngredientCatalog:
    ingredients: tuple[CatalogIngredient, ...]
    aliases: tuple[CatalogAlias, ...]


class IngredientCatalogRepository(Protocol):
    def load_catalog(self) -> IngredientCatalog: ...


class PostgresIngredientCatalogRepository:
    """Load the candidate catalog in two bulk queries, without N+1 access."""

    def __init__(self, connection_factory: Callable = get_connection):
        self.connection_factory = connection_factory

    def load_catalog(self) -> IngredientCatalog:
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, canonical_name, status FROM ingredients ORDER BY id"
                )
                ingredients = tuple(
                    CatalogIngredient(row[0], row[1], row[2])
                    for row in cursor.fetchall()
                )
                cursor.execute(
                    "SELECT ingredient_id, normalized_alias, language, mapping_status "
                    "FROM ingredient_aliases ORDER BY id"
                )
                aliases = tuple(
                    CatalogAlias(row[0], row[1], row[2], row[3])
                    for row in cursor.fetchall()
                )
            return IngredientCatalog(ingredients=ingredients, aliases=aliases)
        finally:
            connection.close()
