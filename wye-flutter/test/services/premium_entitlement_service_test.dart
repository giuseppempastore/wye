import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/premium_entitlement_service.dart';

void main() {
  test('premium instant analysis is unavailable by default', () {
    const service = BuildConfiguredPremiumEntitlement(
      isPhase9DevelopmentBuild: false,
    );
    expect(service.canAnalyzeLabelImmediately, isFalse);
    expect(service.instantLabelAnalysis, PremiumEntitlementState.unavailable);
  });

  test('production-like builds cannot use the development override', () {
    const service = BuildConfiguredPremiumEntitlement(
      isPhase9DevelopmentBuild: false,
    );
    expect(service.canAnalyzeLabelImmediately, isFalse);
  });
}
