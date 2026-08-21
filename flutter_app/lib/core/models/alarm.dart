import 'package:collection/collection.dart';
import 'package:meta/meta.dart';

import 'alarm_sound.dart';
import 'alarm_task.dart';
import 'clock_time.dart';
import 'snooze_setting.dart';
import 'weekday.dart';

/// Kullanıcının kurduğu bir alarm.
///
/// Bu tip yalnızca **yapılandırmayı** temsil eder — "alarm şu an çalıyor mu",
/// "hangi görev tamamlandı" gibi çalışma anı durumları burada tutulmaz.
/// O durum `AlarmSession` içinde yaşar.
///
/// Ayrımın nedeni: yapılandırma kalıcıdır ve kullanıcı tarafından düzenlenir;
/// çalışma anı durumu geçicidir ve alarm bittiğinde atılır. İkisini tek tipte
/// tutmak "dün tamamlanmış görev" gibi kirli durumların diske yazılmasına yol
/// açar.
@immutable
class Alarm {
  Alarm({
    required this.id,
    this.title = '',
    required this.time,
    this.repeatDays = const {},
    this.isEnabled = true,
    this.sound = AlarmSound.systemDefault,
    this.tasks = const [],
    this.snooze = SnoozeSetting.disabled,
    DateTime? createdAt,
  }) : createdAt = _truncateToSeconds(createdAt ?? DateTime.now());

  static const int titleMaxLength = 40;
  static const int maxTaskCount = 5;

  final String id;
  final String title;
  final ClockTime time;

  /// Boş küme = tekrar yok, yalnızca bir sonraki oluşumda çalar.
  final Set<Weekday> repeatDays;
  final bool isEnabled;
  final AlarmSound sound;

  /// Sıra, listedeki konumdur. Boş liste = görevsiz alarm.
  final List<AlarmTask> tasks;
  final SnoozeSetting snooze;
  final DateTime createdAt;

  /// Saniye altı hassasiyet atılır ve saat yerel dilime çekilir.
  ///
  /// İki ayrı tuzağı birden kapatır:
  /// - ISO8601 gibi bazı kodlamalar milisaniyeyi taşımaz;
  /// - Dart'ta `DateTime` eşitliği **UTC/yerel bayrağına da bakar**, yani
  ///   aynı anı gösteren iki tarih farklı bayraklarla eşit sayılmaz.
  ///
  /// İkisi birlikte, kaydedilip geri okunan bir alarmın kendisine eşit
  /// çıkmamasına yol açardı — "alarm değişti mi?" kontrolleri sessizce
  /// yanlış sonuç verirdi.
  static DateTime _truncateToSeconds(DateTime date) {
    final local = date.toLocal();
    return DateTime.fromMillisecondsSinceEpoch(
      (local.millisecondsSinceEpoch ~/ 1000) * 1000,
    );
  }

  bool get isRepeating => repeatDays.isNotEmpty;
  bool get requiresTasks => tasks.isNotEmpty;
  List<Weekday> get orderedRepeatDays => repeatDays.ordered;

  Alarm copyWith({
    String? title,
    ClockTime? time,
    Set<Weekday>? repeatDays,
    bool? isEnabled,
    AlarmSound? sound,
    List<AlarmTask>? tasks,
    SnoozeSetting? snooze,
  }) =>
      Alarm(
        id: id,
        title: title ?? this.title,
        time: time ?? this.time,
        repeatDays: repeatDays ?? this.repeatDays,
        isEnabled: isEnabled ?? this.isEnabled,
        sound: sound ?? this.sound,
        tasks: tasks ?? this.tasks,
        snooze: snooze ?? this.snooze,
        createdAt: createdAt,
      );

  /// Görevleri yeniden sıralar.
  ///
  /// `oldIndex`/`newIndex` Flutter'ın `ReorderableListView` semantiğiyle
  /// uyumludur: aşağı taşımada hedef indeks, öğe listeden çıkarılmadan önceki
  /// konuma göre verilir.
  Alarm movingTask({required int oldIndex, required int newIndex}) {
    if (oldIndex < 0 || oldIndex >= tasks.length) return this;
    final updated = List<AlarmTask>.of(tasks);
    var target = newIndex;
    if (target > oldIndex) target -= 1;
    target = target.clamp(0, updated.length - 1);
    final moved = updated.removeAt(oldIndex);
    updated.insert(target, moved);
    return copyWith(tasks: updated);
  }

