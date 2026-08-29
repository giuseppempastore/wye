"""Read-only PostgreSQL access to the structured substance identifier registry."""

from dataclasses import dataclass

from psycopg2.extras import Json


@dataclass(frozen=True)
class SubstanceIdentifierLookup:
    namespace_key: str
    namespace_version: str
    normalized_value: str
    namespace_id: int | None
    identifier_id: int | None
    identifier_status: str | None
    substance_id: int | None
    substance_status: str | None


class PostgresSubstanceRegistryRepository:
    """Batch-resolve structured identifiers without mutating registry state."""

    def lookup_identifiers(self, cursor, identifiers):
        requests = [
            {
                "ordinal": ordinal,
                "namespace_key": item.namespace_key,
                "namespace_version": item.namespace_version,
                "normalized_value": item.normalized_value,
            }
            for ordinal, item in enumerate(identifiers)
        ]
        cursor.execute(
            """
            WITH requested AS (
                SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(
                    ordinal integer,
                    namespace_key text,
                    namespace_version text,
                    normalized_value text
                )
            )
            SELECT r.namespace_key,r.namespace_version,r.normalized_value,
                   n.id AS namespace_id,i.id AS identifier_id,
                   i.verification_status AS identifier_status,
                   i.substance_id,s.status AS substance_status
            FROM requested r
            LEFT JOIN substance_identifier_namespaces n
              ON n.namespace_key=r.namespace_key
             AND n.namespace_version=r.namespace_version
            LEFT JOIN substance_identifiers i
              ON i.namespace_id=n.id
             AND i.normalized_value=r.normalized_value
            LEFT JOIN substances s ON s.id=i.substance_id
            ORDER BY r.ordinal
            """,
            (Json(requests),),
        )
        return tuple(SubstanceIdentifierLookup(**row) for row in cursor.fetchall())
