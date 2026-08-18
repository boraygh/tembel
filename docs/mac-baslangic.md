# Mac'e Geçiş Kılavuzu

Bu proje Mac olmadan geliştirildi. `TembelCore` gerçekten derlenip test edildi;
`App/` klasöründeki SwiftUI kodu **hiçbir yerde derlenmedi**. Bu doküman Mac
edinildiğinde izlenecek sırayı ve ilk gün karşılaşılacakları anlatır.

---

## 1. Projeyi ayağa kaldır

```bash
brew install xcodegen
cd tembel
xcodegen generate
open Tembel.xcodeproj
```

Gerekenler: **Xcode 26+** (AlarmKit ve Swift 6.2 için), macOS Tahoe 26+.

`.xcodeproj` repoda tutulmuyor — `project.yml`'den üretiliyor. Proje yapısı
değişirse (yeni target, yeni ayar) `project.yml` düzenlenip komut tekrar
çalıştırılır.

## 2. İlk derlemede beklenenler

Derlenmemiş ~1500 satır SwiftUI var. Hataların büyük ihtimalle çıkacağı yerler,
riskli olandan sırayla:

| Yer | Neden riskli |
|---|---|
| `App/Services/MotionService.swift` | CoreMotion + Swift 6 eşzamanlılık. `AsyncStream.makeStream` ile en güvenli biçime getirildi ama doğrulanmadı. |
| `App/Features/AlarmRinging/Tasks/CameraPicker.swift` | `UIViewControllerRepresentable` + delegate isolation. |
| `App/Features/AlarmEditor/AlarmEditorView.swift` | `List` + `.onMove` + özel satır biçimi; en uzun dosya. |
| `Theme.Typography` | Yazı tipi kaydı. Hata vermez ama font yüklenmezse sessizce sistem yazı tipine düşer. |

**Hata çıkarsa** bana Xcode çıktısını olduğu gibi gönder. Tüm dosyayı yeniden
yazmam gerekmez; hata mesajı hangi satırı gösteriyorsa oraya bakarız.

## 3. İlk doğrulama: Demo Mode

AlarmKit'e hiç dokunmadan tüm görev akışı denenebilir:

> Ayarlar → Geliştirme → **Demo alarmı başlat**

Simulator'da çalışır. Beklenen davranış:

1. Sallama görevi sahte sensörle kendiliğinden ilerler (5 sallama).
2. Matematik görevi — tuş takımı, doğru cevapta anında ilerleme.
3. Fotoğraf görevi — Simulator'da kamera olmadığı için fotoğraf kütüphanesi
   açılır.
4. "Alarm tamamlandı" ekranı.

Demo Mode yalnızca `DEBUG` derlemelerinde vardır.

## 4. Yazı tipini doğrula

`App/Resources/Fonts/` altındaki beş Archivo dosyası `project.yml` içindeki
`UIAppFonts` listesinde kayıtlı. Yüklenip yüklenmediğini görmek için:

```swift
// Geçici olarak bir view'ın onAppear'ına koy
UIFont.familyNames.filter { $0.contains("Archivo") }.forEach { print($0) }
```

Boş çıkarsa font kaydı çalışmıyor demektir — düzen bozulmaz, sadece karakter
kaybolur.

---

## 5. Kalan iş: AlarmKit

Bu noktadan sonrası gerçek geliştirme. Yapılacaklar sırasıyla:

1. **İzin akışı** — `AlarmManager.shared.authorizationState`, onboarding'de
   sert kapı. İzin yoksa uygulama işlevsizdir, bunu kullanıcıya açıkça söyle.
2. **Zamanlama** — `AlarmScheduler.firePlan(...)` zaten planı üretiyor
   (`ScheduledFire` listesi). Yapılacak tek şey bu listeyi AlarmKit alarmlarına
   çevirmek. `ScheduledFire.id` sistemdeki alarm kimliği olacak.
3. **Zincir iptali** — görevler bitince `ScheduledFire.alarmID(fromFireID:)`
   ile o alarma ait kalan alarmları iptal et.
4. **Uygulamayı açma** — `LiveActivityIntent` + `openAppWhenRun = true`,
   alarm kimliğini parametre olarak taşı, `AlarmSessionModel.start(alarm:)`
   çağır.
5. **Widget Extension** — AlarmKit alert UI'ı Live Activity kullanıyor,
   ayrı target gerekiyor. `project.yml`'e eklenecek.
6. **Ses** — `AlertConfiguration.AlertSound`. Önce `.default` ile çalıştır,
   özel sesler ancak gerçek cihazda doğrulandıktan sonra açılsın
   (`AlarmSound.availableForSelection` şu an bunu kilitliyor).

Ayrıntılı kısıtlar ve tuzaklar: [`ios-alarm-constraints.md`](ios-alarm-constraints.md)

---

## 6. Gerçek cihazda doğrulanacaklar

