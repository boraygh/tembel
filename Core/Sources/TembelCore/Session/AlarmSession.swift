import Foundation

/// Çalan bir alarmın oturumu — görevlerin yürütüldüğü çalışma anı durumu.
///
/// `Alarm` yapılandırmadır ve kullanıcı tarafından düzenlenir; `AlarmSession`
/// ise tek bir çalışa aittir ve alarm bittiğinde atılır. Görevler oturum
/// açılırken **kopyalanır**: kullanıcı alarm çalarken alarmı düzenlese bile
/// yürüyen görev listesi değişmez.
///
/// Tip `Codable`'dır çünkü uygulama görev ekranındayken öldürülebilir
/// (force-quit, çökme, bellek baskısı). Oturum diske yazıldığı için uygulama
/// yeniden açıldığında kaldığı görevden devam eder — takip alarmı zaten
/// gelmeye devam ediyordur.
public struct AlarmSession: Codable, Sendable, Equatable, Identifiable {

    public enum Phase: Sendable, Equatable {
        case running
        case snoozed(until: Date)
        case finished(at: Date)
    }

    public let id: UUID
    public let alarmID: UUID
    public let startedAt: Date

    /// Alarm çaldığı andaki başlığı ve saati.
    ///
    /// Kopyalanmalarının nedeni: kullanıcı alarm çalarken alarmı silebilir.
    /// Oturum, kaynağı ortadan kalksa bile ekranda ne göstereceğini bilmeli.
    public let alarmTitle: String
    public let alarmTime: TimeOfDay

    /// Alarm çaldığı andaki görev listesi ve sırası.
    public let tasks: [AlarmTask]
    /// Alarm çaldığı andaki erteleme ayarı.
    public let snooze: SnoozeSetting

    /// Tamamlanan görevler, tamamlanma sırasıyla.
    public private(set) var completedTaskIDs: [UUID]
    public private(set) var snoozeCount: Int

    private var snoozedUntil: Date?
    private var finishedAt: Date?

    public init(alarm: Alarm, startedAt: Date, id: UUID = UUID()) {
        self.id = id
        self.alarmID = alarm.id
        self.startedAt = startedAt.truncatedToSeconds()
        self.alarmTitle = alarm.title
        self.alarmTime = alarm.time
        self.tasks = alarm.tasks
        self.snooze = alarm.snooze
        self.completedTaskIDs = []
        self.snoozeCount = 0
        self.snoozedUntil = nil
        // Görevsiz alarm, sıradan bir alarm gibi davranır: açılır açılmaz
        // tamamlanmış sayılır ve zincir kurulmamıştır.
        self.finishedAt = alarm.tasks.isEmpty ? startedAt.truncatedToSeconds() : nil
    }

    // MARK: - Durum

    public var isComplete: Bool {
        completedTaskIDs.count >= tasks.count
    }

    public var phase: Phase {
        if let finishedAt { return .finished(at: finishedAt) }
        if let snoozedUntil { return .snoozed(until: snoozedUntil) }
        return .running
    }

    /// Şu an yapılması gereken görev. Sıra zorunludur — kullanıcı görevleri
    /// atlayamaz.
    public var currentTask: AlarmTask? {
        guard !isComplete else { return nil }
        return tasks[completedTaskIDs.count]
    }

    /// Yürüyen görevin sırası (1'den başlar). Tamamlanmışsa `nil`.
    public var currentTaskNumber: Int? {
        isComplete ? nil : completedTaskIDs.count + 1
    }

    public var completedCount: Int { completedTaskIDs.count }

    public var remainingTasks: [AlarmTask] {
        Array(tasks.dropFirst(completedTaskIDs.count))
    }

    /// 0…1 arası tamamlanma oranı.
    public var progress: Double {
        guard !tasks.isEmpty else { return 1 }
        return Double(completedTaskIDs.count) / Double(tasks.count)
    }

    /// Erteleme hâlâ mümkün mü.
    ///
    /// Sınırsız erteleme uygulamanın amacını yok ederdi; hakkı biten kullanıcı
    /// için görevleri yapmaktan başka yol kalmaz.
    public var canSnooze: Bool {
        guard snooze.isEnabled, !isComplete else { return false }
        if snoozedUntil != nil { return false }
        return snoozeCount < snooze.maxCount
    }

    public var remainingSnoozeCount: Int {
        guard snooze.isEnabled else { return 0 }
        return max(0, snooze.maxCount - snoozeCount)
    }

    // MARK: - Geçişler

    /// Yürüyen görevi tamamlar.
    ///
    /// `taskID` verilirse yalnızca yürüyen görevle eşleştiğinde işler; bu,
    /// ekranda eski bir görev duruyorken gelen geç bir dokunuşun yanlış görevi
    /// tamamlamasını engeller.
    ///
    /// - Returns: Durum ilerlediyse `true`.
    @discardableResult
    public mutating func completeCurrentTask(
        taskID: UUID? = nil,
        at date: Date
    ) -> Bool {
        guard finishedAt == nil, snoozedUntil == nil else { return false }
        guard let current = currentTask else { return false }
        if let taskID, taskID != current.id { return false }

        completedTaskIDs.append(current.id)
        if isComplete {
            finishedAt = date.truncatedToSeconds()
        }
        return true
    }

    /// Alarmı erteler ve uyanma zamanını döndürür. Hak kalmamışsa `nil`.
    @discardableResult
    public mutating func snoozeNow(at date: Date) -> Date? {
        guard canSnooze else { return nil }
        let wakeDate = date
            .addingTimeInterval(TimeInterval(snooze.durationMinutes * 60))
            .truncatedToSeconds()
        snoozeCount += 1
        snoozedUntil = wakeDate
        return wakeDate
    }

    /// Ertelemeden geri döner. Erteleme süresi dolmamışsa hiçbir şey yapmaz.
    @discardableResult
    public mutating func resumeFromSnooze(at date: Date) -> Bool {
        guard let snoozedUntil, date >= snoozedUntil else { return false }
        self.snoozedUntil = nil
        return true
    }

    /// Görev ilerlemesini sıfırlar ama erteleme hakkını geri vermez.
    ///
    /// Erteleme sayacının korunması kasıtlıdır: aksi hâlde kullanıcı görevi
    /// baştan başlatarak sınırsız erteleme hakkı üretebilirdi.
    public mutating func restartTasks() {
        guard !tasks.isEmpty else { return }
        completedTaskIDs.removeAll()
        finishedAt = nil
    }
}
