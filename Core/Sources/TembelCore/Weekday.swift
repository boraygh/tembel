import Foundation

/// Haftanın bir günü.
///
/// `rawValue` değerleri kasıtlı olarak Foundation `Calendar`'ın `weekday`
/// bileşeniyle birebir aynıdır (1 = Pazar … 7 = Cumartesi). Böylece
/// `Calendar.component(.weekday:)` sonucu ve `DateComponents.weekday` alanı
/// hiçbir dönüşüm yapılmadan kullanılabilir — alarm zamanlamasında en sık
/// hata çıkan yer burasıdır.
public enum Weekday: Int, CaseIterable, Codable, Sendable, Identifiable, Comparable {
    case sunday = 1
    case monday = 2
    case tuesday = 3
    case wednesday = 4
    case thursday = 5
    case friday = 6
    case saturday = 7

    public var id: Int { rawValue }

    /// Pazartesi'yi haftanın ilk günü kabul eden sıralama indeksi (0…6).
    ///
    /// Türkiye ve Avrupa'da hafta Pazartesi başlar, ancak `Calendar.weekday`
    /// Pazar'dan başlar. UI sıralaması bu değere göre yapılır.
    public var mondayFirstIndex: Int {
        (rawValue + 5) % 7
    }

    /// Haftanın günleri, Pazartesi'den Pazar'a sıralı.
    public static let orderedMondayFirst: [Weekday] =
        Weekday.allCases.sorted { $0.mondayFirstIndex < $1.mondayFirstIndex }

    public static func < (lhs: Weekday, rhs: Weekday) -> Bool {
        lhs.mondayFirstIndex < rhs.mondayFirstIndex
    }
}

public extension Weekday {
    /// Belirtilen tarihin haftanın hangi gününe denk geldiğini döndürür.
    ///
    /// - Parameters:
    ///   - date: Sorgulanacak tarih.
    ///   - calendar: Kullanılacak takvim. Zaman dilimi bu takvimden gelir.
    static func from(_ date: Date, calendar: Calendar) -> Weekday {
        let component = calendar.component(.weekday, from: date)
        // Calendar.weekday her zaman 1…7 aralığındadır; bu yüzden bu
        // dönüşümün başarısız olması mümkün değildir.
        guard let weekday = Weekday(rawValue: component) else {
            preconditionFailure("Calendar 1...7 aralığı dışında weekday döndürdü: \(component)")
        }
        return weekday
    }
}

public extension Set<Weekday> {
    /// Hafta içi: Pazartesi–Cuma.
    static var weekdays: Set<Weekday> {
        [.monday, .tuesday, .wednesday, .thursday, .friday]
    }

    /// Hafta sonu: Cumartesi–Pazar.
    static var weekend: Set<Weekday> {
        [.saturday, .sunday]
    }

    /// Her gün.
    static var everyday: Set<Weekday> {
        Set(Weekday.allCases)
    }
}
