import Foundation
import Testing

@testable import TembelCore

@Suite("AlarmScheduler")
struct AlarmSchedulerTests {

    /// Türkiye saati — yaz saati uygulaması yok, bu yüzden temel testlerde
    /// hesabı bulandırmaz.
    private static func istanbul() -> Calendar {
        calendar(timeZone: "Europe/Istanbul")
    }

    private static func calendar(timeZone identifier: String) -> Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: identifier)!
        return calendar
    }

    private static func date(
        _ year: Int, _ month: Int, _ day: Int,
        _ hour: Int = 0, _ minute: Int = 0,
        in calendar: Calendar
    ) -> Date {
        calendar.date(from: DateComponents(
            year: year, month: month, day: day, hour: hour, minute: minute
        ))!
    }

    private func alarm(
        hour: Int,
        minute: Int,
        days: Set<Weekday> = [],
        enabled: Bool = true,
        taskCount: Int = 1
    ) -> Alarm {
        Alarm(
            time: TimeOfDay(hour: hour, minute: minute),
            repeatDays: days,
            isEnabled: enabled,
            tasks: (0..<taskCount).map { _ in AlarmTask(configuration: .shake(count: 10)) }
        )
    }

    // MARK: - Sonraki çalma zamanı

    @Test("Tek seferlik alarm bugünkü saati henüz geçmediyse bugün çalar")
    func oneShotLaterToday() {
        let calendar = Self.istanbul()
        // 2026-08-17 Pazartesi, saat 06:00. Alarm 07:30.
        let reference = Self.date(2026, 8, 17, 6, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 17, 7, 30, in: calendar))
    }

    @Test("Tek seferlik alarm saati geçtiyse ertesi güne kayar")
    func oneShotTomorrow() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 9, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 18, 7, 30, in: calendar))
    }

    @Test("Tam alarm saatinde referans verilirse bir sonraki güne geçer")
    func exactlyAtAlarmTimeMovesToNext() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 7, 30, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 18, 7, 30, in: calendar))
    }

    @Test("Tekrarlı alarm bugün de uygunsa bugünü seçer")
    func repeatingPicksToday() {
        let calendar = Self.istanbul()
        // Pazartesi 06:00, alarm Pzt/Çar/Cum 07:30.
        let reference = Self.date(2026, 8, 17, 6, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30, days: [.monday, .wednesday, .friday]),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 17, 7, 30, in: calendar))
    }

    @Test("Tekrarlı alarm bugünü kaçırdıysa listedeki bir sonraki güne gider")
    func repeatingSkipsToNextSelectedDay() {
        let calendar = Self.istanbul()
        // Pazartesi 09:00 — bugünkü 07:30 kaçtı, sıradaki Çarşamba.
        let reference = Self.date(2026, 8, 17, 9, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30, days: [.monday, .wednesday, .friday]),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 19, 7, 30, in: calendar))
    }

    @Test("Haftanın tek günü seçiliyse bir hafta sonrasına sarar")
    func repeatingWrapsToNextWeek() {
        let calendar = Self.istanbul()
        // Pazartesi 09:00, alarm yalnızca Pazartesi.
        let reference = Self.date(2026, 8, 17, 9, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 7, minute: 30, days: [.monday]),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 24, 7, 30, in: calendar))
    }

    @Test("Hafta sonu alarmı Cuma gününden Cumartesiye gider")
    func weekendFromFriday() {
        let calendar = Self.istanbul()
        // 2026-08-21 Cuma.
        let reference = Self.date(2026, 8, 21, 12, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 9, minute: 0, days: .weekend),
            after: reference,
            calendar: calendar
        )
        #expect(next == Self.date(2026, 8, 22, 9, 0, in: calendar))
    }

    @Test("Kapalı alarmın da zamanı hesaplanabilir — süzme işi planlayıcının")
    func disabledAlarmStillHasNextOccurrence() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 6, 0, in: calendar)
        let subject = alarm(hour: 7, minute: 30, enabled: false)
        #expect(AlarmScheduler.nextOccurrence(of: subject, after: reference, calendar: calendar) != nil)
        #expect(AlarmScheduler.firePlan(for: subject, after: reference, calendar: calendar).isEmpty)
    }

    // MARK: - Yaz saati

    @Test("İleri alınan saatte var olmayan alarm zamanı bir sonraki geçerli zamana kayar")
    func springForwardSkipsMissingTime() throws {
        // ABD'de 2026-03-08'de saatler 02:00'den 03:00'e alınır; 02:30 yoktur.
        let calendar = Self.calendar(timeZone: "America/New_York")
        let reference = Self.date(2026, 3, 7, 12, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 2, minute: 30),
            after: reference,
            calendar: calendar
        )
        let resolved = try #require(next)
        let components = calendar.dateComponents([.year, .month, .day, .hour], from: resolved)
        #expect(components.year == 2026)
        #expect(components.month == 3)
        #expect(components.day == 8)
        // Var olmayan 02:30 yerine geçerli bir zamana kaymalı, atlanmamalı.
        #expect(components.hour != 2)
    }

    @Test("Geri alınan saatte alarm kaybolmaz")
    func fallBackStillResolves() {
        // ABD'de 2026-11-01'de 01:00-02:00 arası iki kez yaşanır.
        let calendar = Self.calendar(timeZone: "America/New_York")
        let reference = Self.date(2026, 10, 31, 12, 0, in: calendar)
        let next = AlarmScheduler.nextOccurrence(
            of: alarm(hour: 1, minute: 30),
            after: reference,
            calendar: calendar
        )
        #expect(next != nil)
    }

    // MARK: - Takip zinciri

    @Test("Görevli alarm ana alarm ve takip zinciri üretir")
    func chainForTaskAlarm() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 6, 0, in: calendar)
        let subject = alarm(hour: 7, minute: 30, taskCount: 2)

        let plan = AlarmScheduler.firePlan(for: subject, after: reference, calendar: calendar)
        let main = Self.date(2026, 8, 17, 7, 30, in: calendar)

        #expect(plan.count == FollowUpPolicy.standard.totalFireCount)
        #expect(plan.map(\.sequence) == [0, 1, 2, 3, 4])
        #expect(plan.map(\.date) == [
            main,
            main.addingTimeInterval(60),
            main.addingTimeInterval(180),
            main.addingTimeInterval(360),
            main.addingTimeInterval(600)
        ])
        #expect(plan.first?.isFollowUp == false)
        let remainderAreFollowUps = plan.dropFirst().allSatisfy(\.isFollowUp)
        #expect(remainderAreFollowUps)
    }

    @Test("Görevsiz alarmda takip zinciri kurulmaz")
    func noChainWithoutTasks() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 6, 0, in: calendar)
        let plan = AlarmScheduler.firePlan(
            for: alarm(hour: 7, minute: 30, taskCount: 0),
            after: reference,
            calendar: calendar
        )
        #expect(plan.count == 1)
        #expect(plan.first?.isFollowUp == false)
    }

    @Test("Zincir kimlikleri benzersiz, kararlı ve geri çözülebilir")
    func fireIdentifiersAreStableAndReversible() {
        let subject = alarm(hour: 7, minute: 30)
        let start = Date(timeIntervalSince1970: 1_800_000_000)

        let first = AlarmScheduler.firePlan(alarmID: subject.id, firstFireAt: start)
        let second = AlarmScheduler.firePlan(alarmID: subject.id, firstFireAt: start)

        #expect(first == second)
        #expect(Set(first.map(\.id)).count == first.count)
        for fire in first {
            #expect(ScheduledFire.alarmID(fromFireID: fire.id) == subject.id)
        }
        #expect(ScheduledFire.alarmID(fromFireID: "geçersiz") == nil)
    }

    @Test("Özel politika ile zincir uzunluğu değiştirilebilir")
    func customPolicy() {
        let start = Date(timeIntervalSince1970: 1_800_000_000)
        let policy = FollowUpPolicy(delays: [30, 90])
        let plan = AlarmScheduler.firePlan(alarmID: UUID(), firstFireAt: start, policy: policy)

        #expect(plan.count == 3)
        #expect(plan.map(\.date) == [
            start,
            start.addingTimeInterval(30),
            start.addingTimeInterval(90)
        ])
    }

    @Test("Politika geçersiz gecikmeleri eler ve sıraya sokar")
    func policyNormalizesDelays() {
        let policy = FollowUpPolicy(delays: [300, -10, 0, 60])
        #expect(policy.delays == [60, 300])
        #expect(policy.totalFireCount == 3)
    }

    // MARK: - Çoklu alarm

    @Test("Birden fazla alarmın planı zamana göre sıralanır")
    func multipleAlarmsAreSorted() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 5, 0, in: calendar)
        let early = alarm(hour: 6, minute: 0, taskCount: 0)
        let late = alarm(hour: 8, minute: 0, taskCount: 0)

        let plan = AlarmScheduler.firePlan(
            for: [late, early],
            after: reference,
            calendar: calendar
        )

        #expect(plan.count == 2)
        #expect(plan.map(\.alarmID) == [early.id, late.id])
        #expect(plan[0].date < plan[1].date)
    }

    @Test("Sonraki alarm yalnızca açık alarmlar arasından seçilir")
    func nextAlarmIgnoresDisabled() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 5, 0, in: calendar)
        let disabledEarly = alarm(hour: 6, minute: 0, enabled: false)
        let enabledLate = alarm(hour: 8, minute: 0)

        let result = AlarmScheduler.nextAlarm(
            among: [disabledEarly, enabledLate],
            after: reference,
            calendar: calendar
        )

        #expect(result?.alarm.id == enabledLate.id)
        #expect(result?.date == Self.date(2026, 8, 17, 8, 0, in: calendar))
    }

    @Test("Hiç açık alarm yoksa sonuç yok")
    func nextAlarmWithNoEnabledAlarms() {
        let calendar = Self.istanbul()
        let reference = Self.date(2026, 8, 17, 5, 0, in: calendar)
        #expect(AlarmScheduler.nextAlarm(among: [], after: reference, calendar: calendar) == nil)
        #expect(
            AlarmScheduler.nextAlarm(
                among: [alarm(hour: 6, minute: 0, enabled: false)],
                after: reference,
                calendar: calendar
            ) == nil
        )
    }
}
