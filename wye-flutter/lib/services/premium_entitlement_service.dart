enum PremiumEntitlementState { unavailable, developmentEnabled }

abstract interface class PremiumEntitlementService {
  PremiumEntitlementState get instantLabelAnalysis;
  bool get canAnalyzeLabelImmediately;
}

/// No production user/subscription contract exists in this repository yet.
/// The opt-in can only operate together with the explicit Phase 9 dev build.
class BuildConfiguredPremiumEntitlement implements PremiumEntitlementService {
  static const bool _devOptIn = bool.fromEnvironment(
    'WYE_PREMIUM_LABEL_ANALYSIS_ENABLED',
    defaultValue: false,
  );

  final bool isPhase9DevelopmentBuild;

  const BuildConfiguredPremiumEntitlement({
    required this.isPhase9DevelopmentBuild,
  });

  @override
  PremiumEntitlementState get instantLabelAnalysis =>
      _devOptIn && isPhase9DevelopmentBuild
          ? PremiumEntitlementState.developmentEnabled
          : PremiumEntitlementState.unavailable;

  @override
  bool get canAnalyzeLabelImmediately =>
      instantLabelAnalysis == PremiumEntitlementState.developmentEnabled;
}
