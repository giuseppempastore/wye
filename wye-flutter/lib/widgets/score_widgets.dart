import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Score Card - Mostra lo score finale con colore dinamico
class ScoreCard extends StatelessWidget {
  final double score;
  final String? band;
  final double? ingredientScore;
  final double? nutritionScore;
  final VoidCallback? onTap;

  const ScoreCard({
    Key? key,
    required this.score,
    this.band,
    this.ingredientScore,
    this.nutritionScore,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final color = getScoreColor(score);
    final bandName = band ?? getScoreBand(score);

    return GestureDetector(
      onTap: onTap,
      child: Card(
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: color, width: 2),
        ),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                color.withOpacity(0.1),
                color.withOpacity(0.05),
              ],
            ),
          ),
          child: Column(
            children: [
              // Score principale
              SizedBox(
                height: 120,
                width: 120,
                child: Stack(
                  children: [
                    // Background circle
                    Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: color.withOpacity(0.1),
                      ),
                    ),
                    // Score text
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            '${score.toStringAsFixed(0)}',
                            style: TextStyle(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                              color: color,
                            ),
                          ),
                          Text(
                            '/100',
                            style: TextStyle(
                              fontSize: 14,
                              color: color.withOpacity(0.7),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Circle border
                    Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: color,
                          width: 3,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              // Band name
              Text(
                bandName,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 16),
              // Ingredient e Nutrition scores (se disponibili)
              if (ingredientScore != null || nutritionScore != null)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    if (ingredientScore != null)
                      Column(
                        children: [
                          Text(
                            'Ingredienti',
                            style: AppTypography.labelSmall,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${ingredientScore!.toStringAsFixed(0)}',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: getScoreColor(ingredientScore!),
                            ),
                          ),
                        ],
                      ),
                    if (nutritionScore != null)
                      Column(
                        children: [
                          Text(
                            'Nutrizione',
                            style: AppTypography.labelSmall,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${nutritionScore!.toStringAsFixed(0)}',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: getScoreColor(nutritionScore!),
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
            ],
          ),
        ),
      ),
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
              color: isUserSensitive
                  ? AppColors.riskCritical
                  : AppColors.riskHigh,
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
  })  : borderRadius = borderRadius ?? const BorderRadius.all(Radius.circular(8)),
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
