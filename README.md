# Tembel

Görev tamamlamadan susmayan iOS alarm uygulaması.

Normal alarmlardan farkı: alarmı kapatmak için fiziksel veya zihinsel bir görevi
tamamlaman gerekir — telefonu sallamak, matematik işlemi çözmek, belirli bir
nesnenin fotoğrafını çekmek gibi.

> **iOS gerçeği:** iOS hiçbir uygulamanın alarm sesini durdurmayı engellemesine
> izin vermez (Stop butonu ve fiziksel butonlar sistem garantisidir). Tembel bunu
> engellemeye çalışmaz; bunun yerine görevler tamamlanana kadar alarmın **geri
> gelmesini** garanti eder. Ayrıntı: [`docs/ios-alarm-constraints.md`](docs/ios-alarm-constraints.md)

---

## Teknoloji

| | |
|---|---|
| Dil | Swift 6 |
| UI | SwiftUI |
| Alarm | **AlarmKit** (iOS 26+) |
| Görevler | CoreMotion, AVFoundation, PhotosUI |
| Veri | Cihaz üzerinde. Backend yok, login yok, analytics yok. |
| Min. iOS | 26.0 |

---

## Proje Yapısı

```
tembel/
├── App/                        iOS uygulama target'ı — Mac gerektirir
│   ├── TembelApp.swift
│   ├── RootView.swift
│   ├── DesignSystem/
│   └── Features/
│       ├── Home/
│       ├── AlarmEditor/
│       └── Settings/
│
├── Core/                       TembelCore — platform bağımsız Swift Package
│   ├── Package.swift           Windows/Linux'ta derlenir ve test edilir
│   ├── Sources/TembelCore/
│   └── Tests/TembelCoreTests/
│
├── docs/
│   └── ios-alarm-constraints.md
│
├── project.yml                 XcodeGen tanımı
└── .github/workflows/          Linux CI — Core testleri
```

**Ayrım kuralı:** SwiftUI, AlarmKit, CoreMotion, AVFoundation gibi Apple'a özel
hiçbir import `Core/` içine girmez. Core yalnızca Foundation kullanır. Böylece
mantığın önemli kısmı Mac olmadan test edilebilir.

---

## Geliştirme

### Windows / Linux üzerinde (Mac gerekmez)

Yalnızca `Core/` paketi derlenip test edilebilir:

```bash
swift build --package-path Core
swift test  --package-path Core
```

Windows'ta Swift toolchain kurulu değilse bu adım atlanabilir — her push'ta
GitHub Actions aynı testleri Linux üzerinde çalıştırır.

### macOS üzerinde

```bash
brew install xcodegen
xcodegen generate
open Tembel.xcodeproj
```

`.xcodeproj` repoda tutulmaz, `project.yml`'den üretilir.

---

## Mac / Gerçek Cihaz Gerektiren İşler

| İş | Nerede |
|---|---|
| Core mantığı, testler, modeller | Windows / Linux / CI |
| Xcode build, Simulator | macOS |
| Alarm davranışı, kilit ekranı, sessiz mod | **Gerçek iPhone** |
| Kamera, accelerometer | **Gerçek iPhone** (Simulator'da yok) |

Gerçek cihaz test listesi: [`docs/ios-alarm-constraints.md`](docs/ios-alarm-constraints.md) § 8

---

## Durum

| Phase | Konu | Durum |
|---|---|---|
| 0 | Ortam + iOS kısıt analizi | ✅ |
| 1 | Proje iskeleti + navigation | ✅ |
| 2 | Alarm modeli + persistence | ✅ |
| 3 | Alarm oluşturma ekranı | ✅ |
| 4 | Zamanlama hesabı + follow-up zinciri | ✅ çekirdek · ⏸️ AlarmKit bağlantısı Mac bekliyor |
| 5 | Alarm çalma ekranı | ✅ ekran · ⏸️ tetikleme Mac bekliyor |
| 6 | Matematik görevi | ✅ |
| 7 | Sallama görevi | ✅ algoritma · ⏸️ eşik ayarı gerçek cihaz bekliyor |
| 8 | Fotoğraf görevi | ✅ akış · ⏸️ kamera gerçek cihaz bekliyor |
| 9 | Alarm sesi | ⏸️ Mac |
| 10 | Görev motoru | ✅ |
| 11 | Gerçek cihaz testi | ⏸️ iPhone |
| 12–14 | UI cilası, edge case'ler, App Store | ⏸️ Mac |

`App/` altındaki SwiftUI kodu henüz hiçbir yerde **derlenmedi** — Mac
gerektiriyor. `Core/` her push'ta Linux üzerinde derlenip test ediliyor.

Mac edinildiğinde izlenecek sıra: [`docs/mac-baslangic.md`](docs/mac-baslangic.md)
