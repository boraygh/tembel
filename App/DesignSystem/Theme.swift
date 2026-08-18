import SwiftUI

/// Uygulamanın görsel dili.
///
/// Tüm renk, boşluk ve köşe yarıçapı değerleri buradan gelir. View'ların içine
/// doğrudan sayı veya renk yazılmaz — böylece Phase 12'deki UI cilası tek
/// dosyadan yapılabilir.
enum Theme {

    enum Palette {
        /// Ana zemin — neredeyse siyah, hafif mavi tonda.
        static let background = Color(red: 0.043, green: 0.043, blue: 0.059)
        /// Kart zemini.
        static let surface = Color(red: 0.086, green: 0.086, blue: 0.110)
        /// Yükseltilmiş yüzey (seçili kart, input alanı).
        static let surfaceElevated = Color(red: 0.129, green: 0.129, blue: 0.161)
        /// Vurgu rengi — uyandırıcı, agresif turuncu-kırmızı.
        static let accent = Color(red: 1.0, green: 0.302, blue: 0.180)

        static let textPrimary = Color.white
        static let textSecondary = Color.white.opacity(0.56)
        static let textTertiary = Color.white.opacity(0.32)
        static let separator = Color.white.opacity(0.08)
    }

    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
    }

    enum Radius {
        static let card: CGFloat = 20
        static let control: CGFloat = 14
    }
}
