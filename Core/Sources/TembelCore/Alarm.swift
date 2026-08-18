import Foundation

/// Kullanıcının kurduğu bir alarm.
///
/// Bu tip yalnızca **yapılandırmayı** temsil eder — "alarm şu an çalıyor mu",
/// "hangi görev tamamlandı" gibi çalışma anı durumları burada tutulmaz.
/// O durum ayrı bir oturum (session) tipinde yaşayacak (Phase 10).
///
/// Ayrımın nedeni: yapılandırma kalıcıdır ve kullanıcı tarafından düzenlenir;
/// çalışma anı durumu geçicidir ve alarm bittiğinde atılır. İkisini tek tipte
/// tutmak, "dün tamamlanmış görev" gibi kirli durumların diske yazılmasına
/// yol açar.
public struct Alarm: Identifiable, Codable, Sendable, Hashable {

    public static let titleMaxLength = 40
    public static let maxTaskCount = 5

    public let id: UUID
    public var title: String
    public var time: TimeOfDay
    /// Boş küme = tekrar yok, yalnızca bir sonraki oluşumda çalar.
    public var repeatDays: Set<Weekday>
    public var isEnabled: Bool
    public var sound: AlarmSound
    /// Sıra, dizideki konumdur. Boş dizi = görevsiz alarm (normal alarm gibi).
    public var tasks: [AlarmTask]
    public var snooze: SnoozeSetting
    public let createdAt: Date

    public init(
        id: UUID = UUID(),
        title: String = "",
        time: TimeOfDay,
        repeatDays: Set<Weekday> = [],
        isEnabled: Bool = true,
        sound: AlarmSound = .systemDefault,
        tasks: [AlarmTask] = [],
        snooze: SnoozeSetting = .disabled,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.time = time
        self.repeatDays = repeatDays
        self.isEnabled = isEnabled
        self.sound = sound
        self.tasks = tasks
        self.snooze = snooze
        // Saniye altı hassasiyet atılır — bkz. Date.truncatedToSeconds().
        self.createdAt = createdAt.truncatedToSeconds()
    }
}

public extension Alarm {

    /// Alarm tekrar ediyor mu (haftalık) yoksa tek seferlik mi.
    var isRepeating: Bool { !repeatDays.isEmpty }

    /// Alarmı kapatmak için görev tamamlamak gerekiyor mu.
    var requiresTasks: Bool { !tasks.isEmpty }

    /// Tekrar günleri, UI sırasına göre (Pazartesi'den Pazar'a).
    var orderedRepeatDays: [Weekday] {
        repeatDays.sorted()
    }

    /// Görevleri yeniden sıralar.
    ///
    /// SwiftUI'ın `onMove(perform:)` semantiğiyle uyumludur: `destination`,
    /// öğelerin **önüne** ekleneceği konumdur. Mantık Core'da tutuluyor ki
    /// sürükle-bırak sıralaması Mac olmadan test edilebilsin.
    func movingTasks(fromOffsets source: IndexSet, toOffset destination: Int) -> Alarm {
        var reordered = tasks
        let moving = source.compactMap { tasks.indices.contains($0) ? tasks[$0] : nil }
        guard !moving.isEmpty else { return self }

        for index in source.sorted(by: >) where reordered.indices.contains(index) {
            reordered.remove(at: index)
        }

        let removedBeforeDestination = source.count { $0 < destination }
        let insertionIndex = (destination - removedBeforeDestination)
            .clamped(to: 0...reordered.count)
        reordered.insert(contentsOf: moving, at: insertionIndex)

        var copy = self
        copy.tasks = reordered
        return copy
    }

    /// Diskten okunan veriyi geçerli sınırlara çeker.
    ///
    /// Bozuk veya eski sürümden kalmış bir JSON'ın uygulamayı çökertmesi
    /// yerine makul değerlere düşmesi tercih edilir.
    func normalized() -> Alarm {
        Alarm(
            id: id,
            title: String(title.trimmed().prefix(Self.titleMaxLength)),
            time: time,
            repeatDays: repeatDays,
            isEnabled: isEnabled,
            sound: sound,
            tasks: Array(tasks.map { $0.normalized() }.prefix(Self.maxTaskCount)),
            snooze: snooze.normalized(),
            createdAt: createdAt
        )
    }
}
