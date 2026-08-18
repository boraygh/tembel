import Foundation
import Testing

@testable import TembelCore

@Suite("Alarm oturumu")
struct AlarmSessionTests {

    private static let start = Date(timeIntervalSince1970: 1_800_000_000)

    private func alarm(
        taskCount: Int = 3,
        snooze: SnoozeSetting = .disabled
    ) -> Alarm {
        Alarm(
            title: "Test",
            time: TimeOfDay(hour: 7, minute: 30),
            tasks: (0..<taskCount).map { index in
                AlarmTask(configuration: index.isMultiple(of: 2)
                    ? .shake(count: 10)
                    : .math(difficulty: .medium, questionCount: 1))
            },
            snooze: snooze
        )
    }

    private func session(
        taskCount: Int = 3,
        snooze: SnoozeSetting = .disabled
    ) -> AlarmSession {
        AlarmSession(alarm: alarm(taskCount: taskCount, snooze: snooze), startedAt: Self.start)
    }

    // MARK: - Başlangıç

    @Test("Yeni oturum ilk görevden başlar")
    func startsAtFirstTask() {
        let subject = session()
        #expect(subject.completedCount == 0)
        #expect(subject.currentTaskNumber == 1)
        #expect(subject.currentTask?.id == subject.tasks[0].id)
        #expect(subject.isComplete == false)
        #expect(subject.phase == .running)
        #expect(subject.progress == 0)
    }

    @Test("Görevsiz alarm anında tamamlanmış sayılır")
    func tasklessAlarmIsImmediatelyFinished() {
        let subject = session(taskCount: 0)
        #expect(subject.isComplete)
        #expect(subject.currentTask == nil)
        #expect(subject.currentTaskNumber == nil)
        #expect(subject.progress == 1)
        #expect(subject.phase == .finished(at: Self.start))
    }

    @Test("Görevler alarmdan kopyalanır — sonradan alarm değişse bile oturum değişmez")
    func tasksAreSnapshotted() {
        var source = alarm(taskCount: 2)
        let subject = AlarmSession(alarm: source, startedAt: Self.start)

        source.tasks.removeAll()
        source.title = "Değişti"
        source.time = TimeOfDay(hour: 23, minute: 59)

        #expect(subject.tasks.count == 2)
        #expect(subject.alarmID == source.id)
        // Alarm çalarken silinse bile ekranda gösterilecek bilgi durmalı.
        #expect(subject.alarmTitle == "Test")
        #expect(subject.alarmTime == TimeOfDay(hour: 7, minute: 30))
    }

    // MARK: - Görev ilerlemesi

    @Test("Görevler sırayla tamamlanır")
    func tasksCompleteInOrder() {
        var subject = session(taskCount: 3)

        let first = subject.completeCurrentTask(at: Self.start.addingTimeInterval(10))
        #expect(first)
        #expect(subject.currentTaskNumber == 2)
        #expect(subject.progress > 0.33 && subject.progress < 0.34)

        subject.completeCurrentTask(at: Self.start.addingTimeInterval(20))
        #expect(subject.currentTaskNumber == 3)
        #expect(subject.isComplete == false)

        subject.completeCurrentTask(at: Self.start.addingTimeInterval(30))
        #expect(subject.isComplete)
        #expect(subject.progress == 1)
        #expect(subject.currentTask == nil)
    }

    @Test("Sıradaki görev atlanamaz")
    func cannotSkipAhead() {
        var subject = session(taskCount: 3)
        let thirdTaskID = subject.tasks[2].id

        // Üçüncü görevi tamamlamaya çalışmak reddedilmeli.
        let skipped = subject.completeCurrentTask(taskID: thirdTaskID, at: Self.start)
        #expect(skipped == false)
        #expect(subject.completedCount == 0)
        #expect(subject.currentTaskNumber == 1)
    }

    @Test("Geç gelen dokunuş yanlış görevi tamamlamaz")
    func staleCompletionIsRejected() {
        var subject = session(taskCount: 3)
        let firstTaskID = subject.tasks[0].id

        subject.completeCurrentTask(taskID: firstTaskID, at: Self.start)
        #expect(subject.completedCount == 1)

        // Aynı dokunuş bir kez daha gelirse ikinci görevi tamamlamamalı.
        let repeated = subject.completeCurrentTask(taskID: firstTaskID, at: Self.start)
        #expect(repeated == false)
        #expect(subject.completedCount == 1)
    }

    @Test("Tamamlanmış oturumda görev tamamlanamaz")
    func completingFinishedSessionDoesNothing() {
        var subject = session(taskCount: 1)
        subject.completeCurrentTask(at: Self.start)
        #expect(subject.isComplete)

        let extra = subject.completeCurrentTask(at: Self.start.addingTimeInterval(5))
        #expect(extra == false)
        #expect(subject.completedCount == 1)
    }

    @Test("Tamamlanma zamanı son görevin bitirildiği andır")
    func finishTimestamp() {
        var subject = session(taskCount: 2)
        let finish = Self.start.addingTimeInterval(45)

        subject.completeCurrentTask(at: Self.start.addingTimeInterval(20))
        subject.completeCurrentTask(at: finish)

        #expect(subject.phase == .finished(at: finish))
    }

    // MARK: - Erteleme

    @Test("Erteleme kapalıyken ertelenemez")
    func snoozeDisabled() {
        var subject = session(snooze: .disabled)
        #expect(subject.canSnooze == false)
        #expect(subject.snoozeNow(at: Self.start) == nil)
        #expect(subject.snoozeCount == 0)
    }