Ücretsiz Apple ID ile 7 günlük imzalama MVP için yeterli; $99/yıl hesap
gerekmez.

Simulator'ın **yalan söylediği** konular — bunlar iPhone'da test edilmeden
"çalışıyor" sayılmamalı:

- [ ] Alarm kilitli ekranda çalıyor mu
- [ ] Sessiz modda (ringer kapalı) çalıyor mu
- [ ] Focus / Rahatsız Etmeyin açıkken çalıyor mu
- [ ] Force-quit sonrası çalıyor mu
- [ ] Yeniden başlatma sonrası çalıyor mu
- [ ] **Takip zinciri gerçekten geliyor mu, görev bitince iptal oluyor mu**
- [ ] `stopIntent` hangi durumlarda çalışıyor (zincire güveniyoruz ama bilelim)
- [ ] Özel ses çalıyor mu, yoksa varsayılana mı düşüyor
- [ ] **Sallama eşikleri** — `ShakeDetectorConfiguration.default` (1.8 / 0.8 /
      0.18) gerçek elde makul mü? Algoritma test edildi, sayılar edilmedi.
- [ ] Kamera izni reddi akışı
- [ ] Uygulama Face ID ile kilitliyse alarm sessizce düşüyor mu
- [ ] Landscape'te alarm çalmama hatası bizde tekrar ediyor mu

## 7. Premium (StoreKit 2)

Backend yok. Apple'ın imzaladığı işlemler cihazda doğrulanıyor; kullanıcı
hesabı, sunucu veya abonelik veritabanı gerekmiyor. Haklar Apple ID'ye bağlı
olduğu için kullanıcının diğer cihazlarında da geçerli oluyor.

### Ürün kimlikleri

`App/Services/PremiumProduct.swift` içinde sabit:

| Kimlik | Tür |
|---|---|
| `com.boray.tembel.premium.monthly` | Otomatik yenilenen abonelik |
| `com.boray.tembel.premium.yearly` | Otomatik yenilenen abonelik |
| `com.boray.tembel.premium.lifetime` | Non-consumable (tek seferlik) |

**Fiyatlar kodda yok** — App Store Connect'te belirlenir, uygulama StoreKit'ten
okuyup gösterir. Ülkeye göre değişen ve senin sonradan değiştirebileceğin bir
bilgiyi koda gömmek yanlış olurdu.

Aylık ve yıllık aynı **abonelik grubunda** olmalı; aksi hâlde kullanıcı ikisine
birden abone olabilir.

### Mac gelir gelmez: gerçek satın alma olmadan test

App Store Connect'e hiç dokunmadan denenebilir:

1. Xcode → File → New → File → **StoreKit Configuration File**
2. Üç ürünü yukarıdaki kimliklerle ekle, fiyat ata
3. Scheme → Edit Scheme → Run → Options → **StoreKit Configuration** olarak seç

Bu dosyayı repoya elle yazmadım: biçimi Xcode'a ait ve elle üretilmiş bozuk bir
dosya, çalışmadığında nedenini bulmayı zorlaştırır. Xcode üç tıkta üretiyor.

### App Store'a göndermeden önce zorunlu

- [ ] **Gizlilik politikası URL'si** — `App/Features/Premium/LegalLinks.swift`
      içinde `privacyPolicy` şu an `nil`. Abonelik satan bir ekranda bu bağlantı
      zorunlu; eksikse uygulama reddedilir.
- [ ] Kullanım koşulları — Apple'ın standart EULA adresi kodda hazır, kendi
      sözleşmen varsa değiştir.
- [ ] "Satın alımları geri yükle" düğmesi — kodda var, çalıştığını doğrula.
- [ ] Sandbox hesabıyla gerçek satın alma, iptal ve geri yükleme akışı.

### Ödeme duvarı politikası

`Core/Sources/TembelCore/Premium/Entitlement.swift` başındaki nota dikkat:
alarmın çalması, takip alarm zinciri ve görevlerin zorunlu olması **hiçbir zaman
satılmaz**. Ücretsiz kullanıcının "alarm kurdum" sanıp uyanamaması kabul
edilemez. `EntitlementTests` bunu bir test olarak sabitliyor.

Ücretsiz sınırlar: 2 alarm, alarm başına 2 görev, salla + matematik görevleri,
varsayılan ses.

---

## 8. App Store öncesi

- [ ] Demo Mode gerçekten Release'te görünmüyor mu (`#if DEBUG` doğrula)
- [ ] `PrivacyInfo.xcprivacy` — veri toplamıyoruz, "no data collected"
- [ ] App Icon (henüz yok — asset catalog eklenmedi)
- [ ] İzin metinleri (`project.yml` içinde hazır) inceleme için yeterince açık mı
- [ ] Archivo lisansı: `App/Resources/Fonts/LICENSE.md` (SIL OFL 1.1, uyumlu)
