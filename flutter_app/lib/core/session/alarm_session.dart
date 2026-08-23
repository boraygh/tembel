import 'package:collection/collection.dart';

import '../models/alarm.dart';
import '../models/alarm_task.dart';
import '../models/clock_time.dart';
import '../models/snooze_setting.dart';

enum SessionPhase { running, snoozed, finished }

/// Çalan bir alarmın oturumu — görevlerin yürütüldüğü çalışma anı durumu.
///
/// `Alarm` yapılandırmadır ve kullanıcı tarafından düzenlenir; `AlarmSession`
/// tek bir çalışa aittir ve alarm bittiğinde atılır. Görevler oturum açılırken
/// **kopyalanır**: kullanıcı alarm çalarken alarmı düzenlese bile yürüyen görev
/// listesi değişmez.
///
/// JSON'a yazılabilir çünkü uygulama görev ekranındayken öldürülebilir
/// (force-quit, çökme, bellek baskısı). Oturum diske yazıldığı için uygulama
/// yeniden açıldığında kaldığı görevden devam eder.
class AlarmSession {
  AlarmSession({
    required this.id,
    required this.alarmId,
    required this.alarmTitle,
    required this.alarmTime,
    required this.startedAt,
    required this.tasks,
    required this.snooze,
    List<String>? completedTaskIds,
    this.snoozeCount = 0,
    DateTime? initialSnoozedUntil,
    DateTime? finishedAt,
  }) : completedTaskIds = completedTaskIds ?? <String>[],
       _snoozedUntil = initialSnoozedUntil,
       _finishedAt = finishedAt ?? (tasks.isEmpty ? startedAt : null);

  /// Alarm çaldığında yeni oturum açar.
  factory AlarmSession.start({
    required String id,
    required Alarm alarm,
    required DateTime startedAt,
  }) => AlarmSession(
    id: id,
    alarmId: alarm.id,
    // Başlık ve saat kopyalanır: kullanıcı alarm çalarken alarmı silebilir,
    // oturum ekranda ne göstereceğini bilmeli.
    alarmTitle: alarm.title,
    alarmTime: alarm.time,
    startedAt: startedAt,
    tasks: List.unmodifiable(alarm.tasks),
    snooze: alarm.snooze,
  );

  final String id;
  final String alarmId;
  final String alarmTitle;
  final ClockTime alarmTime;
  final DateTime startedAt;

  /// Alarm çaldığı andaki görev listesi ve sırası.
  final List<AlarmTask> tasks;

  /// Alarm çaldığı andaki erteleme ayarı.
  final SnoozeSetting snooze;

  /// Tamamlanan görevler, tamamlanma sırasıyla.
  final List<String> completedTaskIds;

  int snoozeCount;
  DateTime? _snoozedUntil;
  DateTime? _finishedAt;

  DateTime? get snoozedUntil => _snoozedUntil;
  DateTime? get finishedAt => _finishedAt;

  bool get isComplete => completedTaskIds.length >= tasks.length;

  SessionPhase get phase {
    if (_finishedAt != null) return SessionPhase.finished;
    if (_snoozedUntil != null) return SessionPhase.snoozed;
    return SessionPhase.running;
  }

  /// Şu an yapılması gereken görev. Sıra zorunludur — görev atlanamaz.
  AlarmTask? get currentTask => isComplete ? null : tasks[completedTaskIds.length];

  /// Yürüyen görevin sırası (1'den başlar). Tamamlanmışsa `null`.
  int? get currentTaskNumber => isComplete ? null : completedTaskIds.length + 1;

  int get completedCount => completedTaskIds.length;

  List<AlarmTask> get remainingTasks => tasks.sublist(completedTaskIds.length);

  double get progress => tasks.isEmpty ? 1 : completedTaskIds.length / tasks.length;

  /// Erteleme hâlâ mümkün mü.
  ///
  /// Sınırsız erteleme uygulamanın amacını yok ederdi; hakkı biten kullanıcı
  /// için görevleri yapmaktan başka yol kalmaz.
  bool get canSnooze {
    if (!snooze.isEnabled || isComplete) return false;
    if (_snoozedUntil != null) return false;
    return snoozeCount < snooze.maxCount;
  }

  int get remainingSnoozeCount =>
      snooze.isEnabled ? (snooze.maxCount - snoozeCount).clamp(0, snooze.maxCount) : 0;

