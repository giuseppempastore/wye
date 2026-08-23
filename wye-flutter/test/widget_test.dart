import 'package:flutter_test/flutter_test.dart';
import 'package:wye/providers/app_providers.dart';

void main() {
  test('premium fact-check checkbox is one-shot and resets after a deliberate trigger', () {
    final prefs = UserPreferencesProvider();

    prefs.setPremium(true);
    prefs.setCountry('IT');

    expect(prefs.isPremium, isTrue);
    expect(prefs.country, 'IT');
    expect(prefs.premiumFactCheckConsent, isFalse);

    prefs.setPremiumFactCheckConsent(true);
    expect(prefs.premiumFactCheckConsent, isTrue);

    prefs.resetPremiumFactCheckConsent();
    expect(prefs.premiumFactCheckConsent, isFalse);
  });
}
