import 'package:meta/meta.dart';

enum TaskKind {
  shake,
  math,
  photo;

  static TaskKind fromName(String? name) =>
      TaskKind.values.firstWhere((k) => k.name == name, orElse: () => TaskKind.shake);
}

enum MathDifficulty {
  easy,
  medium,
  hard;

  static MathDifficulty fromName(String? name) => MathDifficulty.values
      .firstWhere((d) => d.name == name, orElse: () => MathDifficulty.medium);
}

/// Bir görevin ayarları.
///
/// Sealed sınıf kullanılmasının nedeni: her görev türünün farklı ayarları var
/// ve tür ile ayarın uyumsuz kalması (shake görevinde `difficulty` alanı gibi)
/// tip düzeyinde imkânsız hale geliyor.
@immutable
sealed class TaskConfiguration {
  const TaskConfiguration();

  static const shakeCountMin = 3;
  static const shakeCountMax = 100;
  static const mathQuestionCountMin = 1;
  static const mathQuestionCountMax = 10;
  static const promptMaxLength = 80;

  TaskKind get kind;

  /// Ayarları geçerli aralıklara çeker. Diskten okunan veriye uygulanır.
  TaskConfiguration normalized();

  Map<String, Object?> toJson();

  /// Yeni görev eklerken kullanılan makul başlangıç değerleri.
  static TaskConfiguration makeDefault(TaskKind kind) => switch (kind) {
        TaskKind.shake => const ShakeConfiguration(count: 10),
        TaskKind.math =>
          const MathConfiguration(difficulty: MathDifficulty.medium, questionCount: 1),
        TaskKind.photo => const PhotoConfiguration(prompt: ''),
      };

  factory TaskConfiguration.fromJson(Map<String, Object?> json) {
    final kind = TaskKind.fromName(json['kind'] as String?);
    return switch (kind) {
      TaskKind.shake => ShakeConfiguration(count: (json['count'] as int?) ?? 10),
      TaskKind.math => MathConfiguration(
          difficulty: MathDifficulty.fromName(json['difficulty'] as String?),
          questionCount: (json['questionCount'] as int?) ?? 1,
        ),
      TaskKind.photo => PhotoConfiguration(prompt: (json['prompt'] as String?) ?? ''),
    }
        .normalized();
  }
}

@immutable
final class ShakeConfiguration extends TaskConfiguration {
  const ShakeConfiguration({required this.count});

  final int count;

  @override
  TaskKind get kind => TaskKind.shake;

  @override
  TaskConfiguration normalized() => ShakeConfiguration(
        count: count.clamp(
          TaskConfiguration.shakeCountMin,
          TaskConfiguration.shakeCountMax,
        ),
      );

  @override
  Map<String, Object?> toJson() => {'kind': kind.name, 'count': count};

  @override
  bool operator ==(Object other) =>
      other is ShakeConfiguration && other.count == count;

  @override
  int get hashCode => Object.hash(kind, count);
}

@immutable
final class MathConfiguration extends TaskConfiguration {
  const MathConfiguration({required this.difficulty, required this.questionCount});

  final MathDifficulty difficulty;
  final int questionCount;

  @override
  TaskKind get kind => TaskKind.math;

  @override
  TaskConfiguration normalized() => MathConfiguration(
        difficulty: difficulty,
        questionCount: questionCount.clamp(
          TaskConfiguration.mathQuestionCountMin,
          TaskConfiguration.mathQuestionCountMax,
        ),
      );

  @override
  Map<String, Object?> toJson() =>
      {'kind': kind.name, 'difficulty': difficulty.name, 'questionCount': questionCount};

  @override
  bool operator ==(Object other) =>
      other is MathConfiguration &&
      other.difficulty == difficulty &&
      other.questionCount == questionCount;

  @override
  int get hashCode => Object.hash(kind, difficulty, questionCount);
}

@immutable
final class PhotoConfiguration extends TaskConfiguration {
  const PhotoConfiguration({required this.prompt});

  final String prompt;

  @override
  TaskKind get kind => TaskKind.photo;

  @override
  TaskConfiguration normalized() {
    final trimmed = prompt.trim();
    return PhotoConfiguration(
      prompt: trimmed.length > TaskConfiguration.promptMaxLength
          ? trimmed.substring(0, TaskConfiguration.promptMaxLength)
          : trimmed,
    );
  }

  @override
  Map<String, Object?> toJson() => {'kind': kind.name, 'prompt': prompt};

  @override
  bool operator ==(Object other) =>
      other is PhotoConfiguration && other.prompt == prompt;

  @override
  int get hashCode => Object.hash(kind, prompt);
}

/// Alarmı kapatmak için tamamlanması gereken tek bir görev.
///
/// Görevin sırası bu tipte **tutulmaz** — sıra, `Alarm.tasks` listesindeki
/// konumdur. Ayrı bir `order` alanı iki doğruluk kaynağı yaratırdı.
@immutable
class AlarmTask {
  const AlarmTask({required this.id, required this.configuration});

  final String id;
  final TaskConfiguration configuration;

  TaskKind get kind => configuration.kind;

  AlarmTask copyWith({TaskConfiguration? configuration}) =>
      AlarmTask(id: id, configuration: configuration ?? this.configuration);

  AlarmTask normalized() =>
      AlarmTask(id: id, configuration: configuration.normalized());

  Map<String, Object?> toJson() => {'id': id, 'configuration': configuration.toJson()};

  factory AlarmTask.fromJson(Map<String, Object?> json) => AlarmTask(
        id: (json['id'] as String?) ?? '',
        configuration: TaskConfiguration.fromJson(
          (json['configuration'] as Map?)?.cast<String, Object?>() ?? const {},
        ),
      );

  @override
  bool operator ==(Object other) =>
      other is AlarmTask && other.id == id && other.configuration == configuration;

  @override
  int get hashCode => Object.hash(id, configuration);
}
