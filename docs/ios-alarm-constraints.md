# iOS Alarm Kısıtları ve Mimari Kararlar

> Bu doküman Apple'ın güncel dokümantasyonu ve Developer Forums'taki DTS engineer
> yanıtları doğrulanarak yazılmıştır. Kaynaklar en altta.
> Son güncelleme: 2026-08

---

## 1. Temel Karar: AlarmKit

iOS 26 ile Apple **AlarmKit** framework'ünü yayınladı. Bu framework tam olarak bu
projenin ihtiyacı olan şeyi yapıyor: üçüncü parti uygulamaların **gerçek sistem
alarmı** kurabilmesi.

AlarmKit öncesi dönemde bir alarm uygulaması şunlardan birine mecburdu:

| Eski yöntem | Problemi |
|---|---|
| `UNNotificationSound` ile local notification | Ses **max 30 saniye**. Sessiz moddayken hiç çalmaz. Focus'u geçemez. |
| Arka planda `AVAudioSession` + `UIBackgroundModes: audio` | Uygulama zaten çalıyor olmalı. Suspend/force-quit sonrası ölür. App Store reddi riski yüksek. |
| Critical Alerts entitlement | Apple'dan özel onay gerekir, pratikte sadece sağlık/güvenlik uygulamalarına verilir. Alarm uygulamasına verilmez. |

**Sonuç: AlarmKit kullanıyoruz. Yukarıdaki üç yöntemin hiçbirini kullanmıyoruz.**

Bu, orijinal spec'te planlanan "arka plan audio + notification zinciri" mimarisini
tamamen ortadan kaldırıyor. Daha az kod, daha yüksek güvenilirlik, App Store riski yok.

### Deployment target: iOS 26.0

AlarmKit iOS 26'dan önce yok. Kapsama (Temmuz 2026 sonu):

- iOS 26: **%85.12**
- iOS 27: %3.00
- **Toplam ~%88**

Yeni bir uygulama için fazlasıyla yeterli. iOS 18-25 desteği istenirse yukarıdaki
üç kırık yöntemden birine dönmek gerekir — önerilmez.

**Platform notu:** AlarmKit iOS, iPadOS ve Mac Catalyst'te var. watchOS/visionOS yok.

---

## 2. EN ÖNEMLİ KISIT: Kullanıcı alarmı her zaman susturabilir

> **Bu, uygulamanın orijinal fikrinin bir kısmının iOS'ta imkânsız olduğu anlamına gelir.**

AlarmKit alarmı çaldığında sistem kendi UI'ını gösterir. Bu UI'da bir **Stop butonu
zorunludur** (`AlarmPresentation.Alert` init'i `stopButton` parametresini şart koşar).
Ayrıca Apple FAQ'da açıkça belirtiliyor:

- Herhangi bir **fiziksel butona** basmak çalan alarmı durdurur.
- Birden fazla fiziksel butona basmak **çalan tüm alarmları** durdurur.

Yani "kullanıcı görevleri bitirmeden ses durmasın" **teknik olarak sağlanamaz.**
Bunu sağlıyormuş gibi kod yazmak dürüst olmaz.

### Bunun yerine ne yapıyoruz: Follow-up Alarm Zinciri

Sesi durdurmayı engelleyemeyiz, ama **alarmın geri gelmesini garanti edebiliriz.**

```
Alarm kurulurken tek bir alarm değil, bir ZİNCİR planlanır:

  07:30:00  →  ana alarm
  07:31:00  →  follow-up #1
  07:33:00  →  follow-up #2
  07:36:00  →  follow-up #3
  07:40:00  →  follow-up #4
  ...

Kullanıcı görevleri TAMAMLADIĞINDA → kalan tüm follow-up'lar iptal edilir.
Kullanıcı Stop'a basıp yatağa dönerse → 60 saniye sonra alarm geri gelir.
```

Bu tasarımın kritik avantajı: **hiçbir kod çalışmasına bağımlı değil.** Zincir alarm
kurulurken sistem tarafına yazılır. Uygulama force-quit edilse, çökse, telefon yeniden
başlatılsa bile follow-up'lar planlandığı gibi çalar.

### Neden `stopIntent`'e güvenmiyoruz

AlarmKit'te alarmın kapatıldığını yakalamak için `AlarmConfiguration`'a `stopIntent`
verilebilir. Cazip görünüyor ama **iOS 26.2.1'de güvenilir değil:**

- Ekran kilidi açıkken kullanıcı alarmla etkileşirse → alarm kapanıyor, `stopIntent`
  **çalışmıyor**.
- Live Activity banner'ı yukarı kaydırılırsa → alarm duruyor, `stopIntent`
  **çalışmıyor**.

Apple DTS engineer bu davranışı "kayda değer" bulup test projesi istemiş; forumda
çözülmüş bir yanıt veya düzeltme tarihi yok.

**Karar:** `stopIntent`'i *ek sinyal* olarak kullanacağız (çalışırsa zinciri
agresifleştirir), ama **omurga follow-up zinciri**. Çalışmayan bir API'ye ürünün
temel vaadini bağlamıyoruz.

