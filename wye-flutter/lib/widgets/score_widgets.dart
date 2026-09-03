import 'package:flutter/material.dart';
import '../models/score_evaluability_model.dart';
import '../theme/app_theme.dart';

/// Component score container. Overall scoring remains unavailable/deferred.
class ScoreCard extends StatelessWidget {
  final ProductScoreView scoreView;
  final VoidCallback? onTap;

  const ScoreCard({
    Key? key,
    required this.scoreView,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final ingredient = scoreView.ingredientGoodnessPercent;
    final nutrition = scoreView.nutritionGoodnessPercent;
    final neutralColor = Theme.of(context).colorScheme.outline;

    return GestureDetector(
      onTap: onTap,
      child: Card(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: neutralColor),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Valutazioni per componente',
                style: AppTypography.label,
              ),
              const SizedBox(height: 16),
              _ComponentResult(
                componentId: 'ingredient',
                label: 'Ingredienti',
                evaluation: ingredient,
              ),
              const SizedBox(height: 12),
              _ComponentResult(
                componentId: 'nutrition',
                label: 'Nutrizione',
                evaluation: nutrition,
              ),
              const SizedBox(height: 16),
              Divider(color: neutralColor),
              const SizedBox(height: 8),
              _OverallResult(overallScore: scoreView.overallScore),
            ],
          ),
        ),
      ),
    );
  }
}

class _ComponentResult extends StatelessWidget {
  final String componentId;
  final String label;
  final ScoreEvaluation evaluation;

  const _ComponentResult({
    required this.componentId,
    required this.label,
    required this.evaluation,
  });

  @override
  Widget build(BuildContext context) {
    final neutralColor = Theme.of(context).colorScheme.outline;

    return Container(
      key: ValueKey('$componentId-component-result'),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: neutralColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(label, style: AppTypography.labelSmall)),
              _EvaluationValue(
                componentId: componentId,
                evaluation: evaluation,
              ),
            ],
          ),
          if (_hasSupportingDetails(evaluation)) ...[
            const SizedBox(height: 10),
            Divider(color: neutralColor),
            const SizedBox(height: 6),
            _SupportingDetails(
              componentId: componentId,
              evaluation: evaluation,
            ),
          ],
        ],
      ),
    );
  }

  bool _hasSupportingDetails(ScoreEvaluation value) {
    return value.assessmentCoveragePercent != null ||
        value.confidenceState != null ||
        value.missingInputs.isNotEmpty ||
        value.uncertainties.isNotEmpty;
  }
}

class _EvaluationValue extends StatelessWidget {
  final String componentId;
  final ScoreEvaluation evaluation;

  const _EvaluationValue({
    required this.componentId,
    required this.evaluation,
  });

  @override
  Widget build(BuildContext context) {
    switch (evaluation.evaluabilityStatus) {
      case EvaluabilityStatus.computable:
        return Text(
          '${evaluation.scoreValue} su 100',
          key: ValueKey('$componentId-score-value'),
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        );
      case EvaluabilityStatus.notComputable:
        return Text(
          'Non calcolabile',
          key: ValueKey('$componentId-not-computable'),
          style: AppTypography.bodySmall,
        );
      case EvaluabilityStatus.nonApplicable:
        return Text(
          'Non applicabile',
          key: ValueKey('$componentId-non-applicable'),
          style: AppTypography.bodySmall,
        );
    }
  }
}

class _SupportingDetails extends StatelessWidget {
  final String componentId;
  final ScoreEvaluation evaluation;

  const _SupportingDetails({
    required this.componentId,
    required this.evaluation,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      key: ValueKey('$componentId-supporting-details'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (evaluation.assessmentCoveragePercent case final coverage?)
          Text('Copertura: $coverage%', style: AppTypography.bodySmall),
        if (evaluation.confidenceState case final confidence?)
          Text('Confidenza: $confidence', style: AppTypography.bodySmall),
        if (evaluation.missingInputs.isNotEmpty)
          Text(
            'Dati mancanti dichiarati: ${evaluation.missingInputs.length}',
            style: AppTypography.bodySmall,
          ),
        if (evaluation.uncertainties.isNotEmpty)
          Text(
            'Incertezze dichiarate: ${evaluation.uncertainties.length}',
            style: AppTypography.bodySmall,
          ),
      ],
    );
  }
}

