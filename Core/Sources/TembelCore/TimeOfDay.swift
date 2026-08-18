import Foundation

/// Günün bir saati — tarihten bağımsız (07:30 gibi).
///
/// Tek bir `Int` olarak saklanır. Bunun iki nedeni var:
/// - Geçersiz durum üretilemez: saat/dakika ayrı ayrı tutulsaydı 25:70 gibi
///   bir değer temsil edilebilirdi.
/// - JSON'da düz bir sayı olarak yazılır, `{"hour":7,"minute":30}` gürültüsü olmaz.
public struct TimeOfDay: Codable, Sendable, Hashable, Comparable {

    public static let minutesPerDay = 24 * 60

    /// Gece yarısından itibaren geçen dakika. Her zaman `0..<1440` aralığındadır.
    public let minutesSinceMidnight: Int

    /// Aralık dışındaki değerleri gün içine sarar.
    ///
    /// Örnek: `25 * 60` → 01:00, `-30` → 23:30. Bu davranış follow-up alarm
    /// zinciri hesabında (gece yarısını geçen alarmlar) işimize yarayacak.
    public init(minutesSinceMidnight raw: Int) {
        let day = Self.minutesPerDay
        self.minutesSinceMidnight = ((raw % day) + day) % day
    }

    public init(hour: Int, minute: Int) {
        self.init(minutesSinceMidnight: hour * 60 + minute)
    }

    public var hour: Int { minutesSinceMidnight / 60 }
    public var minute: Int { minutesSinceMidnight % 60 }

    /// Bu saate dakika ekler, gerekirse gün sınırını sararak.
    public func adding(minutes: Int) -> TimeOfDay {
        TimeOfDay(minutesSinceMidnight: minutesSinceMidnight + minutes)
    }

    public static func < (lhs: TimeOfDay, rhs: TimeOfDay) -> Bool {
        lhs.minutesSinceMidnight < rhs.minutesSinceMidnight
    }

    // Tek değerli kodlama — bozuk veri geldiğinde de init sarma yaptığı için
    // decode asla geçersiz bir TimeOfDay üretemez.
    public init(from decoder: any Decoder) throws {
        let container = try decoder.singleValueContainer()
        self.init(minutesSinceMidnight: try container.decode(Int.self))
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(minutesSinceMidnight)
    }
}

public extension TimeOfDay {
    /// `DateComponents` karşılığı — AlarmKit ve `Calendar` ile kullanım için.
    var dateComponents: DateComponents {
        DateComponents(hour: hour, minute: minute)
    }
}
