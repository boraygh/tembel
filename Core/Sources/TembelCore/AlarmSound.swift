import Foundation

/// Alarm sesi.
///
/// `systemDefault` dışındaki sesler AlarmKit'e dosya adıyla verilir. Kısıt
/// dokümanında not edildiği gibi custom ses desteğinin gerçek cihazda
/// çalıştığı henüz doğrulanmadı; bu yüzden varsayılan `systemDefault`'tur ve
/// diğerleri ancak Phase 11 doğrulamasından sonra kullanıcıya açılacaktır.
public enum AlarmSound: String, Codable, CaseIterable, Sendable, Identifiable {
    case systemDefault
    case aggressive
    case siren
    case digital
    case emergency
    case buzzer

    public var id: String { rawValue }

    /// Uygulama paketindeki ses dosyasının adı. `systemDefault` için `nil` —
    /// bu durumda AlarmKit'in kendi sesi kullanılır.
    public var fileName: String? {
        switch self {
        case .systemDefault: nil
        default: "\(rawValue).caf"
        }
    }

    /// Gerçek cihazda doğrulanana kadar kullanıcıya sunulacak sesler.
    public static var availableForSelection: [AlarmSound] {
        [.systemDefault]
    }
}