---

## 3. Senaryo Tablosu

| # | Senaryo | Alarm çalar mı? | Ses | Kullanıcı ne görür | Görevler | Uygulamaya dönüş |
|---|---|---|---|---|---|---|
| **A** | App foreground | ✅ Evet | Sistem alarm sesi | AlarmKit alert UI (uygulamanın üstünde) | ✅ Doğrudan devam | Zaten açık |
| **B** | App background | ✅ Evet | Sistem alarm sesi | Alert + Dynamic Island / Live Activity | ⚠️ Uygulama öne gelmeli | Secondary button → `LiveActivityIntent` (`openAppWhenRun = true`) |
| **C** | Telefon kilitli | ✅ Evet | Sistem alarm sesi | Lock Screen'de tam alarm UI | ❌ Kilit açılana kadar hayır | Butona bas → Face ID/passcode → app açılır |
| **D** | Telefon açık | ✅ Evet | Sistem alarm sesi | Alert UI | ✅ Evet | Butona bas |
| **E** | App suspended | ✅ Evet | Sistem alarm sesi | Alert UI | ⚠️ Uygulama uyandırılır | Secondary button |
| **F** | **App force-quit** | ✅ **Evet** | Sistem alarm sesi | Alert UI | ⚠️ Uygulama sıfırdan açılır | Secondary button — state'i diskten geri yüklemeliyiz |
| **G** | Bildirim izni kapalı | ✅ Evet | Etkilenmez | Normal | ✅ Evet | AlarmKit ayrı bir izin kullanır (`NSAlarmKitUsageDescription`), `UNUserNotificationCenter` iznine bağlı **değildir** |
| **G2** | **AlarmKit izni reddedilmiş** | ❌ **Hayır** | Yok | Hiçbir şey | ❌ Hayır | Uygulama işlevsiz. Onboarding'de sert kapı gerekir. |
| **H** | Focus / DND açık | ✅ Evet | Çalar | Normal alert | ✅ Evet | AlarmKit **tüm Focus modlarını deler** (Apple FAQ) |
| **I** | Low Power Mode | ✅ Evet | Çalar | Normal alert | ✅ Evet | ⚠️ Live Activity güncelleme sıklığı düşebilir — gerçek cihazda test edilecek |
| **J** | Silent Mode / ringer switch | ✅ Evet | **Çalar** | Normal alert | ✅ Evet | AlarmKit sessiz modu **deler** (Apple FAQ) |

### Ek riskli senaryolar (Apple Developer Forums'tan)

