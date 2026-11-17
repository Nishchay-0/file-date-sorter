import 'dart:ui';
import 'package:flutter/material.dart';

/// Apple Glassmorphism Design System Tokens
class GlassTheme {
  static const Color accentBlue = Color(0xFF007AFF);
  static const Color accentBlueDark = Color(0xFF0A84FF);

  // Light Theme Tokens
  static const Color lightBg = Color(0xFFF2F2F7);
  static const Color lightCard = Color(0xCCFFFFFF);
  static const Color lightCardAlt = Color(0xE6E5E5EA);
  static const Color lightBorder = Color(0x33000000);
  static const Color lightTextPrimary = Color(0xFF000000);
  static const Color lightTextSecondary = Color(0xFF6C6C70);

  // Dark Theme Tokens
  static const Color darkBg = Color(0xFF000000);
  static const Color darkCard = Color(0xCC1C1C1E);
  static const Color darkCardAlt = Color(0xE62C2C2E);
  static const Color darkBorder = Color(0x33FFFFFF);
  static const Color darkTextPrimary = Color(0xFFFFFFFF);
  static const Color darkTextSecondary = Color(0xFF8E8E93);

  static BoxDecoration glassBoxDecoration(BuildContext context, {double radius = 16.0}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return BoxDecoration(
      color: isDark ? darkCard : lightCard,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(
        color: isDark ? darkBorder : lightBorder,
        width: 1.0,
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(isDark ? 0.3 : 0.05),
          blurRadius: 10,
          offset: const Offset(0, 4),
        )
      ],
    );
  }

  static Widget glassCard({
    required BuildContext context,
    required Widget child,
    double radius = 16.0,
    EdgeInsetsGeometry? padding,
  }) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          decoration: glassBoxDecoration(context, radius: radius),
          padding: padding ?? const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }
}
