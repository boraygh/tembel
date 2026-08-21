import '../core/models/alarm.dart';
import '../core/models/weekday.dart';

/// Uygulamadaki tüm metinler.
///
/// Tek yerde tutuluyor ki ileride yerelleştirmeye taşınması tek dosyayı
/// gezmekle bitsin.
abstract final class Strings {
  static const appName = 'Tembel';

  static const alarmsTab = 'Alarmlar';
  static const premiumTab = 'Premium';
  static const settingsTab = 'Ayarlar';

  static const untitledAlarm = 'Alarm';
  static const noRepeat = 'Tekrar yok';
  static const everyday = 'Her gün';
  static const weekdaysLabel = 'Hafta içi';
  static const weekendLabel = 'Hafta sonu';

  static const emptyTitle = 'Henüz alarm yok';
  static const emptyMessage =
      'Kapatmak için görev tamamlaman gereken bir alarm kur. Yataktan kalkmadan susturamazsın.';
  static const emptyAction = 'İlk alarmını kur';

  static const nextAlarmPrefix = 'Sonraki alarm ';
  static const noEnabledAlarm = 'Açık alarm yok';

  static String taskCount(int count) => count == 0 ? 'Görev yok' : '$count görev';

  static String weekdayShort(Weekday day) => switch (day) {
        Weekday.monday => 'Pzt',
        Weekday.tuesday => 'Sal',
        Weekday.wednesday => 'Çar',
        Weekday.thursday => 'Per',
        Weekday.friday => 'Cum',
        Weekday.saturday => 'Cmt',
        Weekday.sunday => 'Paz',
      };

  /// "8 sa 42 dk sonra" — kalan süreyi yazar. Geçmiş bir an verilirse `null`.
  ///
  /// Tek birim gösteren hazır biçimlendiriciler dakikayı yutuyor; alarm
  /// uygulamasında kullanıcının asıl merak ettiği şey dakika.
  static String? timeRemaining(DateTime until, DateTime from) {
    final interval = until.difference(from);
    if (interval <= Duration.zero) return null;
    if (interval.inMinutes < 1) return 'birazdan';
    if (interval.inHours < 1) return '${interval.inMinutes} dakika sonra';
    if (interval.inDays < 1) {
      final minutes = interval.inMinutes % 60;
      return minutes == 0
          ? '${interval.inHours} saat sonra'
          : '${interval.inHours} sa \$minutes dk sonra';
    }
    final hours = interval.inHours % 24;
    return hours == 0
        ? '${interval.inDays} gün sonra'
        : '${interval.inDays} gün \$hours saat sonra';
  }
}

extension AlarmDisplay on Alarm {
  String get displayTitle => title.isEmpty ? Strings.untitledAlarm : title;

  /// Tekrar günlerinin okunabilir özeti.
  ///
  /// Yedi gün rozetini her yerde göstermek yerine yaygın seçimler
  /// adlandırılıyor — "Hafta içi", yedi kutucuktan çok daha hızlı okunur.
  String get repeatSummary {
    if (repeatDays.isEmpty) return Strings.noRepeat;
    if (repeatDays.length == 7) return Strings.everyday;
    if (repeatDays.length == 5 &&
        repeatDays.containsAll(Weekday.weekdays)) {
      return Strings.weekdaysLabel;
    }
    if (repeatDays.length == 2 && repeatDays.containsAll(Weekday.weekend)) {
      return Strings.weekendLabel;
    }
    return orderedRepeatDays.map(Strings.weekdayShort).join(', ');
  }
}
