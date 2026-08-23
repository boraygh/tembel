import 'package:meta/meta.dart';

/// Günün bir saati — tarihten bağımsız (07:30 gibi).
///
/// Tek bir `int` olarak saklanır. Saat ve dakika ayrı tutulsaydı 25:70 gibi
/// geçersiz bir değer temsil edilebilirdi; bu tasarımda mümkün değil.
///
/// Flutter'ın `TimeOfDay` sınıfıyla karışmasın diye `ClockTime` adı seçildi.
@immutable
class ClockTime implements Comparable<ClockTime> {
  static const int minutesPerDay = 24 * 60;

  /// Gece yarısından itibaren geçen dakika. Her zaman `0 <= x < 1440`.
  final int minutesSinceMidnight;

  const ClockTime._(this.minutesSinceMidnight);

  /// Aralık dışındaki değerleri gün içine sarar.
  ///
  /// Örnek: `25 * 60` → 01:00, `-30` → 23:30. Bu davranış takip alarm zinciri
  /// hesabında (gece yarısını geçen alarmlar) işe yarar.
  factory ClockTime.fromMinutes(int raw) {
    final wrapped = ((raw % minutesPerDay) + minutesPerDay) % minutesPerDay;
    return ClockTime._(wrapped);
  }

  factory ClockTime(int hour, int minute) => ClockTime.fromMinutes(hour * 60 + minute);

  int get hour => minutesSinceMidnight ~/ 60;

  int get minute => minutesSinceMidnight % 60;

  /// Dakika ekler, gerekirse gün sınırını sararak.
  ClockTime adding(int minutes) => ClockTime.fromMinutes(minutesSinceMidnight + minutes);

  /// "07:30" — her zaman iki haneli.
  String get displayText =>
      '${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}';

  /// JSON'da düz bir sayı olarak yazılır; `{"hour":7,"minute":30}` gürültüsü olmaz.
  int toJson() => minutesSinceMidnight;

  /// Bozuk veya sınır dışı bir değer geldiğinde de geçerli bir saat üretir.
  factory ClockTime.fromJson(Object? json) =>
      ClockTime.fromMinutes(json is int ? json : 0);

  @override
  int compareTo(ClockTime other) =>
      minutesSinceMidnight.compareTo(other.minutesSinceMidnight);

  bool operator <(ClockTime other) => compareTo(other) < 0;
  bool operator >(ClockTime other) => compareTo(other) > 0;
  bool operator <=(ClockTime other) => compareTo(other) <= 0;
  bool operator >=(ClockTime other) => compareTo(other) >= 0;

  @override
  bool operator ==(Object other) =>
      other is ClockTime && other.minutesSinceMidnight == minutesSinceMidnight;

  @override
  int get hashCode => minutesSinceMidnight.hashCode;

  @override
  String toString() => 'ClockTime($displayText)';
}
