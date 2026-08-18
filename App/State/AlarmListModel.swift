import Foundation
import Observation
import TembelCore

/// Ekranların paylaştığı alarm listesi.
///
/// Diskle konuşan tek yer burasıdır; view'lar `AlarmPersisting`'i doğrudan
/// görmez. Her değişiklik anında kaydedilir — alarm uygulamasında "kaydetmeyi
/// unuttum" diye bir durum olmamalı.
@MainActor
@Observable
final class AlarmListModel {

    private(set) var alarms: [Alarm] = []

    /// Kullanıcıya gösterilecek son hata. Gösterildikten sonra `nil`'lenir.
    var errorMessage: String?

    private let store: any AlarmPersisting

    init(store: any AlarmPersisting) {
        self.store = store
        reload()
    }

    /// Uygulama açılışında ve öne geldiğinde diskten okur.
    func reload() {
        do {
            alarms = try store.load().sortedForDisplay()
            errorMessage = nil
        } catch let error as AlarmStoreError {
            // Alarmları sıfırlamıyoruz ki bir sonraki kayıt bozuk dosyayı
            // sessizce boş listeyle ezmesin.
            errorMessage = Self.message(for: error)
        } catch {
            errorMessage = AppStrings.Errors.storageTitle
        }
    }

    /// Yeni alarm ekler veya var olanı günceller.
    func save(_ alarm: Alarm) {
        var updated = alarms
        if let index = updated.firstIndex(where: { $0.id == alarm.id }) {
            updated[index] = alarm
        } else {
            updated.append(alarm)
        }
        apply(updated)
    }

    func delete(_ alarm: Alarm) {
        apply(alarms.filter { $0.id != alarm.id })
    }

    func setEnabled(_ isEnabled: Bool, for alarm: Alarm) {
        guard let index = alarms.firstIndex(where: { $0.id == alarm.id }) else { return }
        var updated = alarms
        updated[index].isEnabled = isEnabled
        apply(updated)
    }

    private func apply(_ newAlarms: [Alarm]) {
        let sorted = newAlarms.sortedForDisplay()
        do {
            try store.save(sorted)
            alarms = sorted
            errorMessage = nil
        } catch {
            // Kayıt başarısızsa bellekteki listeyi de değiştirmiyoruz;
            // ekranda duran şey diskteki gerçekle aynı kalsın.
            errorMessage = AppStrings.Errors.saveFailed
        }
    }

    private static func message(for error: AlarmStoreError) -> String {
        switch error {
        case .corruptedFile: AppStrings.Errors.corruptedFile
        case .unsupportedSchemaVersion: AppStrings.Errors.unsupportedVersion
        }
    }
}

extension AlarmListModel {
    /// SwiftUI önizlemeleri için diske dokunmayan örnek veri.
    static func preview(alarms: [Alarm] = Alarm.samples) -> AlarmListModel {
        AlarmListModel(store: InMemoryAlarmStore(alarms: alarms))
    }
}

extension Alarm {
    /// Önizlemelerde kullanılan örnek alarmlar.
    static var samples: [Alarm] {
        [
            Alarm(
                title: "İşe Kalk",
                time: TimeOfDay(hour: 7, minute: 30),
                repeatDays: .weekdays,
                tasks: [
                    AlarmTask(configuration: .shake(count: 10)),
                    AlarmTask(configuration: .math(difficulty: .medium, questionCount: 2)),
                    AlarmTask(configuration: .photo(prompt: "Kahve makinesi"))
                ]
            ),
            Alarm(
                title: "Spor",
                time: TimeOfDay(hour: 8, minute: 45),
                repeatDays: [.tuesday, .thursday],
                tasks: [
                    AlarmTask(configuration: .shake(count: 25)),
                    AlarmTask(configuration: .math(difficulty: .hard, questionCount: 3))
                ]
            ),
            Alarm(
                title: "Erken Kalk",
                time: TimeOfDay(hour: 6, minute: 15),
                repeatDays: .weekend,
                isEnabled: false,
                tasks: [AlarmTask(configuration: .math(difficulty: .easy, questionCount: 1))]
            )
        ]
    }
}