  /// Yürüyen görevi tamamlar.
  ///
  /// [taskId] verilirse yalnızca yürüyen görevle eşleştiğinde işler; bu, ekranda
  /// eski bir görev duruyorken gelen geç bir dokunuşun yanlış görevi
  /// tamamlamasını engeller.
  bool completeCurrentTask({String? taskId, required DateTime at}) {
    if (_finishedAt != null || _snoozedUntil != null) return false;
    final current = currentTask;
    if (current == null) return false;
    if (taskId != null && taskId != current.id) return false;

    completedTaskIds.add(current.id);
    if (isComplete) _finishedAt = at;
    return true;
  }

  /// Alarmı erteler ve uyanma zamanını döndürür. Hak kalmamışsa `null`.
  DateTime? snoozeNow(DateTime at) {
    if (!canSnooze) return null;
    final wake = at.add(Duration(minutes: snooze.durationMinutes));
    snoozeCount += 1;
    _snoozedUntil = wake;
    return wake;
  }

  /// Ertelemeden geri döner. Süre dolmamışsa hiçbir şey yapmaz.
  bool resumeFromSnooze(DateTime at) {
    final until = _snoozedUntil;
    if (until == null || at.isBefore(until)) return false;
    _snoozedUntil = null;
    return true;
  }

  /// Görev ilerlemesini sıfırlar ama erteleme hakkını geri vermez.
  ///
  /// Erteleme sayacının korunması kasıtlıdır: aksi hâlde kullanıcı görevi
  /// baştan başlatarak sınırsız erteleme hakkı üretebilirdi.
  void restartTasks() {
    if (tasks.isEmpty) return;
    completedTaskIds.clear();
    _finishedAt = null;
  }

  Map<String, Object?> toJson() => {
    'id': id,
    'alarmId': alarmId,
    'alarmTitle': alarmTitle,
    'alarmTime': alarmTime.toJson(),
    'startedAt': startedAt.toUtc().toIso8601String(),
    'tasks': tasks.map((t) => t.toJson()).toList(),
    'snooze': snooze.toJson(),
    'completedTaskIds': completedTaskIds,
    'snoozeCount': snoozeCount,
    'snoozedUntil': _snoozedUntil?.toUtc().toIso8601String(),
    'finishedAt': _finishedAt?.toUtc().toIso8601String(),
  };

  factory AlarmSession.fromJson(Map<String, Object?> json) {
    DateTime? parse(Object? value) =>
        value is String ? DateTime.tryParse(value)?.toLocal() : null;

    final tasks = ((json['tasks'] as List?) ?? const [])
        .whereType<Map>()
        .map((e) => AlarmTask.fromJson(e.cast<String, Object?>()))
        .toList();

    return AlarmSession(
      id: (json['id'] as String?) ?? '',
      alarmId: (json['alarmId'] as String?) ?? '',
      alarmTitle: (json['alarmTitle'] as String?) ?? '',
      alarmTime: ClockTime.fromJson(json['alarmTime']),
      startedAt: parse(json['startedAt']) ?? DateTime.now(),
      tasks: List.unmodifiable(tasks),
      snooze: SnoozeSetting.fromJson(
        (json['snooze'] as Map?)?.cast<String, Object?>() ?? const {},
      ),
      completedTaskIds: ((json['completedTaskIds'] as List?) ?? const [])
          .whereType<String>()
          .toList(),
      snoozeCount: (json['snoozeCount'] as int?) ?? 0,
      initialSnoozedUntil: parse(json['snoozedUntil']),
      finishedAt: parse(json['finishedAt']),
    );
  }

  @override
  bool operator ==(Object other) =>
      other is AlarmSession &&
      other.id == id &&
      other.alarmId == alarmId &&
      other.alarmTitle == alarmTitle &&
      other.alarmTime == alarmTime &&
      other.startedAt == startedAt &&
      const ListEquality<AlarmTask>().equals(other.tasks, tasks) &&
      other.snooze == snooze &&
      const ListEquality<String>().equals(other.completedTaskIds, completedTaskIds) &&
      other.snoozeCount == snoozeCount &&
      other._snoozedUntil == _snoozedUntil &&
      other._finishedAt == _finishedAt;

  @override
  int get hashCode => Object.hash(
    id,
    alarmId,
    alarmTime,
    startedAt,
    const ListEquality<AlarmTask>().hash(tasks),
    const ListEquality<String>().hash(completedTaskIds),
    snoozeCount,
    _snoozedUntil,
    _finishedAt,
  );
}