    @Test("Erteleme açıkken uyanma zamanı döner")
    func snoozeReturnsWakeDate() {
        var subject = session(
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 2)
        )
        let wake = subject.snoozeNow(at: Self.start)

        #expect(wake == Self.start.addingTimeInterval(300))
        #expect(subject.snoozeCount == 1)
        #expect(subject.phase == .snoozed(until: Self.start.addingTimeInterval(300)))
    }

    @Test("Erteleme hakkı biter")
    func snoozeIsLimited() {
        var subject = session(
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 2)
        )

        _ = subject.snoozeNow(at: Self.start)
        subject.resumeFromSnooze(at: Self.start.addingTimeInterval(300))
        #expect(subject.remainingSnoozeCount == 1)

        _ = subject.snoozeNow(at: Self.start.addingTimeInterval(300))
        subject.resumeFromSnooze(at: Self.start.addingTimeInterval(600))
        #expect(subject.remainingSnoozeCount == 0)
        #expect(subject.canSnooze == false)
        #expect(subject.snoozeNow(at: Self.start.addingTimeInterval(600)) == nil)
    }

    @Test("Ertelenmiş oturumda görev tamamlanamaz")
    func cannotCompleteWhileSnoozed() {
        var subject = session(
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 1)
        )
        _ = subject.snoozeNow(at: Self.start)

        let completed = subject.completeCurrentTask(at: Self.start.addingTimeInterval(10))
        #expect(completed == false)
        #expect(subject.completedCount == 0)
    }

    @Test("Erteleme süresi dolmadan geri dönülemez")
    func resumeRequiresElapsedTime() {
        var subject = session(
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 1)
        )
        _ = subject.snoozeNow(at: Self.start)

        let tooEarly = subject.resumeFromSnooze(at: Self.start.addingTimeInterval(299))
        #expect(tooEarly == false)

        let onTime = subject.resumeFromSnooze(at: Self.start.addingTimeInterval(300))
        #expect(onTime)
        #expect(subject.phase == .running)
    }

    @Test("Tamamlanmış oturum ertelenemez")
    func cannotSnoozeFinishedSession() {
        var subject = session(
            taskCount: 1,
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 3)
        )
        subject.completeCurrentTask(at: Self.start)
        #expect(subject.canSnooze == false)
        #expect(subject.snoozeNow(at: Self.start) == nil)
    }

    @Test("Görevleri baştan başlatmak erteleme hakkını geri vermez")
    func restartDoesNotRefillSnooze() {
        var subject = session(
            taskCount: 2,
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 1)
        )
        _ = subject.snoozeNow(at: Self.start)
        subject.resumeFromSnooze(at: Self.start.addingTimeInterval(300))
        subject.completeCurrentTask(at: Self.start.addingTimeInterval(310))

        subject.restartTasks()

        #expect(subject.completedCount == 0)
        #expect(subject.currentTaskNumber == 1)
        // Sınırsız erteleme üretilememeli.
        #expect(subject.snoozeCount == 1)
        #expect(subject.canSnooze == false)
    }

    // MARK: - Kalıcılık (force-quit sonrası devam)

    @Test("Oturum diske yazılıp aynen geri okunur")
    func sessionSurvivesRoundTrip() throws {
        var subject = session(
            taskCount: 3,
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 10, maxCount: 2)
        )
        subject.completeCurrentTask(at: Self.start.addingTimeInterval(15))

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let restored = try decoder.decode(
            AlarmSession.self,
            from: encoder.encode(subject)
        )

        #expect(restored == subject)
        // Uygulama öldürülüp açıldığında kaldığı görevden devam etmeli.
        #expect(restored.currentTaskNumber == 2)
        #expect(restored.completedCount == 1)
    }

    @Test("Store oturumu saklar, siler ve yoksa nil döner")
    func storeLifecycle() throws {
        let directory = FileManager.default.temporaryDirectory
            .appending(path: "tembel-session-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let store = JSONFileAlarmSessionStore(
            fileURL: directory.appending(path: "active-session.json")
        )

        #expect(try store.loadActiveSession() == nil)

        var subject = session(taskCount: 2)
        subject.completeCurrentTask(at: Self.start.addingTimeInterval(5))
        try store.saveActiveSession(subject)

        #expect(try store.loadActiveSession() == subject)

        try store.saveActiveSession(nil)
        #expect(try store.loadActiveSession() == nil)
    }

    @Test("Bozuk oturum dosyası temizlenir ve nil döner")
    func corruptedSessionFileIsDiscarded() throws {
        let directory = FileManager.default.temporaryDirectory
            .appending(path: "tembel-session-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let fileURL = directory.appending(path: "active-session.json")
        try Data("bu json değil".utf8).write(to: fileURL)

        let store = JSONFileAlarmSessionStore(fileURL: fileURL)
        // Kayıp telafi edilebilir: takip alarmları gelmeye devam eder.
        #expect(try store.loadActiveSession() == nil)
        #expect(FileManager.default.fileExists(atPath: fileURL.path) == false)
    }

    @Test("Bellek içi store aynı sözleşmeye uyar")
    func inMemoryStore() throws {
        let store = InMemoryAlarmSessionStore()
        #expect(try store.loadActiveSession() == nil)

        let subject = session()
        try store.saveActiveSession(subject)
        #expect(try store.loadActiveSession() == subject)

        try store.saveActiveSession(nil)
        #expect(try store.loadActiveSession() == nil)
    }
}
