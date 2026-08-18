import Foundation
import Observation
import TembelCore

/// Çalan alarmın oturumunu yürüten model.
///
/// Her durum değişikliği anında diske yazılır. Bunun nedeni uygulamanın görev
/// ekranındayken öldürülebilmesi: kullanıcı geri döndüğünde kaldığı görevden
/// devam etmeli, baştan başlamamalı.
@MainActor
@Observable
final class AlarmSessionModel {

    private(set) var session: AlarmSession?

    /// Oturum Demo Mode'dan başlatıldı mı.
    ///
    /// Sallama görevinin sahte sensörle ilerleyebilmesi için gerekli; gerçek
    /// alarmda her zaman `false`.
    private(set) var isDemo = false

    private let store: any AlarmSessionPersisting

    init(store: any AlarmSessionPersisting) {
        self.store = store
        restore()
    }

    /// Alarm çalıyor mu (ya da görevleri sürüyor mu).
    var isRinging: Bool {
        guard let session else { return false }
        if case .finished = session.phase { return false }
        return true
    }

    /// Uygulama açılışında yarım kalmış oturumu geri yükler.
    func restore() {
        session = try? store.loadActiveSession()
    }

    /// Alarm çaldı — görev akışını başlatır.
    ///
    /// Zaten yürüyen bir oturum varsa ve aynı alarma aitse dokunulmaz;
    /// takip alarmı geldiğinde ilerleme sıfırlanmamalı.
    func start(alarm: Alarm, at date: Date = Date()) {
        if let session, session.alarmID == alarm.id, !session.isComplete {
            return
        }
        isDemo = false
        persist(AlarmSession(alarm: alarm, startedAt: date))
    }

    /// Alarm beklemeden görev akışını başlatır.
    func startDemo(alarm: Alarm, at date: Date = Date()) {
        isDemo = true
        persist(AlarmSession(alarm: alarm, startedAt: date))
    }

    @discardableResult
    func completeCurrentTask(taskID: UUID? = nil, at date: Date = Date()) -> Bool {
        guard var session else { return false }
        let didAdvance = session.completeCurrentTask(taskID: taskID, at: date)
        if didAdvance { persist(session) }
        return didAdvance
    }

    /// Erteler ve uyanma zamanını döndürür. Hak kalmamışsa `nil`.
    @discardableResult
    func snooze(at date: Date = Date()) -> Date? {
        guard var session else { return nil }
        let wakeDate = session.snoozeNow(at: date)
        if wakeDate != nil { persist(session) }
        return wakeDate
    }

    @discardableResult
    func resumeFromSnooze(at date: Date = Date()) -> Bool {
        guard var session else { return false }
        let didResume = session.resumeFromSnooze(at: date)
        if didResume { persist(session) }
        return didResume
    }

    /// Oturumu kapatır. Görevler tamamlandıktan sonra çağrılır.
    func dismiss() {
        session = nil
        isDemo = false
        try? store.saveActiveSession(nil)
    }

    private func persist(_ newSession: AlarmSession) {
        session = newSession
        // Kayıt başarısız olsa bile oturum bellekte sürer: kullanıcı görevi
        // bitirebilmeli. Kaybedilen tek şey force-quit sonrası devam etme.
        try? store.saveActiveSession(newSession)
    }
}

extension AlarmSessionModel {
    /// Önizleme ve Demo Mode için diske dokunmayan model.
    static func preview(alarm: Alarm? = nil) -> AlarmSessionModel {
        let store = InMemoryAlarmSessionStore()
        let model = AlarmSessionModel(store: store)
        if let alarm {
            model.start(alarm: alarm)
        }
        return model
    }
}
