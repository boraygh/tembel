import Foundation

/// Erteleme ayarı.
///
/// `maxCount` kasıtlı olarak zorunludur: sınırsız erteleme, uygulamanın tüm
/// amacını ortadan kaldırır. Sınıra ulaşıldığında erteleme butonu kaybolur ve
/// görevleri tamamlamaktan başka yol kalmaz.
public struct SnoozeSetting: Codable, Sendable, Hashable {

    public static let durationRange = 1...30
    public static let maxCountRange = 1...5

    public var isEnabled: Bool
    /// Erteleme süresi (dakika).
    public var durationMinutes: Int
    /// Bir alarm çalışında en fazla kaç kez ertelenebileceği.
    public var maxCount: Int

    public init(isEnabled: Bool, durationMinutes: Int, maxCount: Int) {
        self.isEnabled = isEnabled
        self.durationMinutes = durationMinutes
        self.maxCount = maxCount
    }

    /// Varsayılan: erteleme kapalı.
    ///
    /// Uygulamanın vaadi "kolayca susturamamak" olduğu için erteleme
    /// varsayılan olarak kapalı gelir; açmak kullanıcının bilinçli tercihidir.
    public static let disabled = SnoozeSetting(
        isEnabled: false,
        durationMinutes: 5,
        maxCount: 1
    )

    public func normalized() -> SnoozeSetting {
        SnoozeSetting(
            isEnabled: isEnabled,
            durationMinutes: durationMinutes.clamped(to: Self.durationRange),
            maxCount: maxCount.clamped(to: Self.maxCountRange)
        )
    }
}
