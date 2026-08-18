import Foundation
import Testing

@testable import TembelCore

@Suite("AlarmStore")
struct AlarmStoreTests {

    /// Her test kendi geçici klasöründe çalışır.
    private struct TemporaryDirectory: ~Copyable {
        let url: URL

        init() throws {
            url = FileManager.default.temporaryDirectory
                .appending(path: "tembel-tests-\(UUID().uuidString)")
            try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        }

        deinit {
            try? FileManager.default.removeItem(at: url)
        }
    }

    private func makeAlarms() -> [Alarm] {
        [
            Alarm(
                title: "İşe Kalk",
                time: TimeOfDay(hour: 7, minute: 30),
                repeatDays: .weekdays,
                tasks: [
                    AlarmTask(configuration: .shake(count: 10)),
                    AlarmTask(configuration: .math(difficulty: .medium, questionCount: 2))
                ]
            ),
            Alarm(
                title: "Spor",
                time: TimeOfDay(hour: 8, minute: 45),
                repeatDays: [.tuesday, .thursday],
                isEnabled: false,
                tasks: [AlarmTask(configuration: .photo(prompt: "Spor çantası"))]
            )
        ]
    }

    @Test("Dosya yoksa boş liste döner, hata vermez")
    func loadingMissingFileReturnsEmpty() throws {
        let directory = try TemporaryDirectory()
        let store = JSONFileAlarmStore(fileURL: directory.url.appending(path: "alarms.json"))
        #expect(try store.load().isEmpty)
    }

    @Test("Kaydedilen alarmlar aynen geri okunur")
    func saveThenLoadRoundTrip() throws {
        let directory = try TemporaryDirectory()
        let store = JSONFileAlarmStore(fileURL: directory.url.appending(path: "alarms.json"))
        let alarms = makeAlarms()

        try store.save(alarms)
        #expect(try store.load() == alarms)
    }

    @Test("Kayıt, olmayan klasörü oluşturur")
    func saveCreatesIntermediateDirectories() throws {
        let directory = try TemporaryDirectory()
        let nested = directory.url.appending(path: "a/b/c/alarms.json")
        let store = JSONFileAlarmStore(fileURL: nested)

        try store.save(makeAlarms())
        #expect(FileManager.default.fileExists(atPath: nested.path))
    }

    @Test("Yeniden kayıt önceki içeriği tamamen değiştirir")
    func saveOverwrites() throws {
        let directory = try TemporaryDirectory()
        let store = JSONFileAlarmStore(fileURL: directory.url.appending(path: "alarms.json"))

        try store.save(makeAlarms())
        try store.save([])
        #expect(try store.load().isEmpty)
    }

    @Test("Diskten okunan veri normalize edilir")
    func loadNormalizesValues() throws {
        let directory = try TemporaryDirectory()
        let fileURL = directory.url.appending(path: "alarms.json")
        let store = JSONFileAlarmStore(fileURL: fileURL)

        // Sınır dışı shake sayısı içeren, elle yazılmış geçerli JSON.
        let json = """
        {
          "schemaVersion": 1,
          "alarms": [
            {
              "id": "\(UUID().uuidString)",
              "title": "Test",
              "time": 450,
              "repeatDays": [],
              "isEnabled": true,
              "sound": "systemDefault",
              "tasks": [{ "id": "\(UUID().uuidString)", "configuration": { "shake": { "count": 100000 } } }],
              "snooze": { "isEnabled": false, "durationMinutes": 5, "maxCount": 1 },
              "createdAt": "2026-08-18T06:00:00Z"
            }
          ]
        }
        """
        try Data(json.utf8).write(to: fileURL)

        let loaded = try store.load()
        #expect(loaded.count == 1)
        #expect(
            loaded[0].tasks[0].configuration
                == .shake(count: TaskConfiguration.shakeCountRange.upperBound)
        )
    }

    @Test("Bozuk dosya karantinaya alınır ve hata döner")
    func corruptedFileIsQuarantined() throws {
        let directory = try TemporaryDirectory()
        let fileURL = directory.url.appending(path: "alarms.json")
        let store = JSONFileAlarmStore(fileURL: fileURL)

        try Data("bu json değil {{{".utf8).write(to: fileURL)

        var quarantinedURL: URL?
        #expect(throws: AlarmStoreError.self) {
            do {
                _ = try store.load()
            } catch let error as AlarmStoreError {
                if case .corruptedFile(let url, _) = error { quarantinedURL = url }
                throw error
            }
        }

        // Bozuk dosya yerinden alınmış olmalı ki bir sonraki kayıt onu ezmesin.
        #expect(FileManager.default.fileExists(atPath: fileURL.path) == false)
        let quarantined = try #require(quarantinedURL)
        #expect(FileManager.default.fileExists(atPath: quarantined.path))
    }

    @Test("Daha yeni şema sürümü reddedilir, veri ezilmez")
    func newerSchemaVersionIsRejected() throws {
        let directory = try TemporaryDirectory()
        let fileURL = directory.url.appending(path: "alarms.json")
        let store = JSONFileAlarmStore(fileURL: fileURL)

        let json = #"{ "schemaVersion": 99, "alarms": [] }"#
        try Data(json.utf8).write(to: fileURL)

        #expect(throws: AlarmStoreError.unsupportedSchemaVersion(found: 99, supported: 1)) {
            _ = try store.load()
        }
        // Dosya olduğu gibi durmalı — karantinaya alınmamalı.
        #expect(FileManager.default.fileExists(atPath: fileURL.path))
    }

    @Test("Bellek içi store aynı sözleşmeye uyar")
    func inMemoryStoreBehavesTheSame() throws {
        let store = InMemoryAlarmStore()
        #expect(try store.load().isEmpty)

        let alarms = makeAlarms()
        try store.save(alarms)
        #expect(try store.load() == alarms)

        try store.save([])
        #expect(try store.load().isEmpty)
    }
}
