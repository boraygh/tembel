import Foundation

/// Çalan alarm oturumunun kalıcı saklanması.
///
/// Aynı anda yalnızca tek bir oturum yürür — iki alarm aynı anda çalsa bile
/// kullanıcı tek seferde tek görev yapabilir.
public protocol AlarmSessionPersisting: Sendable {
    func loadActiveSession() throws -> AlarmSession?
    func saveActiveSession(_ session: AlarmSession?) throws
}

public struct JSONFileAlarmSessionStore: AlarmSessionPersisting {

    public let fileURL: URL

    public init(fileURL: URL) {
        self.fileURL = fileURL
    }

    public static func defaultStore(
        fileManager: FileManager = .default
    ) throws -> JSONFileAlarmSessionStore {
        let directory = try fileManager.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        return JSONFileAlarmSessionStore(
            fileURL: directory.appending(path: "active-session.json")
        )
    }

    /// Kayıtlı oturumu okur.
    ///
    /// Dosya bozuksa — alarm kayıtlarının aksine — sessizce silinir ve `nil`
    /// dönülür. Bunun nedeni kaybın telafi edilebilir olması: takip alarm
    /// zinciri gelmeye devam ettiği için kullanıcı görevleri baştan yapar.
    /// Alarm listesinde aynı davranış kabul edilemezdi, çünkü orada kayıp
    /// kalıcıdır.
    public func loadActiveSession() throws -> AlarmSession? {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }
        do {
            let data = try Data(contentsOf: fileURL)
            return try Self.makeDecoder().decode(AlarmSession.self, from: data)
        } catch {
            try? FileManager.default.removeItem(at: fileURL)
            return nil
        }
    }

    public func saveActiveSession(_ session: AlarmSession?) throws {
        guard let session else {
            if FileManager.default.fileExists(atPath: fileURL.path) {
                try FileManager.default.removeItem(at: fileURL)
            }
            return
        }

        let data = try Self.makeEncoder().encode(session)
        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try data.write(to: fileURL, options: .atomic)
    }

    private static func makeEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }

    private static func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}

/// Testler ve önizlemeler için diske dokunmayan uyarlama.
public final class InMemoryAlarmSessionStore: AlarmSessionPersisting, @unchecked Sendable {

    private let lock = NSLock()
    private var session: AlarmSession?

    public init(session: AlarmSession? = nil) {
        self.session = session
    }

    public func loadActiveSession() throws -> AlarmSession? {
        lock.lock()
        defer { lock.unlock() }
        return session
    }

    public func saveActiveSession(_ session: AlarmSession?) throws {
        lock.lock()
        defer { lock.unlock() }
        self.session = session
    }
}
