import 'package:meta/meta.dart';

import '../models/alarm.dart';
import '../models/alarm_sound.dart';
import '../models/alarm_task.dart';

/// Premium ile açılan yetenekler.
///
/// Bu listede kasıtlı olarak **bulunmayan** şeyler: alarmın çalması, takip
/// alarm zinciri, görevlerin alarmı kapatmayı zorunlu kılması. Uygulamanın
/// temel vaadi bunlar; ödeme duvarının arkasına konursa ücretsiz kullanıcı
/// "alarm kurdum" sanıp uyanamaz. Premium adet, çeşitlilik ve konfor satar —
/// güvenilirlik satmaz.
enum PremiumFeature {
  unlimitedAlarms,
  moreTasksPerAlarm,
  photoTask,
  allSounds,
  customFollowUpChain;

  /// Ödeme duvarındaki gösterim sırası — en güçlü gerekçe önce.
  static const List<PremiumFeature> displayOrder = [
    PremiumFeature.unlimitedAlarms,
    PremiumFeature.photoTask,
    PremiumFeature.moreTasksPerAlarm,
    PremiumFeature.allSounds,
    PremiumFeature.customFollowUpChain,
  ];
}

/// Kullanıcının premium durumu.
@immutable
class EntitlementStatus {
  const EntitlementStatus._(this.isPurchased, this.expiresAt);

  /// Ücretsiz kullanıcı.
  static const EntitlementStatus free = EntitlementStatus._(false, null);

  /// Ömür boyu satın alma.
  static const EntitlementStatus lifetime = EntitlementStatus._(true, null);

  /// Süreli abonelik.
  factory EntitlementStatus.subscription(DateTime expiresAt) =>
      EntitlementStatus._(true, expiresAt);

  final bool isPurchased;
  final DateTime? expiresAt;

  bool get isLifetime => isPurchased && expiresAt == null;

  /// Verilen anda premium geçerli mi.
  ///
  /// Süresi geçmiş abonelik ücretsiz sayılır — mağaza yenilemeyi bildirene
  /// kadar kullanıcı ücretsiz kısıtlarla devam eder.
  bool isActiveAt(DateTime date) {
    if (!isPurchased) return false;
    final expiry = expiresAt;
    return expiry == null || date.isBefore(expiry);
  }

  Map<String, Object?> toJson() => {
    'isPurchased': isPurchased,
    'expiresAt': expiresAt?.toUtc().toIso8601String(),
  };

  factory EntitlementStatus.fromJson(Map<String, Object?> json) {
    if ((json['isPurchased'] as bool?) != true) return free;
    final raw = json['expiresAt'] as String?;
    final expiry = raw == null ? null : DateTime.tryParse(raw)?.toLocal();
    return expiry == null ? lifetime : EntitlementStatus.subscription(expiry);
  }

  @override
  bool operator ==(Object other) =>
      other is EntitlementStatus &&
      other.isPurchased == isPurchased &&
      other.expiresAt == expiresAt;

  @override
  int get hashCode => Object.hash(isPurchased, expiresAt);
}

/// Hangi yeteneğin kime açık olduğuna karar verir.
///
/// Tüm sınırlar tek yerde toplandı; ekranlar kendi başına "premium mi?" diye
/// karar vermez. Böylece ayrım değiştiğinde tek dosya düzenlenir ve testler
/// değişikliği yakalar.
@immutable
class FeatureGate {
  const FeatureGate({required this.status, required this.referenceDate});

  /// Ücretsiz kullanıcının kurabileceği alarm sayısı.
  ///
  /// İki alarm bilinçli seçim: bir hafta içi bir hafta sonu alarmı kurup
  /// uygulamayı gerçekten kullanabilmeli ki neye para verdiğini bilsin.
  static const int freeAlarmLimit = 2;

  /// Ücretsiz kullanıcının bir alarma ekleyebileceği görev sayısı.
  static const int freeTaskLimitPerAlarm = 2;

  /// Ücretsiz kullanıcıya açık görev türleri.
  static const Set<TaskKind> freeTaskKinds = {TaskKind.shake, TaskKind.math};

  final EntitlementStatus status;

  /// Sınırların hesaplandığı an — abonelik süresi kontrolü için.
  final DateTime referenceDate;

  bool get isPremium => status.isActiveAt(referenceDate);

  bool hasFeature(PremiumFeature feature) => isPremium;

  int get alarmLimit => isPremium ? 1 << 30 : freeAlarmLimit;

  int get taskLimitPerAlarm => isPremium ? Alarm.maxTaskCount : freeTaskLimitPerAlarm;

  bool canAddAlarm(int currentCount) => currentCount < alarmLimit;

  bool canAddTask(int currentCount) => currentCount < taskLimitPerAlarm;

  bool hasTaskKind(TaskKind kind) => isPremium || freeTaskKinds.contains(kind);

  List<TaskKind> get availableTaskKinds => TaskKind.values.where(hasTaskKind).toList();

  bool hasSound(AlarmSound sound) => isPremium || sound == AlarmSound.systemDefault;

  /// Kullanıcının seçebileceği sesler.
  ///
  /// `AlarmSound.availableForSelection` ayrıca özel seslerin gerçek cihazda
  /// doğrulanıp doğrulanmadığını süzer; premium durumu bunun üstüne biner.
  List<AlarmSound> get availableSounds =>
      AlarmSound.availableForSelection.where(hasSound).toList();
}
