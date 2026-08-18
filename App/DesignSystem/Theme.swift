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
        /// Vurgunun açık ucu. Gradyanların üst tarafında ve ikonlarda kullanılır;
        /// tek renk yerine iki uç, yüzeye derinlik veriyor.
        static let accentBright = Color(red: 1.0, green: 0.451, blue: 0.329)

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

    /// Yüzey malzemeleri.
    ///
    /// Premium his düz dolgudan değil malzemeden gelir: yüzeyde hafif dikey
    /// gradyan, üst kenarda 1px ışık çizgisi, altta yumuşak gölge. Bu üçü
    /// birlikte kartı "ekrana yapışık" olmaktan çıkarıp üstünde duruyormuş
    /// gibi gösterir.
    enum Gradients {

        /// Sayfa zemini — yukarıdan aşağı koyulaşır.
        static let page = LinearGradient(
            stops: [
                .init(color: Color(red: 0.063, green: 0.063, blue: 0.090), location: 0),
                .init(color: Color(red: 0.039, green: 0.039, blue: 0.055), location: 0.45),
                .init(color: Color(red: 0.027, green: 0.027, blue: 0.039), location: 1)
            ],
            startPoint: .top,
            endPoint: .bottom
        )

        /// Kart yüzeyi.
        static let surface = LinearGradient(
            colors: [
                Color(red: 0.110, green: 0.110, blue: 0.141),
                Color(red: 0.078, green: 0.078, blue: 0.098)
            ],
            startPoint: .top,
            endPoint: .bottom
        )

        /// Üst kenardaki ışık çizgisi — aşağı doğru söner.
        static let edgeHighlight = LinearGradient(
            colors: [Color.white.opacity(0.08), Color.white.opacity(0.012)],
            startPoint: .top,
            endPoint: .bottom
        )

        /// Yaprak (sheet) zemini — ana zeminden bir ton açık başlar ki
        /// üst üste bindiklerinde ayrışsınlar.
        static let sheet = LinearGradient(
            colors: [
                Color(red: 0.082, green: 0.082, blue: 0.110),
                Color(red: 0.047, green: 0.047, blue: 0.067)
            ],
            startPoint: .top,
            endPoint: .bottom
        )

        /// Vurgu gradyanı — butonlar, seçili günler, açık anahtarlar.
        static let ember = LinearGradient(
            colors: [Palette.accentBright, Palette.accent],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        /// Vurgunun soluk dolgusu — ikincil butonlar ve rozetler.
        static let emberFaint = LinearGradient(
            colors: [Palette.accent.opacity(0.16), Palette.accent.opacity(0.05)],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    /// Gölgeler.
    enum Shadow {
        static let card = Color.black.opacity(0.36)
        /// Vurgu renkli butonun altındaki sıcak gölge — nötr gri gölge yerine
        /// butonun kendi rengi, ışık kaynağı hissi veriyor.
        static let ember = Palette.accent.opacity(0.34)
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