| # | Senaryo | Davranış | Bizim aksiyonumuz |
|---|---|---|---|
| **K** | Uygulama Face ID/passcode ile kilitli **veya** Hidden Apps klasöründe | ❌ Alarm **sessizce hiç çalmaz** | Onboarding'de açık uyarı. İlk çalıştırmada tespit edip kullanıcıyı uyaracak bir kontrol ekleyeceğiz. |
| **L** | Ön plandaki bir uygulama **landscape** moddayken | ⚠️ Alarmın çalmadığı raporlanmış | Test listesine alındı. Bizim tarafımızda workaround yok. |
| **M** | Aynı anda birden fazla uygulamanın alarmı | ⚠️ Hangisinin çalacağı **deterministik değil** | Kullanıcıya "sistem Saat uygulaması alarmını da kurma" önerisi. |
| **N** | Uygulama silinmiş | Alarm yine çalar, ama uygulama adı yerine bundle ID gösterir | Aksiyon yok. |
| **O** | Cihaz yeniden başlatıldı | ✅ Alarmlar korunur (Apple FAQ) | Ancak kilit açılmadan önce Live Activity yoksa `AlarmPresentation.Paused` gösterilir. |
| **P** | Çok fazla alarm planlandı | `maximumLimitReached` hatası döner. Sabit bir sayı dokümante edilmemiş. | Follow-up zinciri **sınırlı tutulmalı** (alarm başına ~5-6). Zinciri sonsuz yapamayız. |

---

## 4. Görev (Task) Kısıtları

### Shake görevi — CoreMotion

`CMMotionManager` accelerometer verisi **sadece uygulama foreground'dayken** akar.
Uygulama background'a geçtiğinde durur. Background execution mode'u yok.

**Sonuç:** Shake görevi ancak kullanıcı uygulamayı açtıktan sonra çalışır. Akış zaten
böyle olduğu için bu bir sorun değil — sadece "arka planda sallamayı say" gibi bir
tasarım yapılamaz.

**Simulator:** accelerometer **yok**. Shake görevi simulator'da test edilemez.
Bu yüzden `MotionService` bir protokol arkasına alınacak ve simulator/test için
sahte (fake) bir implementasyon kullanılacak.

### Photo görevi — Kamera

- `NSCameraUsageDescription` zorunlu.
- Kullanıcı kamera iznini reddedebilir → görev tamamlanamaz → **fallback gerekir**
  (izin yoksa o görevi atla veya alternatif görev sun, yoksa kullanıcı alarmda kilitlenir).
- Uygulama kamera açıkken kapatılırsa: görev state'i diske yazılmış olmalı, açılışta
  aynı görevden devam edilmeli.
- MVP'de nesne tanıma yok — çek + onayla. Vision/Core ML sonradan `PhotoValidator`
  protokolünün arkasına eklenecek.
- Fotoğraflar **cihazda kalır**, hiçbir yere gönderilmez, görev bitince silinir.

### Math görevi

Donanım bağımsız. Tamamen `WakeTaskCore` içinde, Windows/Linux'ta test edilebilir.

---

## 5. Ses (Audio)

### Alarm sesi
AlarmKit yönetir. `AlertConfiguration`'a `sound:` parametresi verilir.
Custom ses: `AlertConfiguration.AlertSound.named("dosya.caf")` — dosya app bundle'ında
veya `Library/Sounds` klasöründe olmalı, **uzantısıyla birlikte** yazılır.

⚠️ **Doğrulanmamış:** Forumda custom sound'un çalışmayıp default sesin çaldığı
bildirilmiş. Apple DTS yanıt vermiş ama thread'de kesin çözüm yok.
**Karar:** Ses seçimi bir abstraction arkasına alınacak, MVP `.default` ile
çalışacak şekilde kurulacak, custom sesler gerçek cihazda doğrulandıktan sonra
aktifleştirilecek.

### Uygulama içi ses
Görev ekranı açıkken uygulama kendi sesini `AVAudioSession` `.playback` kategorisiyle
çalabilir. Burada background audio mode'una **gerek yok** — çünkü ses sadece kullanıcı
uygulamayı açıkça kullanırken çalıyor.

### Telif
Hiçbir telifli ses kullanılmayacak. Sesler ya sentetik üretilecek ya da CC0 kaynaktan
alınacak, lisans bilgisi `Resources/Sounds/LICENSE.md` içinde tutulacak.

---

## 6. Gerekli İzinler ve Info.plist

