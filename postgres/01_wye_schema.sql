-- WYE PostgreSQL schema
-- Database: wye
-- Purpose: product catalog, ingredient scoring, allergens, nutrition, users, premium profiles

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    barcode VARCHAR(255) UNIQUE,
    gtin VARCHAR(255),
    brand_name VARCHAR(255),
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    product_type VARCHAR(100),
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'draft', 'needs_review', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredients (
    id BIGSERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL,
    ingredient_group VARCHAR(100),
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    allergen_flag BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_level INTEGER NOT NULL DEFAULT 1 CHECK (evidence_level BETWEEN 1 AND 6),
    cas_number VARCHAR(50),
    einecs_number VARCHAR(50),
    common_name VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'review_pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient_aliases (
    id BIGSERIAL PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    alias_name VARCHAR(255) NOT NULL,
    normalized_alias VARCHAR(255) NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    alias_type VARCHAR(30) NOT NULL DEFAULT 'synonym' CHECK (alias_type IN ('synonym', 'translation', 'code', 'e_number', 'trade_name')),
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient_categories (
    id BIGSERIAL PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    classification_source VARCHAR(50) NOT NULL DEFAULT 'internal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient_risk_profiles (
    id BIGSERIAL PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    hazard_type VARCHAR(100),
    evidence_level INTEGER NOT NULL DEFAULT 1 CHECK (evidence_level BETWEEN 1 AND 6),
    adverse_risk_note TEXT,
    noael NUMERIC(12,4),
    adi NUMERIC(12,4),
    dose_threshold_low NUMERIC(12,4),
    dose_threshold_high NUMERIC(12,4),
    population_at_risk TEXT,
    review_status VARCHAR(20) NOT NULL DEFAULT 'approved' CHECK (review_status IN ('approved', 'pending_review', 'disputed')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS allergens (
    id BIGSERIAL PRIMARY KEY,
    allergen_name VARCHAR(255) NOT NULL,
    canonical_code VARCHAR(50),
    category VARCHAR(100),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient_allergens (
    id BIGSERIAL PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    allergen_id BIGINT NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    relationship_type VARCHAR(20) NOT NULL CHECK (relationship_type IN ('contains', 'may_contain', 'suspected', 'derived_from')),
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(30) NOT NULL CHECK (source_type IN ('regulatory', 'public_health', 'scientific', 'academic')),
    url TEXT,
    authority_level INTEGER NOT NULL DEFAULT 1 CHECK (authority_level BETWEEN 1 AND 6),
    country VARCHAR(10),
    is_authoritative BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient_evidence (
    id BIGSERIAL PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    evidence_title VARCHAR(255),
    evidence_summary TEXT,
    risk_statement TEXT,
    evidence_level INTEGER NOT NULL DEFAULT 1 CHECK (evidence_level BETWEEN 1 AND 6),
    url TEXT,
    publication_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_ingredients (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    raw_name TEXT NOT NULL,
    canonical_name VARCHAR(255),
    position_in_list INTEGER NOT NULL DEFAULT 0,
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    allergen_flag BOOLEAN NOT NULL DEFAULT FALSE,
    risky_flag BOOLEAN NOT NULL DEFAULT FALSE,
    is_unknown BOOLEAN NOT NULL DEFAULT FALSE,
    manual_override BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nutrition_facts (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    serving_size VARCHAR(50),
    energy_kcal NUMERIC(10,2),
    protein_g NUMERIC(10,2),
    carbs_g NUMERIC(10,2),
    sugar_g NUMERIC(10,2),
    fat_g NUMERIC(10,2),
    saturated_fat_g NUMERIC(10,2),
    sodium_mg NUMERIC(10,2),
    fiber_g NUMERIC(10,2),
    source VARCHAR(50) NOT NULL DEFAULT 'manufacturer',
    declared_by_manufacturer BOOLEAN NOT NULL DEFAULT TRUE,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    raw_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nutrition_thresholds (
    id BIGSERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    nutrient_name VARCHAR(50) NOT NULL,
    threshold_low NUMERIC(10,2),
    threshold_medium NUMERIC(10,2),
    threshold_high NUMERIC(10,2),
    unit VARCHAR(20),
    source_reference TEXT,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_scores (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    ingredient_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (ingredient_score BETWEEN 0 AND 100),
    nutrition_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (nutrition_score BETWEEN 0 AND 100),
    final_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (final_score BETWEEN 0 AND 100),
    score_band VARCHAR(20) NOT NULL CHECK (score_band IN ('excellent', 'good', 'moderate', 'poor', 'critical')),
    ingredient_risk_summary TEXT,
    nutrition_summary TEXT,
    final_summary TEXT,
    calculation_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cosmetics_products (
    id BIGSERIAL PRIMARY KEY,
    barcode VARCHAR(255),
    brand VARCHAR(255),
    product_name VARCHAR(255) NOT NULL,
    product_type VARCHAR(100),
    ingredient_list_raw TEXT,
    ingredients_mapped BOOLEAN NOT NULL DEFAULT FALSE,
    ingredient_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (ingredient_score BETWEEN 0 AND 100),
    final_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (final_score BETWEEN 0 AND 100),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cosmetic_ingredient_assessment (
    id BIGSERIAL PRIMARY KEY,
    cosmetic_product_id BIGINT NOT NULL REFERENCES cosmetics_products(id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    reason TEXT,
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255),
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'anonymous' CHECK (auth_provider IN ('google', 'email', 'anonymous')),
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    height_cm NUMERIC(5,2),
    weight_kg NUMERIC(5,2),
    bmi NUMERIC(5,2),
    allergies_raw TEXT,
    health_conditions_raw TEXT,
    diet_type VARCHAR(100),
    activity_level VARCHAR(50),
    goal_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_allergies (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    allergen_id BIGINT NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL DEFAULT 'moderate' CHECK (severity IN ('mild', 'moderate', 'severe')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS product_reviews (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    submitted_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected')),
    source_type VARCHAR(30) NOT NULL DEFAULT 'manual_input' CHECK (source_type IN ('manual_input', 'OCR', 'barcode')),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_ingredients_canonical_name ON ingredients(canonical_name);
CREATE INDEX IF NOT EXISTS idx_ingredient_aliases_normalized ON ingredient_aliases(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_product_ingredients_product_id ON product_ingredients(product_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_facts_product_id ON nutrition_facts(product_id);
CREATE INDEX IF NOT EXISTS idx_product_scores_product_id ON product_scores(product_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_allergens_name ON allergens(allergen_name);
