import Foundation

/// Alarmların kalıcı olarak saklanması.
///
/// Protokol arkasına alınmasının nedeni testlerde ve SwiftUI önizlemelerinde
/// diske dokunmadan çalışabilmek — ayrıca ileride SwiftData'ya geçilmek
/// istenirse yalnızca bu protokolün yeni bir uyarlaması yazılır.
public protocol AlarmPersisting: Sendable {
    func load() throws -> [Alarm]
    func save(_ alarms: [Alarm]) throws
}

public enum AlarmStoreError: Error, Sendable, Equatable {
    /// Dosya, bu sürümün tanımadığı daha yeni bir şemayla yazılmış.
    /// Bu durumda dosyanın üzerine yazmak kullanıcının alarmlarını silmek
    /// olur; bu yüzden okuma başarısız sayılır.
    case unsupportedSchemaVersion(found: Int, supported: Int)

    /// Dosya çözümlenemedi. Bozuk dosya kenara alınır ki bir sonraki kayıt
    /// onu ezmesin ve gerekirse elle kurtarılabilsin.
    case corruptedFile(quarantinedAt: URL?, underlying: String)
}

// MARK: - Dosya biçimi

/// Diskteki JSON'un en dış katmanı.
///
/// Alarm dizisini doğrudan yazmak yerine sürüm numaralı bir zarf kullanılıyor;
/// böylece ileride model değiştiğinde eski dosyalar tanınıp dönüştürülebilir.
struct AlarmFile: Codable, Sendable {
    var schemaVersion: Int
    var alarms: [Alarm]
}

// MARK: - JSON dosya uyarlaması

public struct JSONFileAlarmStore: AlarmPersisting {

    /// Şema sürümü. Model kırıcı biçimde değiştiğinde artırılır.
    public static let currentSchemaVersion = 1

    public let fileURL: URL

    public init(fileURL: URL) {
        self.fileURL = fileURL
    }

    /// Uygulamanın Application Support klasöründeki varsayılan konum.
    public static func defaultStore(
        fileManager: FileManager = .default
    ) throws -> JSONFileAlarmStore {
        let directory = try fileManager.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        return JSONFileAlarmStore(fileURL: directory.appending(path: "alarms.json"))
    }

    public func load() throws -> [Alarm] {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return []
        }

        let data: Data
        do {
            data = try Data(contentsOf: fileURL)
        } catch {
            throw AlarmStoreError.corruptedFile(
                quarantinedAt: quarantine(),
                underlying: String(describing: error)
            )
        }

        let file: AlarmFile
        do {
            file = try Self.makeDecoder().decode(AlarmFile.self, from: data)
        } catch {
            throw AlarmStoreError.corruptedFile(
                quarantinedAt: quarantine(),
                underlying: String(describing: error)
            )
        }

        guard file.schemaVersion <= Self.currentSchemaVersion else {
            throw AlarmStoreError.unsupportedSchemaVersion(
                found: file.schemaVersion,
                supported: Self.currentSchemaVersion
            )
        }

        return file.alarms.map { $0.normalized() }
    }

    public func save(_ alarms: [Alarm]) throws {
        let file = AlarmFile(
            schemaVersion: Self.currentSchemaVersion,
            alarms: alarms.map { $0.normalized() }
        )
        let data = try Self.makeEncoder().encode(file)

        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )

        // .atomic: önce geçici dosyaya yazıp sonra yer değiştirir. Yazma
        // sırasında uygulama öldürülürse mevcut alarmlar bozulmaz.
        try data.write(to: fileURL, options: .atomic)
    }

    /// Bozuk dosyayı yanına taşır. Başarısız olursa `nil` döner — bu durumda
    /// da okuma hata verir, veri sessizce kaybolmaz.
    private func quarantine() -> URL? {
        let stamp = Int(Date().timeIntervalSince1970)
        let destination = fileURL
            .deletingLastPathComponent()
            .appending(path: "\(fileURL.lastPathComponent).corrupt-\(stamp)")
        do {
            try FileManager.default.moveItem(at: fileURL, to: destination)
            return destination
        } catch {
            return nil
        }
    }

    private static func makeEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        return encoder
    }

    private static func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}

// MARK: - Bellek içi uyarlama

/// Testler ve SwiftUI önizlemeleri için diske dokunmayan uyarlama.
public final class InMemoryAlarmStore: AlarmPersisting, @unchecked Sendable {
    private let lock = NSLock()
    private var alarms: [Alarm]

    public init(alarms: [Alarm] = []) {
        self.alarms = alarms
    }

    public func load() throws -> [Alarm] {
        lock.lock()
        defer { lock.unlock() }
        return alarms.map { $0.normalized() }
    }

    public func save(_ alarms: [Alarm]) throws {
        lock.lock()
        defer { lock.unlock() }
        self.alarms = alarms.map { $0.normalized() }
    }
}