class _OverallResult extends StatelessWidget {
  final OverallScoreState overallScore;

  const _OverallResult({required this.overallScore});

  @override
  Widget build(BuildContext context) {
    final stateLabel = switch (overallScore.availability) {
      OverallScoreAvailability.deferred => 'Differita per questa fase MVP',
      OverallScoreAvailability.unavailable =>
        'Non disponibile per questa fase MVP',
    };

    return Row(
      key: const ValueKey('overall-result-state'),
      children: [
        Icon(
          Icons.info_outline,
          color: Theme.of(context).colorScheme.outline,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Valutazione complessiva', style: AppTypography.labelSmall),
              const SizedBox(height: 2),
              Text(stateLabel, style: AppTypography.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}

/// Ingredient Risk Tag - Mostra ingrediente critico
class RiskTag extends StatelessWidget {
  final String label;
  final String riskLevel; // low, moderate, high, critical
  final VoidCallback? onTap;

  const RiskTag({
    Key? key,
    required this.label,
    required this.riskLevel,
    this.onTap,
  }) : super(key: key);

  Color _getColorForRisk(String risk) {
    switch (risk.toLowerCase()) {
      case 'critical':
        return AppColors.riskCritical;
      case 'high':
        return AppColors.riskHigh;
      case 'moderate':
        return AppColors.riskModerate;
      case 'low':
        return AppColors.riskLow;
      default:
        return AppColors.mediumGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColorForRisk(riskLevel);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          border: Border.all(color: color, width: 1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

/// Allergen Badge - Mostra allergene rilevato
class AllergenBadge extends StatelessWidget {
  final String allergen;
  final bool isUserSensitive;

  const AllergenBadge({
    Key? key,
    required this.allergen,
    this.isUserSensitive = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: isUserSensitive
            ? AppColors.riskCritical.withOpacity(0.2)
            : AppColors.riskHigh.withOpacity(0.2),
        border: Border.all(
          color: isUserSensitive ? AppColors.riskCritical : AppColors.riskHigh,
          width: 1.5,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '⚠️',
            style: const TextStyle(fontSize: 12),
          ),
          const SizedBox(width: 4),
          Text(
            allergen,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color:
                  isUserSensitive ? AppColors.riskCritical : AppColors.riskHigh,
            ),
          ),
        ],
      ),
    );
  }
}

/// Loading Shimmer - Placeholder mentre carica
class LoadingShimmer extends StatelessWidget {
  final double height;
  final double width;
  final BorderRadius borderRadius;

  const LoadingShimmer({
    Key? key,
    this.height = 20,
    this.width = double.infinity,
    BorderRadius? borderRadius,
  })  : borderRadius =
            borderRadius ?? const BorderRadius.all(Radius.circular(8)),
        super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: width,
      decoration: BoxDecoration(
        color: AppColors.lightGrey,
        borderRadius: borderRadius,
      ),
      child: const Shimmer.fromColors(
        baseColor: AppColors.lightGrey,
        highlightColor: AppColors.white,
        child: SizedBox.expand(),
      ),
    );
  }
}

// Placeholder per shimmer - aggiungi a pubspec.yaml: shimmer: ^3.0.0
class Shimmer extends StatelessWidget {
  const Shimmer.fromColors({
    Key? key,
    required this.baseColor,
    required this.highlightColor,
    required this.child,
  }) : super(key: key);

  final Color baseColor;
  final Color highlightColor;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return child; // Placeholder - implementa shimmer effect vero
  }
}

/// Info Section - Sezione informativa con icona
class InfoSection extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final Color? iconColor;

  const InfoSection({
    Key? key,
    required this.title,
    required this.description,
    required this.icon,
    this.iconColor,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bgPrimary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.borderGrey),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: iconColor ?? AppColors.primary,
            size: 24,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTypography.label,
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: AppTypography.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
