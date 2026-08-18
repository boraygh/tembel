import Foundation

/// Premium ile açılan yetenekler.
///
/// Bu listede kasıtlı olarak **bulunmayan** şeyler: alarmın çalması, takip
/// alarm zinciri, görevlerin alarmı kapatmayı zorunlu kılması. Uygulamanın
/// temel vaadi bunlar; ödeme duvarının arkasına konursa ücretsiz kullanıcı
/// "alarm kurdum" sanıp uyanamaz. Premium adet, çeşitlilik ve konfor satar —
/// güvenilirlik satmaz.
public enum PremiumFeature: String, CaseIterable, Sendable, Identifiable, Codable {
    /// Sınırsız alarm (ücretsizde `FeatureGate.freeAlarmLimit` kadar).
    case unlimitedAlarms
    /// Alarm başına daha fazla görev.
    case moreTasksPerAlarm
    /// Fotoğraf görevi.
    case photoTask
    /// Varsayılan dışındaki alarm sesleri.
    case allSounds
    /// Takip zincirinin sıklığını değiştirebilme.
    case customFollowUpChain

    public var id: String { rawValue }
}

/// Kullanıcının premium durumu.
public enum EntitlementStatus: Equatable, Sendable, Codable {
    case free
    /// Abonelik. `expiresAt` `nil` ise ömür boyu satın alma.
    case premium(expiresAt: Date?)

    /// Verilen anda premium geçerli mi.
    ///
    /// Süresi geçmiş abonelik ücretsiz sayılır — StoreKit yenilemeyi
    /// bildirene kadar kullanıcı ücretsiz kısıtlarla devam eder.
    public func isActive(at date: Date = Date()) -> Bool {
        switch self {
        case .free: false
        case .premium(let expiresAt): expiresAt.map { date < $0 } ?? true
        }
    }

    /// Ömür boyu satın alma mı.
    public var isLifetime: Bool {
        if case .premium(let expiresAt) = self { return expiresAt == nil }
        return false
    }
}

/// Hangi yeteneğin kime açık olduğuna karar verir.
///
/// Tüm sınırlar tek yerde toplandı; ekranlar kendi başına "premium mi?" diye
/// karar vermez. Böylece ücretsiz/premium ayrımı değiştiğinde tek dosya
/// düzenlenir ve testler değişikliği yakalar.
public struct FeatureGate: Sendable, Equatable {

    /// Ücretsiz kullanıcının kurabileceği alarm sayısı.
    ///
    /// İki alarm bilinçli seçim: bir hafta içi bir hafta sonu alarmı kurup
    /// uygulamayı gerçekten kullanabilmeli ki neye para verdiğini bilsin.
    public static let freeAlarmLimit = 2

    /// Ücretsiz kullanıcının bir alarma ekleyebileceği görev sayısı.
    public static let freeTaskLimitPerAlarm = 2

    /// Ücretsiz kullanıcıya açık görev türleri.
    public static let freeTaskKinds: Set<TaskKind> = [.shake, .math]

    public let status: EntitlementStatus
    /// Sınırların hesaplandığı an — abonelik süresi kontrolü için.
    public let referenceDate: Date

    public init(status: EntitlementStatus, referenceDate: Date = Date()) {
        self.status = status
        self.referenceDate = referenceDate
    }

    public var isPremium: Bool {
        status.isActive(at: referenceDate)
    }

    public func isAvailable(_ feature: PremiumFeature) -> Bool {
        isPremium
    }

    // MARK: - Sayısal sınırlar

    public var alarmLimit: Int {
        isPremium ? .max : Self.freeAlarmLimit
    }

    public var taskLimitPerAlarm: Int {
        isPremium ? Alarm.maxTaskCount : Self.freeTaskLimitPerAlarm
    }

    public func canAddAlarm(currentCount: Int) -> Bool {
        currentCount < alarmLimit
    }

    public func canAddTask(currentCount: Int) -> Bool {
        currentCount < taskLimitPerAlarm
    }

    // MARK: - İçerik sınırları

    public func isAvailable(_ kind: TaskKind) -> Bool {
        isPremium || Self.freeTaskKinds.contains(kind)
    }

    public var availableTaskKinds: [TaskKind] {
        TaskKind.allCases.filter { isAvailable($0) }
    }

    public func isAvailable(_ sound: AlarmSound) -> Bool {
        isPremium || sound == .systemDefault
    }

    /// Kullanıcının seçebileceği sesler.
    ///
    /// `AlarmSound.availableForSelection` ayrıca özel seslerin gerçek cihazda
    /// doğrulanıp doğrulanmadığını süzer; premium durumu bunun üstüne biner.
    public var availableSounds: [AlarmSound] {
        AlarmSound.availableForSelection.filter { isAvailable($0) }
    }
}
