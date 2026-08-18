import SwiftUI
import TembelCore

// TembelCore platform bağımsızdır ve içinde gösterim metni tutmaz.
// Çekirdek tiplerin ekranda nasıl göründüğü burada tanımlanır.

extension Weekday {
    /// Gün kısaltması — Pzt, Sal, …
    var shortLabel: String {
        switch self {
        case .monday: "Pzt"
        case .tuesday: "Sal"
        case .wednesday: "Çar"
        case .thursday: "Per"
        case .friday: "Cum"
        case .saturday: "Cmt"
        case .sunday: "Paz"
        }
    }
}

extension TimeOfDay {
    /// 07:30 biçiminde, her zaman iki haneli.
    var displayText: String {
        String(format: "%02d:%02d", hour, minute)
    }
}

extension TaskKind {
    var title: String {
        switch self {
        case .shake: "Salla"
        case .math: "Matematik"
        case .photo: "Fotoğraf"
        }
    }

    var summary: String {
        switch self {
        case .shake: "Telefonu belirlediğin kadar salla"
        case .math: "İşlemi doğru çözmeden kapanmaz"
        case .photo: "Belirlediğin nesnenin fotoğrafını çek"
        }
    }

    /// SF Symbol adı.
    var symbolName: String {
        switch self {
        case .shake: "iphone.radiowaves.left.and.right"
        case .math: "plus.forwardslash.minus"
        case .photo: "camera.fill"
        }
    }
}

extension MathDifficulty {
    var title: String {
        switch self {
        case .easy: "Kolay"
        case .medium: "Orta"
        case .hard: "Zor"
        }
    }
}

extension TaskConfiguration {
    /// Görev kartında başlığın altında görünen özet.
    var detailText: String {
        switch self {
        case .shake(let count):
            "\(count) kez"
        case .math(let difficulty, let questionCount):
            questionCount == 1
                ? difficulty.title
                : "\(difficulty.title) · \(questionCount) soru"
        case .photo(let prompt):
            prompt.isEmpty ? AppStrings.Editor.photoPromptMissing : prompt
        }
    }
}

extension AlarmSound {
    var title: String {
        switch self {
        case .systemDefault: "Varsayılan"
        case .aggressive: "Agresif"
        case .siren: "Siren"
        case .digital: "Dijital"
        case .emergency: "Acil"
        case .buzzer: "Zil"
        }
    }
}

extension Alarm {
    /// Başlık boşsa listede yerine gösterilecek metin.
    var displayTitle: String {
        title.isEmpty ? AppStrings.Home.untitledAlarm : title
    }
}
