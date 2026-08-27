"""Verify and adopt an existing pre-Alembic Wye database without changing Wye data."""

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from alembic import command
from alembic.config import Config
from app.db import get_connection

REVISION = "0001_initial_schema"
EXPECTED_COLUMNS = {
    "products": "id barcode gtin brand_name product_name category product_type source verified version status image_url ingredient_image_url nutrition_image_url created_at updated_at",
    "ingredients": "id canonical_name ingredient_group risk_level allergen_flag evidence_level cas_number einecs_number common_name status created_at updated_at",
    "ingredient_aliases": "id ingredient_id alias_name normalized_alias language alias_type confidence is_primary created_at",
    "ingredient_categories": "id ingredient_id category_name classification_source created_at",
    "ingredient_risk_profiles": "id ingredient_id risk_level hazard_type evidence_level adverse_risk_note noael adi dose_threshold_low dose_threshold_high population_at_risk review_status updated_at",
    "allergens": "id allergen_name canonical_code category description is_active created_at",
    "ingredient_allergens": "id ingredient_id allergen_id relationship_type confidence notes created_at",
    "sources": "id source_name source_type url authority_level country is_authoritative created_at",
    "ingredient_evidence": "id ingredient_id source_id evidence_title evidence_summary risk_statement evidence_level url publication_date created_at",
    "product_ingredients": "id product_id ingredient_id raw_name canonical_name position_in_list confidence allergen_flag risky_flag is_unknown manual_override created_at",
    "nutrition_facts": "id product_id serving_size energy_kcal protein_g carbs_g sugar_g fat_g saturated_fat_g sodium_mg fiber_g source declared_by_manufacturer verified raw_text created_at updated_at",
    "nutrition_thresholds": "id category nutrient_name threshold_low threshold_medium threshold_high unit source_reference valid_from valid_to created_at",
    "product_scores": "id product_id ingredient_score nutrition_score final_score score_band ingredient_risk_summary nutrition_summary final_summary calculation_version generated_at",
    "cosmetics_products": "id barcode brand product_name product_type ingredient_list_raw ingredients_mapped ingredient_score final_score verified created_at updated_at",
    "cosmetic_ingredient_assessment": "id cosmetic_product_id ingredient_id risk_level reason confidence created_at",
    "users": "id email auth_provider is_premium created_at",
    "user_profiles": "id user_id age height_cm weight_kg bmi allergies_raw health_conditions_raw diet_type activity_level goal_type created_at updated_at",
    "user_allergies": "id user_id allergen_id severity notes",
    "product_reviews": "id product_id submitted_by_user_id review_status source_type reason created_at",
}
EXPECTED_COLUMNS = {table: set(columns.split()) for table, columns in EXPECTED_COLUMNS.items()}
EXPECTED_INDEXES = {
    "idx_products_barcode", "idx_products_category", "idx_ingredients_canonical_name",
    "idx_ingredient_aliases_normalized", "idx_product_ingredients_product_id",
    "idx_nutrition_facts_product_id", "idx_product_scores_product_id", "idx_users_email",
    "idx_allergens_name",
}


def validate_existing_schema() -> list[str]:
    """Return discrepancies. All queries in this function are read-only."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            actual_tables = {row[0] for row in cur.fetchall()}
            errors = [f"missing table: {name}" for name in EXPECTED_COLUMNS if name not in actual_tables]
            for table_name, expected_columns in EXPECTED_COLUMNS.items():
                if table_name not in actual_tables:
                    continue
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s",
                    (table_name,),
                )
                actual_columns = {row[0] for row in cur.fetchall()}
                errors.extend(
                    f"missing column: {table_name}.{column}"
                    for column in sorted(expected_columns - actual_columns)
                )
            cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
            actual_indexes = {row[0] for row in cur.fetchall()}
            errors.extend(
                f"missing index: {name}" for name in sorted(EXPECTED_INDEXES - actual_indexes)
            )
            cur.execute("SELECT to_regclass('public.alembic_version')")
            if cur.fetchone()[0]:
                cur.execute("SELECT version_num FROM alembic_version")
                if {row[0] for row in cur.fetchall()} != {REVISION}:
                    errors.append("database already has a different Alembic revision")
    finally:
        conn.close()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="verify only; do not stamp")
    args = parser.parse_args()

    errors = validate_existing_schema()
    if errors:
        print("Baseline adoption aborted; no changes were made:")
        print(*[f"- {error}" for error in errors], sep="\n")
        return 1
    if args.dry_run:
        print("Schema matches baseline 0001; dry-run completed without changes.")
        return 0

    command.stamp(Config(str(BACKEND_ROOT / "alembic.ini")), REVISION)
    print("Database adopted at Alembic revision 0001_initial_schema. Wye data was not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

