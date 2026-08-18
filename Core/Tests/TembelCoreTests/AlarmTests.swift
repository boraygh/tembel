import Foundation
import Testing

@testable import TembelCore

@Suite("Alarm")
struct AlarmTests {

    private func makeAlarm(
        title: String = "İşe Kalk",
        tasks: [AlarmTask] = []
    ) -> Alarm {
        Alarm(
            title: title,
            time: TimeOfDay(hour: 7, minute: 30),
            repeatDays: .weekdays,
            tasks: tasks
        )
    }

    @Test("Varsayılanlar uygulamanın vaadiyle tutarlıdır")
    func defaults() {
        let alarm = Alarm(time: TimeOfDay(hour: 7, minute: 0))
        #expect(alarm.isEnabled)
        #expect(alarm.sound == .systemDefault)
        #expect(alarm.tasks.isEmpty)
        // Erteleme varsayılan olarak kapalı olmalı — açık olması uygulamanın
        // temel fikrini zayıflatır.
        #expect(alarm.snooze.isEnabled == false)
    }

    @Test("isRepeating ve requiresTasks doğru hesaplanır")
    func derivedFlags() {
        let oneShot = Alarm(time: TimeOfDay(hour: 7, minute: 0))
        #expect(oneShot.isRepeating == false)
        #expect(oneShot.requiresTasks == false)

        let repeating = makeAlarm(tasks: [AlarmTask(configuration: .shake(count: 10))])
        #expect(repeating.isRepeating)
        #expect(repeating.requiresTasks)
    }

    @Test("Tekrar günleri Pazartesi'den başlayarak sıralanır")
    func repeatDaysOrdering() {
        let alarm = Alarm(
            time: TimeOfDay(hour: 7, minute: 0),
            repeatDays: [.sunday, .monday, .friday]
        )
        #expect(alarm.orderedRepeatDays == [.monday, .friday, .sunday])
    }

    @Test("Görev sırası dizideki sıradır")
    func taskOrderFollowsArray() {
        let shake = AlarmTask(configuration: .shake(count: 10))
        let math = AlarmTask(configuration: .math(difficulty: .hard, questionCount: 3))
        let photo = AlarmTask(configuration: .photo(prompt: "Kahve makinesi"))

        let alarm = makeAlarm(tasks: [shake, math, photo])
        #expect(alarm.tasks.map(\.kind) == [.shake, .math, .photo])

        // Sonuncuyu başa taşı.
        let toFront = alarm.movingTasks(fromOffsets: IndexSet(integer: 2), toOffset: 0)
        #expect(toFront.tasks.map(\.kind) == [.photo, .shake, .math])
        // Kimlikler korunur — sürükle-bırak sıralama görevleri yeniden yaratmaz.
        #expect(toFront.tasks.first?.id == photo.id)

        // İlkini sona taşı. SwiftUI semantiğinde "sona" hedefi dizi uzunluğudur.
        let toBack = alarm.movingTasks(fromOffsets: IndexSet(integer: 0), toOffset: 3)
        #expect(toBack.tasks.map(\.kind) == [.math, .photo, .shake])

        // Ortadakini yerinde bırakan bir taşıma diziyi değiştirmemeli.
        let noop = alarm.movingTasks(fromOffsets: IndexSet(integer: 1), toOffset: 1)
        #expect(noop.tasks.map(\.id) == alarm.tasks.map(\.id))

        // Birden fazla öğe birlikte taşınabilir.
        let multiple = alarm.movingTasks(fromOffsets: IndexSet([0, 2]), toOffset: 1)
        #expect(multiple.tasks.map(\.kind) == [.shake, .photo, .math])

        // Sınır dışı indeksler çökmemeli.
        let outOfBounds = alarm.movingTasks(fromOffsets: IndexSet(integer: 99), toOffset: 0)
        #expect(outOfBounds.tasks.map(\.id) == alarm.tasks.map(\.id))
    }

