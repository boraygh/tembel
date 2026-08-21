import 'package:flutter/material.dart';

/// Uygulamanın görsel dili.
///
/// Swift sürümündeki `Theme` ile aynı değerler. Premium his düz dolgudan değil
/// **malzemeden** gelir: yüzeyde hafif dikey gradyan, üst kenarda 1px ışık
/// çizgisi, altta yumuşak gölge.
abstract final class AppTheme {
  // MARK: Renkler
  static const background = Color(0xFF0B0B0F);
  static const surface = Color(0xFF16161C);
  static const surfaceElevated = Color(0xFF212129);
  static const sheetBackground = Color(0xFF13131A);
  static const accent = Color(0xFFFF4D2E);

  /// Vurgunun açık ucu — gradyanların üst tarafında.
  static const accentBright = Color(0xFFFF7345);

  static const textPrimary = Colors.white;
  static final textSecondary = Colors.white.withValues(alpha: 0.56);
  static final textTertiary = Colors.white.withValues(alpha: 0.32);
  static final textQuaternary = Colors.white.withValues(alpha: 0.16);
  static final separator = Colors.white.withValues(alpha: 0.08);
  static final fill = Colors.white.withValues(alpha: 0.06);
  static final accentFill = accent.withValues(alpha: 0.12);

  // MARK: Malzemeler
  static const pageGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF101017), Color(0xFF0A0A0E), Color(0xFF07070A)],
    stops: [0, 0.45, 1],
  );

  static const surfaceGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF1C1C24), Color(0xFF141419)],
  );

  static const emberGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [accentBright, accent],
  );

  /// Kartın üst kenarındaki ışık çizgisi — aşağı doğru söner.
  static Border get edgeHighlight => Border.all(color: Colors.white.withValues(alpha: 0.055));

  static List<BoxShadow> get cardShadow => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.36),
          blurRadius: 18,
          offset: const Offset(0, 8),
        ),
      ];

  /// Vurgu renkli düğmenin altındaki sıcak gölge — nötr gri yerine kendi rengi.
  static List<BoxShadow> get emberShadow => [
        BoxShadow(
          color: accent.withValues(alpha: 0.34),
          blurRadius: 20,
          offset: const Offset(0, 8),
        ),
      ];

  /// Kart malzemesi: gradyan yüzey + kenar ışığı + gölge.
  static BoxDecoration card({double radius = 24}) => BoxDecoration(
        gradient: surfaceGradient,
        borderRadius: BorderRadius.circular(radius),
        border: edgeHighlight,
        boxShadow: cardShadow,
      );

  // MARK: Boşluk ve yarıçap
  static const double spaceXs = 4;
  static const double spaceSm = 8;
  static const double spaceMd = 16;
  static const double spaceLg = 24;
  static const double spaceXl = 32;

  static const double radiusCard = 24;
  static const double radiusTask = 18;
  static const double radiusControl = 16;

  // MARK: Tipografi
  static const _family = 'Archivo';

  static const TextStyle heroTime = TextStyle(
    fontFamily: _family,
    fontSize: 88,
    fontWeight: FontWeight.w800,
    letterSpacing: -4,
    height: 1,
    color: textPrimary,
  );

  static const TextStyle cardTime = TextStyle(
    fontFamily: _family,
    fontSize: 44,
    fontWeight: FontWeight.w800,
    letterSpacing: -2,
    height: 1,
    color: textPrimary,
  );

  static const TextStyle largeTitle = TextStyle(
    fontFamily: _family,
    fontSize: 32,
    fontWeight: FontWeight.w800,
    letterSpacing: -1,
    color: textPrimary,
  );

  static const TextStyle title = TextStyle(
    fontFamily: _family,
    fontSize: 24,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.5,
    color: textPrimary,
  );

  static const TextStyle body = TextStyle(
    fontFamily: _family,
    fontSize: 16,
    fontWeight: FontWeight.w500,
    color: textPrimary,
  );

  static const TextStyle callout = TextStyle(
    fontFamily: _family,
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: textPrimary,
  );

  static const TextStyle footnote = TextStyle(
    fontFamily: _family,
    fontSize: 13,
    fontWeight: FontWeight.w500,
  );

  static const TextStyle sectionLabel = TextStyle(
    fontFamily: _family,
    fontSize: 11,
    fontWeight: FontWeight.w800,
    letterSpacing: 2.2,
  );

  static ThemeData get data => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        fontFamily: _family,
        scaffoldBackgroundColor: background,
        colorScheme: const ColorScheme.dark(
          primary: accent,
          secondary: accentBright,
          surface: surface,
        ),
        splashFactory: InkSparkle.splashFactory,
      );
}
