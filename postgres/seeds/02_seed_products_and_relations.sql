-- Seed: products, product_ingredients, nutrition_facts, product_scores
-- Insert a sample product
INSERT INTO products (barcode, brand_name, product_name, category, product_type, source, verified, status)
SELECT '9876543210987', 'SeedBrand', 'Seeded Snack Bar', 'food', 'snack', 'manual', TRUE, 'active'
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE barcode = '9876543210987'
);

-- Link product to ingredients (look up ids)
WITH prod AS (
  SELECT id FROM products WHERE barcode = '9876543210987' LIMIT 1
), ing_sugar AS (
  SELECT id FROM ingredients WHERE canonical_name = 'sugar' LIMIT 1
)
INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, canonical_name, position_in_list, confidence, allergen_flag, risky_flag)
SELECT prod.id, ing_sugar.id, 'Sugar', 'sugar', 1, 0.9, FALSE, FALSE
FROM prod, ing_sugar
WHERE NOT EXISTS (
  SELECT 1 FROM product_ingredients pi
  WHERE pi.product_id = prod.id AND pi.ingredient_id = ing_sugar.id
);

WITH prod AS (
  SELECT id FROM products WHERE barcode = '9876543210987' LIMIT 1
), ing_benzoate AS (
  SELECT id FROM ingredients WHERE canonical_name = 'sodium benzoate' LIMIT 1
)
INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, canonical_name, position_in_list, confidence, allergen_flag, risky_flag)
SELECT prod.id, ing_benzoate.id, 'Sodium Benzoate', 'sodium benzoate', 2, 0.85, FALSE, TRUE
FROM prod, ing_benzoate
WHERE NOT EXISTS (
  SELECT 1 FROM product_ingredients pi
  WHERE pi.product_id = prod.id AND pi.ingredient_id = ing_benzoate.id
);

WITH prod AS (
  SELECT id FROM products WHERE barcode = '9876543210987' LIMIT 1
), ing_milk AS (
  SELECT id FROM ingredients WHERE canonical_name = 'milk' LIMIT 1
)
INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, canonical_name, position_in_list, confidence, allergen_flag, risky_flag)
SELECT prod.id, ing_milk.id, 'Milk Powder', 'milk', 3, 0.95, TRUE, FALSE
FROM prod, ing_milk
WHERE NOT EXISTS (
  SELECT 1 FROM product_ingredients pi
  WHERE pi.product_id = prod.id AND pi.ingredient_id = ing_milk.id
);

-- Insert nutrition facts for the product
WITH prod AS (
  SELECT id FROM products WHERE barcode = '9876543210987' LIMIT 1
)
INSERT INTO nutrition_facts (product_id, serving_size, energy_kcal, protein_g, carbs_g, sugar_g, fat_g, saturated_fat_g, sodium_mg, fiber_g, source, declared_by_manufacturer, verified, raw_text)
SELECT prod.id, '100g', 420, 6.0, 55.0, 30.0, 18.0, 8.0, 300, 3.5, 'manufacturer', TRUE, TRUE, 'Sample nutrition facts'
FROM prod
WHERE NOT EXISTS (
  SELECT 1 FROM nutrition_facts nf WHERE nf.product_id = prod.id
);

-- Insert a product score (example values)
WITH prod AS (
  SELECT id FROM products WHERE barcode = '9876543210987' LIMIT 1
)
INSERT INTO product_scores (product_id, ingredient_score, nutrition_score, final_score, score_band, ingredient_risk_summary, nutrition_summary, final_summary, calculation_version)
SELECT prod.id, 40.00, 75.00, 52.00, 'moderate', 'Contains preservatives', 'Nutrition acceptable', 'Final penalized due to ingredients', 'v1'
FROM prod
WHERE NOT EXISTS (
  SELECT 1 FROM product_scores ps WHERE ps.product_id = prod.id
);
