-- Seed: ingredients and allergens
-- Insert some canonical ingredients
INSERT INTO ingredients (canonical_name, ingredient_group, risk_level, allergen_flag, evidence_level, common_name)
VALUES
('sodium benzoate', 'preservative', 'moderate', FALSE, 3, 'Sodium benzoate'),
('sugar', 'sweetener', 'low', FALSE, 1, 'Sugar'),
('aspartame', 'sweetener', 'high', FALSE, 4, 'Aspartame'),
('milk', 'dairy', 'moderate', TRUE, 5, 'Milk'),
('wheat flour', 'grain', 'moderate', TRUE, 4, 'Wheat Flour')
;

-- Insert allergens
INSERT INTO allergens (allergen_name, canonical_code, category, description, is_active)
VALUES
('milk', 'ALL-MILK', 'dairy', 'Milk and milk derivatives', TRUE),
('gluten', 'ALL-GLUTEN', 'cereals', 'Gluten-containing cereals', TRUE),
('nuts', 'ALL-NUTS', 'tree_nuts', 'Tree nuts and derivatives', TRUE)
;

-- Map ingredient -> allergen where applicable
WITH ing AS (
  SELECT id FROM ingredients WHERE canonical_name = 'milk' LIMIT 1
), alg AS (
  SELECT id FROM allergens WHERE allergen_name = 'milk' LIMIT 1
)
INSERT INTO ingredient_allergens (ingredient_id, allergen_id, relationship_type, confidence, notes)
SELECT ing.id, alg.id, 'contains', 0.95, 'Canonical mapping'
FROM ing, alg
WHERE NOT EXISTS (
  SELECT 1 FROM ingredient_allergens ia
  WHERE ia.ingredient_id = ing.id AND ia.allergen_id = alg.id
);