    @Test("normalized() sınır dışı değerleri düzeltir")
    func normalizationClampsValues() {
        let alarm = Alarm(
            title: "   " + String(repeating: "x", count: 100) + "   ",
            time: TimeOfDay(hour: 7, minute: 0),
            tasks: [
                AlarmTask(configuration: .shake(count: 9_999)),
                AlarmTask(configuration: .math(difficulty: .easy, questionCount: 0)),
                AlarmTask(configuration: .photo(prompt: "  kupa  ")),
                AlarmTask(configuration: .shake(count: 1)),
                AlarmTask(configuration: .shake(count: 5)),
                AlarmTask(configuration: .shake(count: 6)),
                AlarmTask(configuration: .shake(count: 7))
            ],
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 999, maxCount: 99)
        ).normalized()

        #expect(alarm.title.count == Alarm.titleMaxLength)
        #expect(alarm.tasks.count == Alarm.maxTaskCount)
        #expect(alarm.tasks[0].configuration == .shake(count: TaskConfiguration.shakeCountRange.upperBound))
        #expect(alarm.tasks[1].configuration == .math(difficulty: .easy, questionCount: 1))
        #expect(alarm.tasks[2].configuration == .photo(prompt: "kupa"))
        #expect(alarm.tasks[3].configuration == .shake(count: TaskConfiguration.shakeCountRange.lowerBound))
        #expect(alarm.snooze.durationMinutes == SnoozeSetting.durationRange.upperBound)
        #expect(alarm.snooze.maxCount == SnoozeSetting.maxCountRange.upperBound)
    }

    @Test("normalized() geçerli veriyi değiştirmez")
    func normalizationIsIdempotentOnValidData() {
        let alarm = makeAlarm(tasks: [
            AlarmTask(configuration: .shake(count: 10)),
            AlarmTask(configuration: .math(difficulty: .medium, questionCount: 2))
        ])
        #expect(alarm.normalized() == alarm)
        #expect(alarm.normalized().normalized() == alarm.normalized())
    }

    @Test("Codable gidiş-dönüşü tüm alanları korur")
    func codableRoundTrip() throws {
        let original = Alarm(
            title: "Spor",
            time: TimeOfDay(hour: 8, minute: 45),
            repeatDays: [.tuesday, .thursday],
            isEnabled: false,
            sound: .siren,
            tasks: [
                AlarmTask(configuration: .shake(count: 15)),
                AlarmTask(configuration: .math(difficulty: .hard, questionCount: 3)),
                AlarmTask(configuration: .photo(prompt: "Spor çantası"))
            ],
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 10, maxCount: 2)
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let decoded = try decoder.decode(Alarm.self, from: encoder.encode(original))
        #expect(decoded == original)
    }

    @Test("createdAt saniye hassasiyetindedir")
    func createdAtHasNoSubSecondPrecision() {
        // Saniye altı hassasiyet, ISO8601 gidiş-dönüşünde kaybolur ve iki
        // mantıksal olarak aynı alarmın eşitsiz görünmesine yol açar.
        let messy = Date(timeIntervalSince1970: 1_755_500_618.123_456)
        let alarm = Alarm(time: TimeOfDay(hour: 7, minute: 0), createdAt: messy)
        #expect(alarm.createdAt.timeIntervalSince1970 == 1_755_500_618)
    }

    @Test("Görev türü ve ayarı uyumsuz kalamaz")
    func configurationCarriesItsOwnKind() {
        #expect(TaskConfiguration.shake(count: 10).kind == .shake)
        #expect(TaskConfiguration.math(difficulty: .easy, questionCount: 1).kind == .math)
        #expect(TaskConfiguration.photo(prompt: "x").kind == .photo)

        for kind in TaskKind.allCases {
            #expect(TaskConfiguration.makeDefault(for: kind).kind == kind)
            // Varsayılanlar zaten geçerli aralıkta olmalı.
            let config = TaskConfiguration.makeDefault(for: kind)
            #expect(config.normalized() == config)
        }
    }
}
