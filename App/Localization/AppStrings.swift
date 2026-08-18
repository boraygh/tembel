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
        static let everyday = "Her gün"
        static let weekdays = "Hafta içi"
        static let weekend = "Hafta sonu"
        static let delete = "Sil"
        static let edit = "Düzenle"
        static let nextAlarmPrefix = "Sonraki alarm "
        static let limitHint = "Ücretsiz sürümde iki alarm kurabilirsin. Sınırsız için Premium."
        static let noEnabledAlarm = "Açık alarm yok"

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
        static let addTaskPremium = "Daha fazla görev için Premium"
        static let taskLimitReached = "En fazla 5 görev eklenebilir."
        static let premiumBadge = "PREMIUM"
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

    enum Ringing {
        static let wakeUp = "KALK"
        static let completedTitle = "Alarm tamamlandı"
        static let completedMessage = "Günaydın. Artık uyanıksın."
        static let dismiss = "Kapat"
        static let snooze = "Ertele"
        static let noSnoozeLeft = "Erteleme hakkın bitti"

        static func taskProgress(current: Int, total: Int) -> String {
            "GÖREV \(current) / \(total)"
        }

        static func snoozeRemaining(_ count: Int) -> String {
            "\(count) hak kaldı"
        }
    }

    enum ShakeTask {
        static let instruction = "Telefonu salla"
        static let unavailable = "Bu cihazda hareket sensörü yok"
        static let unavailableHelp =
            "Sallama görevi gerçek iPhone gerektirir. Simulator'da ivmeölçer bulunmaz."
        static let simulatorTap = "Simulator: saymak için dokun"

        static func progress(_ done: Int, _ target: Int) -> String { "\(done) / \(target)" }
    }

    enum MathTask {
        static let wrongAnswer = "Yanlış"

        static func questionProgress(current: Int, total: Int) -> String {
            total == 1 ? "" : "\(current) / \(total)"
        }
    }

    enum PhotoTask {
        static let openCamera = "Kamerayı aç"
        static let retake = "Tekrar çek"
        static let confirm = "Bu doğru fotoğraf"
        static let permissionDenied = "Kamera izni kapalı"
        static let permissionHelp =
            "Ayarlar → Tembel → Kamera bölümünden izin vermen gerekiyor."
        static let privacyNote = "Fotoğraf cihazından çıkmaz ve görev bitince silinir."
    }

    enum Premium {
        static let tab = "Premium"
        static let title = "Tembel Premium"
        static let tagline =
            "Uyanmayı daha da zorlaştır. Alarmın çalması ve geri gelmesi her zaman ücretsiz."
        static let subscribe = "Premium'a geç"
        static let restore = "Satın alımları geri yükle"
        static let cancelAnytime = "İstediğin zaman iptal edebilirsin."
        static let terms = "Kullanım Koşulları"
        static let privacy = "Gizlilik"
        static let recommended = "EN İYİ"

        // Aktif üyelik
        static let activeTitle = "Premium üyesin"
        static let activeLifetime = "Ömür boyu erişimin var."
        static let manage = "Aboneliği yönet"
        static let unlockedSection = "Açık özellikler"

        static func activeUntil(_ date: String) -> String {
            "\(date) tarihine kadar geçerli."
        }

        static func perMonth(_ price: String) -> String { "ayda \(price)" }

        // Özellik listesi
        static let featureUnlimitedTitle = "Sınırsız alarm"
        static let featureUnlimitedDetail = "Ücretsizde iki alarmla sınırlısın"
        static let featurePhotoTitle = "Fotoğraf görevi"
        static let featurePhotoDetail = "Yatakta yatarak çekemeyeceğin bir şey seç"
        static let featureTasksTitle = "Alarm başına 5 görev"
        static let featureTasksDetail = "Ücretsizde 2 görev ekleyebilirsin"
        static let featureSoundsTitle = "Tüm alarm sesleri"
        static let featureSoundsDetail = "Siren, acil durum, zil ve diğerleri"
        static let featureChainTitle = "Zincir ayarı"
        static let featureChainDetail = "Takip alarmlarının sıklığını sen belirle"

        // Sınıra takılma
        static let alarmLimitTitle = "Alarm sınırına ulaştın"
        static let taskLimitTitle = "Görev sınırına ulaştın"
        static let photoLockedTitle = "Fotoğraf görevi premium"

        // Hatalar
        static let loadFailed = "Satın alma seçenekleri yüklenemedi."
        static let productUnavailable = "Bu seçenek şu an kullanılamıyor."
        static let purchaseFailed = "Satın alma tamamlanamadı."
        static let verificationFailed = "Satın alma doğrulanamadı."
        static let purchasePending = "Satın alma onay bekliyor."
        static let restoreFailed = "Geri yükleme başarısız oldu."
        static let nothingToRestore = "Geri yüklenecek satın alma bulunamadı."
    }

    enum Demo {
        static let section = "Geliştirme"
        static let title = "Demo Mode"
        static let help =
            "Alarm beklemeden görev akışını baştan sona dener. Sallama görevi sahte sensör verisiyle kendiliğinden ilerler."
        static let start = "Demo alarmı başlat"
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
