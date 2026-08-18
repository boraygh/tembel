import Foundation

/// App Store Connect'te tanımlanacak ürünler.
///
/// Kimlikler burada sabit; **fiyatlar burada yok.** Fiyatı App Store Connect
/// belirler, uygulama StoreKit'ten okuyup gösterir. Fiyatı koda yazmak, ülkeye
/// göre değişen ve senin sonradan değiştirebileceğin bir bilgiyi dondurmak
/// olurdu.
enum PremiumProduct: String, CaseIterable, Sendable, Identifiable {
    case monthly = "com.boray.tembel.premium.monthly"
    case yearly = "com.boray.tembel.premium.yearly"
    case lifetime = "com.boray.tembel.premium.lifetime"

    var id: String { rawValue }

    /// App Store Connect'te seçilecek ürün türü.
    var isSubscription: Bool {
        switch self {
        case .monthly, .yearly: true
        case .lifetime: false
        }
    }

    var title: String {
        switch self {
        case .monthly: "Aylık"
        case .yearly: "Yıllık"
        case .lifetime: "Ömür boyu"
        }
    }

    var subtitle: String {
        switch self {
        case .monthly: "her ay"
        case .yearly: "yılda bir"
        case .lifetime: "tek seferlik"
        }
    }

    /// Ekranda önerilen sırayla.
    static var displayOrder: [PremiumProduct] { [.monthly, .yearly, .lifetime] }
}

/// Ekranda gösterilen tek bir satın alma seçeneği.
///
/// `displayPrice` StoreKit'ten gelir — para birimi ve biçim kullanıcının
/// App Store bölgesine göre değişir, elle biçimlendirilmez.
struct PremiumOffer: Identifiable, Sendable {
    let product: PremiumProduct
    let displayPrice: String
    /// Yıllık planda "ayda X" gibi ek bilgi. Yoksa `nil`.
    let secondaryPrice: String?
    /// Öne çıkarılan plan mı.
    let isRecommended: Bool

    var id: String { product.rawValue }
}
