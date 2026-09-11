import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'anonymous_installation_service.dart';
import 'api_client.dart';

enum AiUsagePlan { base, premiumLight, premiumPro, internal }

extension AiUsagePlanInfo on AiUsagePlan {
  String get wireName => switch (this) {
        AiUsagePlan.base => 'base',
        AiUsagePlan.premiumLight => 'premium_light',
        AiUsagePlan.premiumPro => 'premium_pro',
        AiUsagePlan.internal => 'internal',
      };

  int? get dailyLimit => switch (this) {
        AiUsagePlan.base => 3,
        AiUsagePlan.premiumLight => 50,
        AiUsagePlan.premiumPro => 100,
        AiUsagePlan.internal => null,
      };
}

class AiUsageQuotaService extends ChangeNotifier {
  final AnonymousInstallationService installation;
  final http.Client client;
  final AiUsagePlan plan;
  int _used = 0;
  bool _authoritative = false;

  AiUsageQuotaService({
    required this.installation,
    http.Client? client,
    this.plan = AiUsagePlan.base,
  }) : client = client ?? http.Client();

  int get used => _used;
  int? get limit => plan.dailyLimit;
  int? get remaining =>
      limit == null ? null : (limit! - _used).clamp(0, limit!);
  bool get exhausted => remaining == 0;
  bool get isAuthoritative => _authoritative;

  String get availabilityLabel => remaining == null
      ? 'Analisi AI disponibili oggi: senza limite (sviluppo)'
      : 'Analisi AI disponibili oggi: $remaining';

  static String localDay([DateTime? now]) {
    final value = now ?? DateTime.now();
    return '${value.year.toString().padLeft(4, '0')}-'
        '${value.month.toString().padLeft(2, '0')}-'
        '${value.day.toString().padLeft(2, '0')}';
  }

  Future<void> initialize() async {
    final preferences = await SharedPreferences.getInstance();
    _used = preferences.getInt('wye_ai_usage_${localDay()}') ?? 0;
    notifyListeners();
    await refresh();
  }

  Future<void> refresh() async {
    try {
      final id = await installation.ensureId();
      final uri = Uri.parse('${ApiConfig.baseUrl}/mobile/v1/ai-usage/today')
          .replace(queryParameters: {'local_day': localDay()});
      final response = await client.get(uri, headers: {
        'X-WYE-Install-ID': id,
        'X-WYE-Plan': plan.wireName,
      });
      if (response.statusCode != 200) return;
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      _used = (data['used'] as num?)?.toInt() ?? _used;
      _authoritative = true;
      final preferences = await SharedPreferences.getInstance();
      await preferences.setInt('wye_ai_usage_${localDay()}', _used);
      notifyListeners();
    } on Object {
      _authoritative = false;
      notifyListeners();
    }
  }

  void simulateBillableCallForTest({bool cacheHit = false}) {
    if (!cacheHit && !exhausted) _used += 1;
    notifyListeners();
  }

  void close() => client.close();
}
