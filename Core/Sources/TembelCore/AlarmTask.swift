import Foundation

/// Bir görevin türü. UI'da ikon/başlık seçmek ve gruplamak için kullanılır.
public enum TaskKind: String, Codable, CaseIterable, Sendable, Identifiable {
    case shake
    case math
    case photo

    public var id: String { rawValue }
}

public enum MathDifficulty: String, Codable, CaseIterable, Sendable, Identifiable {
    case easy
    case medium
    case hard

    public var id: String { rawValue }
}

/// Bir görevin ayarları.
///
/// Associated value'lu enum kullanılmasının nedeni: her görev türünün farklı
/// ayarları var ve tür ile ayarın uyumsuz kalması (örneğin shake görevinde
/// `difficulty` alanı) imkânsız hale geliyor.
public enum TaskConfiguration: Codable, Sendable, Hashable {
    case shake(count: Int)
    case math(difficulty: MathDifficulty, questionCount: Int)
    case photo(prompt: String)

    public var kind: TaskKind {
        switch self {
        case .shake: .shake
        case .math: .math
        case .photo: .photo
        }
    }
}

public extension TaskConfiguration {

    static let shakeCountRange = 3...100
    static let mathQuestionCountRange = 1...10
    static let promptMaxLength = 80

    /// Ayarları geçerli aralıklara çeker.
    ///
    /// Diskten okunan veriye uygulanır — bkz. `Clamping.swift`.
    func normalized() -> TaskConfiguration {
        switch self {
        case .shake(let count):
            .shake(count: count.clamped(to: Self.shakeCountRange))

        case .math(let difficulty, let questionCount):
            .math(
                difficulty: difficulty,
                questionCount: questionCount.clamped(to: Self.mathQuestionCountRange)
            )

        case .photo(let prompt):
            .photo(prompt: String(prompt.trimmed().prefix(Self.promptMaxLength)))
        }
    }

    /// Yeni görev eklerken kullanılan makul başlangıç değerleri.
    static func makeDefault(for kind: TaskKind) -> TaskConfiguration {
        switch kind {
        case .shake: .shake(count: 10)
        case .math: .math(difficulty: .medium, questionCount: 1)
        case .photo: .photo(prompt: "")
        }
    }
}

/// Alarmı kapatmak için tamamlanması gereken tek bir görev.
///
/// Görevin sırası bu tipte **tutulmaz** — sıra, `Alarm.tasks` dizisindeki
/// konumdur. Ayrı bir `order` alanı tutulsaydı dizi sırası ile alan değeri
/// birbirinden ayrı düşebilirdi; tek doğruluk kaynağı bırakmak daha güvenli.
public struct AlarmTask: Identifiable, Codable, Sendable, Hashable {
    public let id: UUID
    public var configuration: TaskConfiguration

    public init(id: UUID = UUID(), configuration: TaskConfiguration) {
        self.id = id
        self.configuration = configuration
    }

    public var kind: TaskKind { configuration.kind }

    public func normalized() -> AlarmTask {
        AlarmTask(id: id, configuration: configuration.normalized())
    }
}
