import 'package:meta/meta.dart';

/// Erteleme ayarı.
///
/// [maxCount] kasıtlı olarak zorunludur: sınırsız erteleme uygulamanın tüm
/// amacını ortadan kaldırır. Sınıra ulaşıldığında erteleme düğmesi kaybolur ve
/// görevleri tamamlamaktan başka yol kalmaz.
@immutable
class SnoozeSetting {
  const SnoozeSetting({
    required this.isEnabled,
    required this.durationMinutes,
    required this.maxCount,
  });

  static const int durationMin = 1;
  static const int durationMax = 30;
  static const int maxCountMin = 1;
  static const int maxCountMax = 5;

  final bool isEnabled;
  final int durationMinutes;
  final int maxCount;

  /// Varsayılan: erteleme kapalı.
  ///
  /// Uygulamanın vaadi "kolayca susturamamak" olduğu için erteleme kapalı
  /// gelir; açmak kullanıcının bilinçli tercihidir.
  static const SnoozeSetting disabled =
      SnoozeSetting(isEnabled: false, durationMinutes: 5, maxCount: 1);

  SnoozeSetting copyWith({bool? isEnabled, int? durationMinutes, int? maxCount}) =>
      SnoozeSetting(
        isEnabled: isEnabled ?? this.isEnabled,
        durationMinutes: durationMinutes ?? this.durationMinutes,
        maxCount: maxCount ?? this.maxCount,
      );

  SnoozeSetting normalized() => SnoozeSetting(
        isEnabled: isEnabled,
        durationMinutes: durationMinutes.clamp(durationMin, durationMax),
        maxCount: maxCount.clamp(maxCountMin, maxCountMax),
      );

  Map<String, Object?> toJson() => {
        'isEnabled': isEnabled,
        'durationMinutes': durationMinutes,
        'maxCount': maxCount,
      };

  factory SnoozeSetting.fromJson(Map<String, Object?> json) => SnoozeSetting(
        isEnabled: (json['isEnabled'] as bool?) ?? false,
        durationMinutes: (json['durationMinutes'] as int?) ?? 5,
        maxCount: (json['maxCount'] as int?) ?? 1,
      ).normalized();

  @override
  bool operator ==(Object other) =>
      other is SnoozeSetting &&
      other.isEnabled == isEnabled &&
      other.durationMinutes == durationMinutes &&
      other.maxCount == maxCount;

  @override
  int get hashCode => Object.hash(isEnabled, durationMinutes, maxCount);
}
