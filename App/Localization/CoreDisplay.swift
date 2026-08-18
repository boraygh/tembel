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

extension PremiumFeature {
    /// Ödeme duvarındaki gösterim sırası — en güçlü gerekçe önce.
    static var displayOrder: [PremiumFeature] {
        [.unlimitedAlarms, .photoTask, .moreTasksPerAlarm, .allSounds, .customFollowUpChain]
    }

    var title: String {
        switch self {
        case .unlimitedAlarms: AppStrings.Premium.featureUnlimitedTitle
        case .photoTask: AppStrings.Premium.featurePhotoTitle
        case .moreTasksPerAlarm: AppStrings.Premium.featureTasksTitle
        case .allSounds: AppStrings.Premium.featureSoundsTitle
        case .customFollowUpChain: AppStrings.Premium.featureChainTitle
        }
    }

    var detail: String {
        switch self {
        case .unlimitedAlarms: AppStrings.Premium.featureUnlimitedDetail
        case .photoTask: AppStrings.Premium.featurePhotoDetail
        case .moreTasksPerAlarm: AppStrings.Premium.featureTasksDetail
        case .allSounds: AppStrings.Premium.featureSoundsDetail
        case .customFollowUpChain: AppStrings.Premium.featureChainDetail
        }
    }

    var symbolName: String {
        switch self {
        case .unlimitedAlarms: "infinity"
        case .photoTask: "camera.fill"
        case .moreTasksPerAlarm: "square.stack.3d.up.fill"
        case .allSounds: "speaker.wave.3.fill"
        case .customFollowUpChain: "link"
        }
    }
}

extension Alarm {
    /// Başlık boşsa listede yerine gösterilecek metin.
    var displayTitle: String {
        title.isEmpty ? AppStrings.Home.untitledAlarm : title
    }

    /// Tekrar günlerinin okunabilir özeti.
    ///
    /// Yedi gün rozetini her yerde göstermek yerine yaygın seçimler
    /// adlandırılıyor — "Hafta içi", yedi kutucuktan çok daha hızlı okunur.
    var repeatSummary: String {
        if repeatDays.isEmpty { return AppStrings.Home.noRepeat }
        if repeatDays == .everyday { return AppStrings.Home.everyday }
        if repeatDays == .weekdays { return AppStrings.Home.weekdays }
        if repeatDays == .weekend { return AppStrings.Home.weekend }
        return orderedRepeatDays.map(\.shortLabel).joined(separator: ", ")
    }
}
