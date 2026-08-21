import 'package:meta/meta.dart';

import '../models/alarm.dart';
import '../models/weekday.dart';

/// Planlanmış tek bir alarm çalışı.
///
/// Bir alarm tek bir çalış değil bir **zincir** üretir: ana alarm ve onu takip
/// eden birkaç alarm. Kullanıcı görevleri tamamlamadan sesi susturursa takip
/// alarmları gelmeye devam eder; görevler tamamlandığında kalan zincir iptal
/// edilir.
///
/// Bu tasarımın nedeni platformların temel bir kısıtıdır: uygulama,
/// kullanıcının alarm sesini durdurmasını **engelleyemez**. Engelleyemediğimiz
/// için geri gelmeyi garanti ediyoruz.
@immutable
class ScheduledFire {
  const ScheduledFire({
    required this.alarmId,
    required this.sequence,
    required this.date,
  });

  final String alarmId;

  /// 0 = ana alarm, 1 ve sonrası = takip alarmları.
  final int sequence;
  final DateTime date;

  bool get isFollowUp => sequence > 0;

  /// Sistemde bu çalışı tanımlayan kimlik.
  ///
  /// Alarm kimliği ile sıra numarasından türetilir; aynı alarm için her zaman
  /// aynı değerleri üretir. Görevler tamamlandığında kalan zinciri iptal
  /// edebilmek bu kararlılığa dayanır.
  String get id => '$alarmId#$sequence';

  /// Platform tarafında sayısal kimlik gerektiğinde kullanılır
  /// (Android `AlarmManager` gibi).
  int get numericId => id.hashCode & 0x7FFFFFFF;

  /// [id]'den alarm kimliğini geri çözer.
  static String? alarmIdFromFireId(String fireId) {
    final index = fireId.indexOf('#');
    return index <= 0 ? null : fireId.substring(0, index);
  }

  @override
  bool operator ==(Object other) =>
      other is ScheduledFire &&
      other.alarmId == alarmId &&
      other.sequence == sequence &&
      other.date == date;

  @override
  int get hashCode => Object.hash(alarmId, sequence, date);

  @override
  String toString() => 'ScheduledFire($id, $date)';
}

/// Ana alarmdan sonra kaç saniye aralıkla takip alarmı kurulacağı.
@immutable
class FollowUpPolicy {
  FollowUpPolicy(List<Duration> delays)
      : delays = List.unmodifiable(
          delays.where((d) => d > Duration.zero).toList()..sort(),
        );

  final List<Duration> delays;

  /// Varsayılan zincir: 1, 3, 6 ve 10 dakika sonra.
  ///
  /// Aralıklar kasıtlı olarak artan: ilk takip hemen gelir, sonrakiler
  /// seyrelir. Zincir sınırlıdır çünkü platformların planlanabilir alarm
  /// sayısında üst sınırı var ve bunu tek bir alarmla tüketmek diğerlerini
  /// riske atar.
  static final FollowUpPolicy standard = FollowUpPolicy(const [
    Duration(minutes: 1),
    Duration(minutes: 3),
    Duration(minutes: 6),
    Duration(minutes: 10),
  ]);

  /// Takip alarmı kurmaz — görevsiz alarmlar için.
  static final FollowUpPolicy none = FollowUpPolicy(const []);

  /// Ana alarm dahil toplam kaç alarm planlanacağı.
  int get totalFireCount => delays.length + 1;
}

abstract final class AlarmScheduler {
  /// Kaç gün ileriye bakılacağı. Bir hafta + bugün, her tekrar kalıbını
  /// yakalamaya yeter.
  static const int _searchDays = 8;

  /// Alarmın verilen andan sonraki ilk çalma zamanı.
  ///
  /// Alarmın açık olup olmadığına **bakmaz** — saf zaman hesabıdır.
  /// Kapalı alarmları elemek [firePlan] işidir.
  ///
  /// Yaz saati geçişleri `DateTime`'ın yerel saat normalizasyonuyla ele alınır:
  /// ileri alınan saatte var olmayan bir zaman istendiğinde sonuç geçerli bir
  /// ana kayar, alarm atlanmaz.
  static DateTime? nextOccurrence(Alarm alarm, DateTime after) {
    for (var offset = 0; offset <= _searchDays; offset++) {
      final day = DateTime(after.year, after.month, after.day + offset);
      if (alarm.repeatDays.isNotEmpty &&
          !alarm.repeatDays.contains(Weekday.fromDateTime(day))) {
        continue;
      }
      final candidate = DateTime(
        day.year,
        day.month,
        day.day,
        alarm.time.hour,
        alarm.time.minute,
      );
      if (candidate.isAfter(after)) return candidate;
    }
    return null;
  }

  /// Bir alarmın bir sonraki çalışı için kurulacak alarm zinciri.
  ///
  /// Kapalı alarm boş liste döndürür. Görevi olmayan alarmda takip zinciri
  /// kurulmaz — susturmayı zorlaştırmanın bir anlamı yoktur.
  static List<ScheduledFire> firePlan(
    Alarm alarm,
    DateTime after, {
    FollowUpPolicy? policy,
  }) {
    if (!alarm.isEnabled) return const [];
    final first = nextOccurrence(alarm, after);
    if (first == null) return const [];
    final effective =
        alarm.requiresTasks ? (policy ?? FollowUpPolicy.standard) : FollowUpPolicy.none;
    return chainFrom(alarmId: alarm.id, firstFireAt: first, policy: effective);
  }

  /// Verilen anı ana alarm kabul ederek zinciri kurar.
  ///
  /// Test alarmı ve erteleme de bunu kullanır — ikisi de "şu andan itibaren şu
  /// kadar sonra çal" demektir.
  static List<ScheduledFire> chainFrom({
    required String alarmId,
    required DateTime firstFireAt,
    FollowUpPolicy? policy,
  }) {
    final effective = policy ?? FollowUpPolicy.standard;
    return [
      ScheduledFire(alarmId: alarmId, sequence: 0, date: firstFireAt),
      for (var i = 0; i < effective.delays.length; i++)
        ScheduledFire(
          alarmId: alarmId,
          sequence: i + 1,
          date: firstFireAt.add(effective.delays[i]),
        ),
    ];
  }

  /// Birden fazla alarmın planlarını birleştirir, zamana göre sıralar.
  static List<ScheduledFire> firePlanForAll(
    List<Alarm> alarms,
    DateTime after, {
    FollowUpPolicy? policy,
  }) {
    final all = <ScheduledFire>[
      for (final alarm in alarms) ...firePlan(alarm, after, policy: policy),
    ];
    all.sort((a, b) {
      final byDate = a.date.compareTo(b.date);
      return byDate != 0 ? byDate : a.id.compareTo(b.id);
    });
    return all;
  }

  /// Listedeki alarmlar arasından en yakın çalacak olanı bulur.
  ///
  /// Ana sayfadaki "sonraki alarm ... sonra" satırı bunu kullanır.
  /// Kapalı alarmlar dikkate alınmaz.
  static ({Alarm alarm, DateTime date})? nextAlarm(
    List<Alarm> alarms,
    DateTime after,
  ) {
    ({Alarm alarm, DateTime date})? best;
    for (final alarm in alarms.where((a) => a.isEnabled)) {
      final date = nextOccurrence(alarm, after);
      if (date == null) continue;
      if (best == null ||
          date.isBefore(best.date) ||
          (date == best.date && alarm.id.compareTo(best.alarm.id) < 0)) {
        best = (alarm: alarm, date: date);
      }
    }
    return best;
  }
}
