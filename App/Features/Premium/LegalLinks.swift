import Foundation

/// Ödeme duvarında gösterilmesi zorunlu bağlantılar.
///
/// App Store incelemesi abonelik satan bir ekranda kullanım koşulları ve
/// gizlilik politikası bağlantısı arar; eksikse uygulama reddedilir.
enum LegalLinks {

    /// Apple'ın standart lisans sözleşmesi.
    ///
    /// Kendi EULA'nı yazmadıysan geçerli ve kabul edilen adres budur.
    static let termsOfUse = URL(
        string: "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
    )

    /// ⚠️ **App Store'a göndermeden önce doldurulmalı.**
    ///
    /// Kendi gizlilik politikan bir yerde yayınlanmalı ve adresi buraya
    /// yazılmalı. Uydurma bir adres koymaktansa `nil` bırakıldı: böylece
    /// ekranda bozuk bir bağlantı görünmez, eksik olduğu belli olur.
    static let privacyPolicy: URL? = nil
}
