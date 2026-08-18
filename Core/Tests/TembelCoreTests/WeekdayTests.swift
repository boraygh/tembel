import Foundation
import Testing

@testable import TembelCore

@Suite("Weekday")
struct WeekdayTests {

    /// UTC sabitlenmiş takvim — testler makinenin saat dilimine göre değişmemeli.
    private static func utcCalendar() -> Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        return calendar
    }

    private static func date(_ year: Int, _ month: Int, _ day: Int) -> Date {
        let calendar = utcCalendar()
        let components = DateComponents(year: year, month: month, day: day, hour: 12)
        guard let date = calendar.date(from: components) else {
            fatalError("Test tarihi oluşturulamadı: \(year)-\(month)-\(day)")
        }
        return date
    }

    @Test("rawValue, Calendar.weekday ile birebir eşleşir")
    func rawValueMatchesCalendarComponent() {
        let calendar = Self.utcCalendar()
        for weekday in Weekday.allCases {
            let reference = Self.date(2026, 8, 17)  // Pazartesi
            let offset = (weekday.mondayFirstIndex)
            let shifted = calendar.date(byAdding: .day, value: offset, to: reference)!
            let component = calendar.component(.weekday, from: shifted)
            #expect(component == weekday.rawValue)
        }
    }

    @Test("Bilinen bir tarih doğru güne çözümlenir")
    func knownDateResolvesCorrectly() {
        let calendar = Self.utcCalendar()
        // 2026-08-17 bir Pazartesidir.
        #expect(Weekday.from(Self.date(2026, 8, 17), calendar: calendar) == .monday)
        #expect(Weekday.from(Self.date(2026, 8, 22), calendar: calendar) == .saturday)
        #expect(Weekday.from(Self.date(2026, 8, 23), calendar: calendar) == .sunday)
    }

    @Test("mondayFirstIndex Pazartesi'den başlar")
    func mondayFirstIndexing() {
        #expect(Weekday.monday.mondayFirstIndex == 0)
        #expect(Weekday.friday.mondayFirstIndex == 4)
        #expect(Weekday.saturday.mondayFirstIndex == 5)
        #expect(Weekday.sunday.mondayFirstIndex == 6)
    }

    @Test("orderedMondayFirst tam ve doğru sıradadır")
    func orderedMondayFirstIsComplete() {
        #expect(Weekday.orderedMondayFirst == [
            .monday, .tuesday, .wednesday, .thursday, .friday, .saturday, .sunday
        ])
    }

    @Test("Comparable, Pazar'ı haftanın sonuna koyar")
    func sundaySortsLast() {
        #expect(Weekday.monday < Weekday.sunday)
        #expect(Weekday.saturday < Weekday.sunday)
        #expect([Weekday.sunday, .wednesday, .monday].sorted() == [.monday, .wednesday, .sunday])
    }

    @Test("Hazır kümeler doğru içeriğe sahiptir")
    func presetSets() {
        #expect(Set<Weekday>.weekdays.count == 5)
        #expect(Set<Weekday>.weekend == [.saturday, .sunday])
        #expect(Set<Weekday>.everyday.count == 7)
        #expect(Set<Weekday>.weekdays.isDisjoint(with: Set<Weekday>.weekend))
        #expect(Set<Weekday>.weekdays.union(Set<Weekday>.weekend) == .everyday)
    }

    @Test("Codable gidiş-dönüşü değeri korur")
    func codableRoundTrip() throws {
        let original = Set<Weekday>.weekdays
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Set<Weekday>.self, from: data)
        #expect(decoded == original)
    }
}
