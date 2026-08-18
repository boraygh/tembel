import SwiftUI

/// Uygulamanın görsel dili.
///
/// Tüm renk, tipografi, boşluk ve köşe yarıçapı değerleri buradan gelir.
/// View'ların içine doğrudan sayı veya renk yazılmaz.
enum Theme {

    enum Palette {
        /// Ana zemin — neredeyse siyah, hafif mavi tonda.
        static let background = Color(red: 0.043, green: 0.043, blue: 0.059)
        /// Kart zemini.
        static let surface = Color(red: 0.086, green: 0.086, blue: 0.110)
        /// Yükseltilmiş yüzey (ikon kutusu, seçili kart).
        static let surfaceElevated = Color(red: 0.129, green: 0.129, blue: 0.161)
        /// Yaprak (sheet) zemini — ana zeminden bir ton açık, üst üste
        /// bindiklerinde ayrışsınlar diye.
        static let sheetBackground = Color(red: 0.075, green: 0.075, blue: 0.094)
        /// Vurgu rengi — uyandırıcı turuncu-kırmızı.
        static let accent = Color(red: 1.0, green: 0.302, blue: 0.180)

        static let textPrimary = Color.white
        static let textSecondary = Color.white.opacity(0.56)
        static let textTertiary = Color.white.opacity(0.32)
        static let textQuaternary = Color.white.opacity(0.16)
        static let separator = Color.white.opacity(0.08)
        static let fill = Color.white.opacity(0.06)

        /// Vurgu renginin şeffaf varyantları — dolgu ve kenarlık için.
        static let accentFill = accent.opacity(0.12)
        static let accentBorder = accent.opacity(0.28)
    }

    /// Tipografi.
    ///
    /// Archivo, uygulamanın varsayılan iOS görünümünden ayrışması için
    /// seçildi. Yazı tipi bir nedenle yüklenemezse `Font.custom` sessizce
    /// sistem yazı tipine düşer; düzen bozulmaz, yalnızca karakteri değişir.
    enum Typography {
        private enum Face {
            static let regular = "Archivo-Regular"
            static let medium = "Archivo-Medium"
            static let semiBold = "Archivo-SemiBold"
            static let bold = "Archivo-Bold"
            static let extraBold = "Archivo-ExtraBold"
        }

        /// Düzenleyicideki dev saat. Dinamik tip ile ölçeklenmez — bu boyutta
        /// ölçeklenme düzeni taşırır.
        static let hero = Font.custom(Face.extraBold, fixedSize: 88)
        /// Alarm kartındaki saat.
        static let cardTime = Font.custom(Face.extraBold, fixedSize: 40)
        /// Sayaç/adet göstergeleri.
        static let numeric = Font.custom(Face.extraBold, fixedSize: 44)

        static let largeTitle = Font.custom(Face.extraBold, size: 32, relativeTo: .largeTitle)
        static let title = Font.custom(Face.extraBold, size: 24, relativeTo: .title2)
        static let headline = Font.custom(Face.semiBold, size: 17, relativeTo: .headline)
        static let body = Font.custom(Face.medium, size: 16, relativeTo: .body)
        static let bodyEmphasized = Font.custom(Face.semiBold, size: 16, relativeTo: .body)
        static let callout = Font.custom(Face.semiBold, size: 15, relativeTo: .callout)
        static let subheadline = Font.custom(Face.medium, size: 15, relativeTo: .subheadline)
        static let footnote = Font.custom(Face.medium, size: 13, relativeTo: .footnote)
        static let footnoteEmphasized = Font.custom(Face.semiBold, size: 13, relativeTo: .footnote)
        /// Bölüm başlıkları — büyük harf ve geniş harf aralığıyla kullanılır.
        static let sectionLabel = Font.custom(Face.bold, size: 12, relativeTo: .caption)
        static let caption = Font.custom(Face.medium, size: 12, relativeTo: .caption)
        static let chip = Font.custom(Face.bold, size: 13, relativeTo: .footnote)
        static let chipSmall = Font.custom(Face.bold, size: 10, relativeTo: .caption2)
    }

    /// Harf aralığı. Büyük başlıklar sıkışır, küçük etiketler açılır.
    enum Tracking {
        static let hero: CGFloat = -4
        static let cardTime: CGFloat = -1.8
        static let largeTitle: CGFloat = -1
        static let title: CGFloat = -0.5
        static let sectionLabel: CGFloat = 1.4
        static let brand: CGFloat = 1.7
    }

    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
    }

    enum Radius {
        /// Liste kartları — geniş yarıçap yumuşak, "sert alarm" hissini
        /// dengeliyor.
        static let cardLarge: CGFloat = 24
        static let card: CGFloat = 20
        static let task: CGFloat = 18
        static let control: CGFloat = 16
        static let iconBox: CGFloat = 12
    }

    enum Size {
        static let iconBox: CGFloat = 40
        static let iconBoxLarge: CGFloat = 44
        static let dayChip: CGFloat = 44
        static let row: CGFloat = 56
        static let primaryButton: CGFloat = 54
        static let roundButton: CGFloat = 44
    }
}