  /// Diskten okunan veriyi geçerli sınırlara çeker.
  Alarm normalized() {
    final trimmed = title.trim();
    return Alarm(
      id: id,
      title: trimmed.length > titleMaxLength
          ? trimmed.substring(0, titleMaxLength)
          : trimmed,
      time: time,
      repeatDays: repeatDays,
      isEnabled: isEnabled,
      sound: sound,
      tasks: tasks.take(maxTaskCount).map((t) => t.normalized()).toList(),
      snooze: snooze.normalized(),
      createdAt: createdAt,
    );
  }

  Map<String, Object?> toJson() => {
        'id': id,
        'title': title,
        'time': time.toJson(),
        'repeatDays': repeatDays.map((d) => d.value).toList()..sort(),
        'isEnabled': isEnabled,
        'sound': sound.name,
        'tasks': tasks.map((t) => t.toJson()).toList(),
        'snooze': snooze.toJson(),
        'createdAt': createdAt.toUtc().toIso8601String(),
      };

  factory Alarm.fromJson(Map<String, Object?> json) => Alarm(
        id: (json['id'] as String?) ?? '',
        title: (json['title'] as String?) ?? '',
        time: ClockTime.fromJson(json['time']),
        repeatDays: ((json['repeatDays'] as List?) ?? const [])
            .whereType<int>()
            .map(Weekday.fromValue)
            .nonNulls
            .toSet(),
        isEnabled: (json['isEnabled'] as bool?) ?? true,
        sound: AlarmSound.fromName(json['sound'] as String?),
        tasks: ((json['tasks'] as List?) ?? const [])
            .whereType<Map>()
            .map((e) => AlarmTask.fromJson(e.cast<String, Object?>()))
            .toList(),
        snooze: SnoozeSetting.fromJson(
          (json['snooze'] as Map?)?.cast<String, Object?>() ?? const {},
        ),
        createdAt: DateTime.tryParse((json['createdAt'] as String?) ?? '')?.toLocal(),
      ).normalized();

  @override
  bool operator ==(Object other) =>
      other is Alarm &&
      other.id == id &&
      other.title == title &&
      other.time == time &&
      const SetEquality<Weekday>().equals(other.repeatDays, repeatDays) &&
      other.isEnabled == isEnabled &&
      other.sound == sound &&
      const ListEquality<AlarmTask>().equals(other.tasks, tasks) &&
      other.snooze == snooze &&
      other.createdAt == createdAt;

  @override
  int get hashCode => Object.hash(
        id,
        title,
        time,
        const SetEquality<Weekday>().hash(repeatDays),
        isEnabled,
        sound,
        const ListEquality<AlarmTask>().hash(tasks),
        snooze,
        createdAt,
      );
}

extension AlarmListOrdering on List<Alarm> {
  /// Ana sayfadaki gösterim sırası.
  ///
  /// Açık alarmlar önce gelir — kullanıcının sabah bakacağı şey onlardır.
  /// Her grup kendi içinde saate göre sıralanır. Aynı saatteki alarmlar
  /// oluşturulma zamanına, o da eşitse kimliğe göre ayrışır; böylece sıra her
  /// çağrıda aynı olur ve liste kendiliğinden yer değiştirmez.
  List<Alarm> sortedForDisplay() {
    final copy = List<Alarm>.of(this);
    copy.sort((a, b) {
      if (a.isEnabled != b.isEnabled) return a.isEnabled ? -1 : 1;
      final byTime = a.time.compareTo(b.time);
      if (byTime != 0) return byTime;
      final byCreation = a.createdAt.compareTo(b.createdAt);
      if (byCreation != 0) return byCreation;
      return a.id.compareTo(b.id);
    });
    return copy;
  }
}