| Anahtar | Neden |
|---|---|
| `NSAlarmKitUsageDescription` | Alarm kurabilmek için (zorunlu) |
| `NSCameraUsageDescription` | Photo görevi |
| `NSMotionUsageDescription` | Shake görevi (CoreMotion) |
| `NSSupportsLiveActivities` = `YES` | AlarmKit alert UI'ı Live Activity kullanır |

**Gerekmeyenler:** `UIBackgroundModes` (audio dahil), Push Notification entitlement,
Critical Alerts entitlement, konum izni, Photo Library izni (fotoğrafı kaydetmiyoruz).

Privacy Manifest (`PrivacyInfo.xcprivacy`) gerekli — ama veri toplamadığımız için
"no data collected" olarak beyan edilecek.

---

## 7. Mimari Sonuçlar

Bu kısıtların koda yansıması:

1. **Ayrı bir Widget Extension target'ı gerekiyor** (Live Activity için). AlarmKit
   bunu zorunlu kılıyor. Tek target'lı bir proje olmayacak.
2. **Alarm state diske yazılmalı** — force-quit sonrası görev akışı kaldığı yerden
   devam edebilmeli.
3. **Follow-up zinciri persistence'a bağlı** — hangi alarm ID'lerinin hangi alarma
   ait olduğu saklanmalı ki görev bitince iptal edilebilsin.
4. **`WakeTaskCore` platform bağımsız kalmalı** — zincir hesabı, tekrar günleri,
   math üretimi, görev sırası burada. Böylece Mac olmadan test edilebilir.
5. **Donanıma bağlı her şey protokol arkasında** — `MotionService`, `CameraService`,
   `AlarmScheduling`. Fake implementasyonlarla Linux'ta test edilir.

---

## 8. Gerçek Cihaz Test Listesi (Phase 11)

Simulator'da doğrulanamayacak, **iPhone şart** olanlar:

- [ ] Alarm kilitli ekranda çalıyor mu
- [ ] Sessiz moddayken (ringer switch kapalı) çalıyor mu
- [ ] Focus / DND açıkken çalıyor mu
- [ ] Force-quit sonrası çalıyor mu
- [ ] Yeniden başlatma sonrası çalıyor mu
- [ ] Follow-up zinciri gerçekten geliyor mu, iptal doğru çalışıyor mu
- [ ] `stopIntent` hangi durumlarda çalışıyor (bizim varsayımımızı doğrula)
- [ ] Custom ses gerçekten çalıyor mu, yoksa default'a mı düşüyor
- [ ] Shake görevi — gerçek accelerometer eşik değerleri
- [ ] Kamera görevi — izin reddi akışı
- [ ] Low Power Mode'da Live Activity davranışı
- [ ] Uygulama Face ID ile kilitliyse alarm gerçekten sessizce mi düşüyor
- [ ] Landscape bug'ı bizde tekrar ediyor mu
- [ ] `maximumLimitReached` — kaç alarmda tetikleniyor

---

## Kaynaklar

- [AlarmKit — Apple Developer Documentation](https://developer.apple.com/documentation/alarmkit)
- [Wake up to the AlarmKit API — WWDC25 Session 230](https://developer.apple.com/videos/play/wwdc2025/230/)
- [WWDC25-230 notes](https://wwdcnotes.com/documentation/wwdc25-230-wake-up-to-the-alarmkit-api/)
- [AlarmKit FAQ — Apple Developer Forums #797158](https://developer.apple.com/forums/thread/797158)
- [AlarmKit — Behaviors when dismissing alarms — Forums #815064](https://developer.apple.com/forums/thread/815064)
- [AlarmKit custom sounds — Forums #814732](https://developer.apple.com/forums/thread/814732)
- [AlarmPresentation.Alert.SecondaryButtonBehavior.countdown](https://developer.apple.com/documentation/alarmkit/alarmpresentation/alert-swift.struct/secondarybuttonbehavior-swift.enum/countdown)
- [iOS sürüm dağılımı — TelemetryDeck](https://telemetrydeck.com/survey/apple/iOS/majorSystemVersions/)
