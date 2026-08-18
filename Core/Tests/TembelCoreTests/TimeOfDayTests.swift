import Foundation
import Testing

@testable import TembelCore

@Suite("TimeOfDay")
struct TimeOfDayTests {

    @Test("Saat ve dakika doğru ayrıştırılır")
    func hourAndMinute() {
        let time = TimeOfDay(hour: 7, minute: 30)
        #expect(time.hour == 7)
        #expect(time.minute == 30)
        #expect(time.minutesSinceMidnight == 450)
    }

    @Test("Gün sınırını aşan değerler sarar")
    func wrapsAroundDay() {
        #expect(TimeOfDay(hour: 25, minute: 0) == TimeOfDay(hour: 1, minute: 0))
        #expect(TimeOfDay(hour: 24, minute: 0) == TimeOfDay(hour: 0, minute: 0))
        #expect(TimeOfDay(minutesSinceMidnight: -30) == TimeOfDay(hour: 23, minute: 30))
        #expect(TimeOfDay(minutesSinceMidnight: -1) == TimeOfDay(hour: 23, minute: 59))
    }

    @Test("Geçersiz TimeOfDay üretilemez")
    func alwaysInValidRange() {
        for raw in stride(from: -5000, through: 5000, by: 137) {
            let time = TimeOfDay(minutesSinceMidnight: raw)
            #expect((0..<TimeOfDay.minutesPerDay).contains(time.minutesSinceMidnight))
            #expect((0...23).contains(time.hour))
            #expect((0...59).contains(time.minute))
        }
    }

    @Test("Dakika ekleme gece yarısını doğru geçer")
    func addingMinutesCrossesMidnight() {
        let time = TimeOfDay(hour: 23, minute: 50)
        #expect(time.adding(minutes: 20) == TimeOfDay(hour: 0, minute: 10))
        #expect(time.adding(minutes: -20) == TimeOfDay(hour: 23, minute: 30))
    }

    @Test("Sıralama saat sırasına göredir")
    func comparable() {
        #expect(TimeOfDay(hour: 6, minute: 0) < TimeOfDay(hour: 7, minute: 30))
        #expect(TimeOfDay(hour: 7, minute: 29) < TimeOfDay(hour: 7, minute: 30))
    }

    @Test("JSON'a düz sayı olarak yazılır")
    func encodesAsPlainInteger() throws {
        let data = try JSONEncoder().encode(TimeOfDay(hour: 7, minute: 30))
        #expect(String(data: data, encoding: .utf8) == "450")
    }

    @Test("Bozuk JSON değeri geçerli aralığa çekilir")
    func decodingOutOfRangeValueIsSafe() throws {
        let data = Data("99999".utf8)
        let decoded = try JSONDecoder().decode(TimeOfDay.self, from: data)
        #expect((0..<TimeOfDay.minutesPerDay).contains(decoded.minutesSinceMidnight))
    }

    @Test("dateComponents doğru alanları taşır")
    func dateComponentsMapping() {
        let components = TimeOfDay(hour: 7, minute: 30).dateComponents
        #expect(components.hour == 7)
        #expect(components.minute == 30)
    }
}
