import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/product_model.dart';

void main() {
  test('canonical JSON keeps salt_g as grams', () {
    final facts = NutritionFacts.fromJson(const {'salt_g': 1.2});
    expect(facts.saltG, 1.2);
    expect(facts.toJson()['salt_g'], 1.2);
    expect(facts.toJson(), isNot(contains('salt_mg')));
  });

  test('canonical JSON keeps sodium_mg as milligrams', () {
    final facts = NutritionFacts.fromJson(const {'sodium_mg': 480});
    expect(facts.sodiumMg, 480);
    expect(facts.toJson()['sodium_mg'], 480);
  });

  test('salt and sodium are not silently derived from each other', () {
    final saltOnly = NutritionFacts.fromJson(const {'salt_g': .7});
    final sodiumOnly = NutritionFacts.fromJson(const {'sodium_mg': 280});
    expect(saltOnly.sodiumMg, isNull);
    expect(sodiumOnly.saltG, isNull);
  });

  test('legacy unambiguous keys can still be read but emit canonical keys', () {
    final facts = NutritionFacts.fromJson(const {'salt': .5, 'sodium': 200});
    expect(facts.toJson(), containsPair('salt_g', .5));
    expect(facts.toJson(), containsPair('sodium_mg', 200));
    expect(facts.toJson(), isNot(contains('salt')));
    expect(facts.toJson(), isNot(contains('sodium')));
  });
}
