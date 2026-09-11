import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/ai_usage_quota_service.dart';
import 'package:wye/services/anonymous_installation_service.dart';

void main() {
  test('prototype plans expose the governed daily limits', () {
    expect(AiUsagePlan.base.dailyLimit, 3);
    expect(AiUsagePlan.premiumLight.dailyLimit, 50);
    expect(AiUsagePlan.premiumPro.dailyLimit, 100);
  });

  test('only a simulated billable non-cache call decrements availability', () {
    final service = AiUsageQuotaService(
      installation: AnonymousInstallationService(),
    );
    expect(service.remaining, 3);
    service.simulateBillableCallForTest(cacheHit: true);
    expect(service.remaining, 3);
    service.simulateBillableCallForTest();
    expect(service.remaining, 2);
  });

  test('base quota saturates at zero', () {
    final service = AiUsageQuotaService(
      installation: AnonymousInstallationService(),
    );
    for (var index = 0; index < 8; index++) {
      service.simulateBillableCallForTest();
    }
    expect(service.remaining, 0);
    expect(service.exhausted, isTrue);
  });
}
