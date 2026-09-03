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
    final hasIngredientScore =
        ingredient.evaluabilityStatus == EvaluabilityStatus.computable;
    final hasNutritionScore =
        nutrition.evaluabilityStatus == EvaluabilityStatus.computable;
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
            children: [
              if (hasIngredientScore || hasNutritionScore)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    if (hasIngredientScore)
                      _ComponentScore(
                        label: 'Ingredienti',
                        value: ingredient.scoreValue!,
                      ),
                    if (hasNutritionScore)
                      _ComponentScore(
                        label: 'Nutrizione',
                        value: nutrition.scoreValue!,
                      ),
                  ],
                ),
              if (!hasIngredientScore && !hasNutritionScore)
                Icon(Icons.info_outline, color: neutralColor),
            ],
          ),
        ),
      ),
    );
  }
}

class _ComponentScore extends StatelessWidget {
  final String label;
  final int value;

  const _ComponentScore({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: AppTypography.labelSmall),
        const SizedBox(height: 4),
        Text(
          '$value',
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
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
