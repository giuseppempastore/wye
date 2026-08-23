import 'package:flutter/material.dart';

class AppColors {
  // Risk Score Colors
  static const Color riskCritical = Color(0xFFD32F2F); // Rosso
  static const Color riskHigh = Color(0xFFF57C00); // Arancio
  static const Color riskModerate = Color(0xFFFBC02D); // Giallo
  static const Color riskLow = Color(0xFF7CB342); // Verde chiaro
  static const Color riskExcellent = Color(0xFF388E3C); // Verde scuro

  // Brand Colors - white + sky blue palette inspired by the new hero artwork
  static const Color primary = Color(0xFF4AA9E8); // Azzurro principale
  static const Color secondary = Color(0xFFBEE6FF); // Azzurro chiaro secondario
  static const Color accent = Color(0xFF8ED7FF); // Azzurro accent

  // Neutral
  static const Color white = Color(0xFFFFFFFF);
  static const Color darkGrey = Color(0xFF212121);
  static const Color mediumGrey = Color(0xFF757575);
  static const Color lightGrey = Color(0xFFF5FBFF);
  static const Color borderGrey = Color(0xFFDDEEFF);

  // Semantic
  static const Color success = Color(0xFF388E3C);
  static const Color error = Color(0xFFD32F2F);
  static const Color warning = Color(0xFFFBC02D);
  static const Color info = Color(0xFF1976D2);

  // Backgrounds
  static const Color bgPrimary = Color(0xFFFAFAFA);
  static const Color bgSecondary = Color(0xFFFFFFFF);

  // Score Gradients (per visualizzazione progressiva)
  static const List<Color> scoreGradient = [
    riskCritical,
    riskHigh,
    riskModerate,
    riskLow,
    riskExcellent,
  ];
}

class AppTypography {
  // Headlines
  static const TextStyle headline1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    fontFamily: 'Poppins',
    color: AppColors.darkGrey,
    height: 1.2,
  );

  static const TextStyle headline2 = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.bold,
    fontFamily: 'Poppins',
    color: AppColors.darkGrey,
    height: 1.2,
  );

  static const TextStyle headline3 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
    fontFamily: 'Poppins',
    color: AppColors.darkGrey,
    height: 1.3,
  );

  // Body
  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w500,
    fontFamily: 'Poppins',
    color: AppColors.darkGrey,
    height: 1.5,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    fontFamily: 'Poppins',
    color: AppColors.mediumGrey,
    height: 1.5,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400,
    fontFamily: 'Poppins',
    color: AppColors.mediumGrey,
    height: 1.4,
  );

  // Button
  static const TextStyle buttonLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    fontFamily: 'Poppins',
    color: AppColors.white,
  );

  static const TextStyle buttonSmall = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    fontFamily: 'Poppins',
    color: AppColors.white,
  );

  // Label
  static const TextStyle label = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w600,
    fontFamily: 'Poppins',
    color: AppColors.darkGrey,
  );

  static const TextStyle labelSmall = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w600,
    fontFamily: 'Poppins',
    color: AppColors.mediumGrey,
  );
}

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        error: AppColors.error,
        surface: AppColors.bgSecondary,
        background: AppColors.bgPrimary,
      ),
      scaffoldBackgroundColor: AppColors.bgPrimary,
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.darkGrey,
        centerTitle: true,
        titleTextStyle: AppTypography.headline3,
      ),
      // cardTheme removed to avoid type mismatch across Flutter versions
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: AppTypography.buttonLarge,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.primary, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: AppTypography.buttonLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primary,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: AppTypography.buttonSmall,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.bgPrimary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.borderGrey),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.borderGrey),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: AppColors.primary,
            width: 2,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.error),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        hintStyle: AppTypography.bodyMedium,
      ),
    );
  }
}

// Utility function per ottenere il colore dal score
Color getScoreColor(double score) {
  if (score < 25) return AppColors.riskCritical;
  if (score < 40) return AppColors.riskHigh;
  if (score < 60) return AppColors.riskModerate;
  if (score < 80) return AppColors.riskLow;
  return AppColors.riskExcellent;
}

String getScoreBand(double score) {
  if (score < 25) return 'Critical';
  if (score < 40) return 'Poor';
  if (score < 60) return 'Moderate';
  if (score < 80) return 'Good';
  return 'Excellent';
}
