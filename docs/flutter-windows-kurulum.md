# Flutter — Windows Kurulumu

Bu doküman `flutter_app/` klasöründeki Flutter sürümünü **kendi Windows
bilgisayarında** çalıştırmak içindir.

> **Neden Flutter?** iOS'ta gerçek alarm (AlarmKit) için yine Swift, Xcode ve
> Mac gerekir — Flutter bunu kaldırmaz. Kazanç şu: **bugün, Mac olmadan,
> uygulamayı kendi bilgisayarında çalıştırıp görebilirsin.** Android'i de
> bedavaya alırsın. Ayrıntı: [`ios-alarm-constraints.md`](ios-alarm-constraints.md)

---

## 1. Flutter SDK (zorunlu, ~1 GB)

PowerShell'i **normal kullanıcı** olarak aç (yönetici gerekmez):

```powershell
# İndir ve C:\src\flutter içine aç
New-Item -ItemType Directory -Force -Path C:\src | Out-Null
Invoke-WebRequest `
  -Uri "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.47.1-stable.zip" `
  -OutFile "$env:TEMP\flutter.zip"
Expand-Archive -Path "$env:TEMP\flutter.zip" -DestinationPath C:\src -Force
Remove-Item "$env:TEMP\flutter.zip"

# PATH'e kalıcı olarak ekle
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike '*C:\src\flutter\bin*') {
  [Environment]::SetEnvironmentVariable('Path', "$userPath;C:\src\flutter\bin", 'User')
}
```

İndirme birkaç dakika sürer. Bitince **PowerShell'i kapat/aç** ve doğrula:

```powershell
flutter --version
```

`Flutter 3.47.1` görmelisin. Container'da kullanılan sürüm de bu; aynı sürümde
kalmak sürpriz farkları önler.

## 2. Chrome (uygulamayı görmenin en hızlı yolu)

```powershell
# Kuruluysa atla
winget install --id Google.Chrome -e --source winget
```

## 3. Çalıştır

```powershell
cd <projenin-yolu>\tembel\flutter_app
flutter pub get
flutter run -d chrome
```

Ana sayfa açılır. Kod değiştirip kaydedince terminalde **`r`** tuşuna basmak
ekranı anında günceller (hot reload).

---

## Ne kurmadık ve neden

| Hedef | Gereken | Durum |
|---|---|---|
| **Web (Chrome)** | Sadece Flutter + Chrome | ✅ Yukarıdaki adımlar yeter |
| Windows masaüstü | Visual Studio 2022 + "Desktop development with C++" (~7 GB) | ⏸️ Gerekmiyor — web zaten gösteriyor |
| Android | Android Studio + JDK (~10 GB) | ⏸️ Gerçek alarm denemek isteyince |
| iOS | macOS + Xcode | ⏸️ Mac gerekiyor |

Web ile başlamak bilinçli: **7 GB'lık kurulum yapmadan** uygulamanın tamamını
görüp tıklayabilirsin. Gerçek alarm davranışını denemek istediğinde Android'i
kurarız — Android'de exact alarm API'si var ve iOS'un aksine ciddi bir kısıt yok.

---

## Doğrulama

```powershell
flutter analyze   # uyarı olmamalı
flutter test      # 76 test geçmeli
```

Bu iki komut container'da da çalıştırılıyor; sende farklı sonuç çıkarsa sürüm
uyuşmazlığı vardır, önce `flutter --version` kontrol et.

---

## Proje yapısı

```
flutter_app/
├── lib/
│   ├── core/                 platform bağımsız mantık (Swift'teki TembelCore'un karşılığı)
│   │   ├── models/           Alarm, ClockTime, AlarmTask, SnoozeSetting, Weekday
│   │   ├── scheduling/       sonraki çalma zamanı + takip alarm zinciri
│   │   ├── tasks/            matematik üretimi, sallama algılama
│   │   ├── session/          görev motoru (force-quit sonrası devam)
│   │   └── premium/          ücretsiz/premium sınırları
│   ├── design/theme.dart     renk, tipografi, malzeme
│   ├── features/home/        ana sayfa
│   └── localization/         tüm metinler
└── test/                     76 test
```

`core/` içine Flutter'a özel hiçbir import girmez (`material.dart` yok). Aynı
kural Swift sürümünde de geçerli — mantık her iki tarafta da UI'dan bağımsız
test edilebiliyor.

## Sıradaki adımlar

- [ ] Alarm düzenleyici ekranı ve kalıcı kayıt (`shared_preferences`)
- [ ] Alarm çalma ekranı + görev ekranları
- [ ] Premium sekmesi (`in_app_purchase` paketi — Apple ve Google birlikte)
- [ ] Android exact alarm entegrasyonu
- [ ] iOS: AlarmKit için Swift platform channel (**Mac gerekir**)
