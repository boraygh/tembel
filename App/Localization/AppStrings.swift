import Foundation

/// Uygulamadaki tüm metinler.
///
/// Tek yerde tutuluyor ki ileride String Catalog'a taşınıp yerelleştirilmesi
/// tek dosyayı gezmekle bitsin.
enum AppStrings {

    enum Brand {
        static let name = "Tembel"
    }

    enum Tabs {
        static let alarms = "Alarmlar"
        static let settings = "Ayarlar"
    }

    enum Home {
        static let title = "Alarmlar"
        static let addAlarm = "Alarm ekle"
        static let emptyTitle = "Henüz alarm yok"
        static let emptyMessage =
            "Kapatmak için görev tamamlaman gereken bir alarm kur. Yataktan kalkmadan susturamazsın."
        static let emptyAction = "İlk alarmını kur"
        static let untitledAlarm = "Alarm"
        static let noRepeat = "Tekrar yok"
        static let delete = "Sil"
        static let edit = "Düzenle"

        static func taskCount(_ count: Int) -> String {
            count == 0 ? "Görev yok" : "\(count) görev"
        }
    }

    enum Editor {
        static let newAlarmTitle = "Yeni Alarm"
        static let editAlarmTitle = "Alarmı Düzenle"
        static let cancel = "Vazgeç"
        static let save = "Kaydet"
        static let namePlaceholder = "Alarm adı"
        static let repeatSection = "Tekrar"
        static let tasksSection = "Görevler"
        static let alarmSection = "Alarm"
        static let addTask = "Görev ekle"
        static let taskLimitReached = "En fazla 5 görev eklenebilir."
        static let sound = "Ses"
        static let soundDefaultValue = "Varsayılan"
        static let soundNote =
            "Özel alarm sesleri gerçek cihazda doğrulandıktan sonra açılacak."
        static let snooze = "Erteleme"
        static let snoozeOffCaption = "Kapalı — görevler zorunlu"
        static let snoozeDuration = "Süre"
        static let snoozeMaxCount = "En fazla"
        static let photoPromptMissing = "Fotoğraf görevine ne çekileceğini yaz."

        static func snoozeOnCaption(minutes: Int, count: Int) -> String {
            "\(minutes) dakika · en fazla \(count) kez"
        }

        static func minutes(_ value: Int) -> String { "\(value) dakika" }
        static func times(_ value: Int) -> String { "\(value) kez" }
    }

    enum TaskEditor {
        static let addTitle = "Görev Ekle"
        static let editTitle = "Görevi Düzenle"
        static let add = "Ekle"
        static let done = "Tamam"
        static let cancel = "Vazgeç"
        static let settingSection = "Ayar"

        static let shakeQuestion = "Kaç kez sallanacak?"
        static let mathDifficulty = "Zorluk"
        static let mathQuestionCount = "Soru sayısı"
        static let photoPrompt = "Ne çekilecek?"
        static let photoPromptPlaceholder = "Örneğin: mutfaktaki kahve makinesi"
        static let photoPromptHelp =
            "Alarm çaldığında bu metni göreceksin. Yataktan kalkmanı gerektiren bir şey seç."
    }

    enum Settings {
        static let title = "Ayarlar"
        static let aboutSection = "Hakkında"
        static let version = "Sürüm"
    }

    enum Accessibility {
        static let increase = "Artır"
        static let decrease = "Azalt"
        static let changeTimeHint = "Saati değiştirmek için dokun"
    }

    enum Errors {
        static let storageTitle = "Alarmlar okunamadı"
        static let corruptedFile =
            "Kayıt dosyası bozuk olduğu için okunamadı. Bozuk dosya silinmedi, yedeğe alındı."
        static let unsupportedVersion =
            "Kayıt dosyası uygulamanın daha yeni bir sürümüyle yazılmış. Uygulamayı güncelle."
        static let saveFailed = "Alarm kaydedilemedi."
    }
}
