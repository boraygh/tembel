import Foundation
import Testing

@testable import TembelCore

@Suite("Alarm listesi ve doğrulama")
struct AlarmListTests {

    private func alarm(
        _ hour: Int,
        _ minute: Int,
        enabled: Bool = true,
        createdAt: Date = Date(timeIntervalSince1970: 1_000_000),
        tasks: [AlarmTask] = []
    ) -> Alarm {
        Alarm(
            time: TimeOfDay(hour: hour, minute: minute),
            isEnabled: enabled,
            tasks: tasks,
            createdAt: createdAt
        )
    }

    // MARK: - Sıralama

    @Test("Açık alarmlar kapalı olanlardan önce gelir")
    func enabledFirst() {
        let sorted = [
            alarm(6, 15, enabled: false),
            alarm(8, 45),
            alarm(7, 30)
        ].sortedForDisplay()

        #expect(sorted.map(\.time.minutesSinceMidnight) == [
            TimeOfDay(hour: 7, minute: 30).minutesSinceMidnight,
            TimeOfDay(hour: 8, minute: 45).minutesSinceMidnight,
            TimeOfDay(hour: 6, minute: 15).minutesSinceMidnight
        ])
        #expect(sorted.map(\.isEnabled) == [true, true, false])
    }

    @Test("Her grup kendi içinde saate göre sıralanır")
    func sortedByTimeWithinGroup() {
        let sorted = [
            alarm(23, 0, enabled: false),
            alarm(5, 0, enabled: false),
            alarm(22, 0),
            alarm(4, 0)
        ].sortedForDisplay()

        #expect(sorted.map(\.time.hour) == [4, 22, 5, 23])
    }

    @Test("Sıra kararlıdır — aynı saatteki alarmlar yer değiştirmez")
    func stableOrdering() {
        let early = alarm(7, 0, createdAt: Date(timeIntervalSince1970: 100))
        let late = alarm(7, 0, createdAt: Date(timeIntervalSince1970: 200))

        let once = [late, early].sortedForDisplay()
        let twice = once.sortedForDisplay()

        #expect(once.map(\.id) == [early.id, late.id])
        #expect(twice.map(\.id) == once.map(\.id))
    }

    @Test("Boş liste sorunsuz sıralanır")
    func emptyList() {
        #expect([Alarm]().sortedForDisplay().isEmpty)
    }

    // MARK: - Doğrulama

    @Test("Görevsiz alarm kaydedilebilir")
    func alarmWithoutTasksIsValid() {
        #expect(alarm(7, 0).canBeSaved)
        #expect(alarm(7, 0).validationIssues.isEmpty)
    }

    @Test("Açıklaması boş fotoğraf görevi kaydı engeller")
    func emptyPhotoPromptBlocksSaving() {
        let task = AlarmTask(configuration: .photo(prompt: "   "))
        let subject = alarm(7, 0, tasks: [task])

        #expect(subject.canBeSaved == false)
        #expect(subject.validationIssues == [.photoTaskMissingPrompt(taskID: task.id)])
    }

    @Test("Açıklaması dolu fotoğraf görevi sorun değildir")
    func filledPhotoPromptIsValid() {
        let subject = alarm(7, 0, tasks: [
            AlarmTask(configuration: .photo(prompt: "Kahve makinesi"))
        ])
        #expect(subject.canBeSaved)
    }

    @Test("Salla ve matematik görevleri her zaman geçerlidir")
    func otherTaskKindsAreAlwaysValid() {
        let subject = alarm(7, 0, tasks: [
            AlarmTask(configuration: .shake(count: 10)),
            AlarmTask(configuration: .math(difficulty: .hard, questionCount: 3))
        ])
        #expect(subject.canBeSaved)
    }

    @Test("Birden fazla bozuk fotoğraf görevi ayrı ayrı raporlanır")
    func multipleIssuesAreReported() {
        let first = AlarmTask(configuration: .photo(prompt: ""))
        let second = AlarmTask(configuration: .photo(prompt: "\n "))
        let subject = alarm(7, 0, tasks: [
            first,
            AlarmTask(configuration: .shake(count: 5)),
            second
        ])

        #expect(subject.validationIssues == [
            .photoTaskMissingPrompt(taskID: first.id),
            .photoTaskMissingPrompt(taskID: second.id)
        ])
    }
}
