import Foundation
import Observation
import StoreKit
import TembelCore

/// Premium durumunu ve satın alma akışını yürütür.
///
/// Backend yok: Apple'ın imzaladığı işlemler cihazda doğrulanır. Kullanıcı
/// hesabı, sunucu, abonelik veritabanı gerekmez — StoreKit 2 `currentEntitlements`
/// üzerinden geçerli haklar zaten cihazda mevcuttur ve Apple ID'ye bağlıdır,
/// yani kullanıcının diğer cihazlarında da geçerlidir.
@MainActor
@Observable
final class PremiumModel {

    private(set) var status: EntitlementStatus = .free
    private(set) var offers: [PremiumOffer] = []
    private(set) var isLoadingOffers = false
    private(set) var purchasingProduct: PremiumProduct?

    var errorMessage: String?

    /// StoreKit ürünleri — satın alma için gerekli. Önizlemede boştur.
    private var storeProducts: [PremiumProduct: Product] = [:]
    private var updatesTask: Task<Void, Never>?

    init() {}

    /// Yetkilendirme kapısı. Ekranlar sınırları buradan sorar.
    var gate: FeatureGate {
        FeatureGate(status: status)
    }

    var isPremium: Bool { gate.isPremium }

    // MARK: - Yaşam döngüsü

    /// Uygulama açılışında çağrılır.
    func start() async {
        // Dinleyici önce başlar: satın alma dışarıda (Ayarlar, aile paylaşımı,
        // iade) değişirse de haberdar olalım.
        startListeningForTransactionUpdates()
        await refreshEntitlements()
        await loadOffers()
    }

    private func startListeningForTransactionUpdates() {
        guard updatesTask == nil else { return }
        updatesTask = Task { [weak self] in
            for await update in Transaction.updates {
                guard case .verified(let transaction) = update else { continue }
                await transaction.finish()
                await self?.refreshEntitlements()
            }
        }
    }

    // MARK: - Yetkilendirme

    /// Cihazdaki geçerli hakları okuyup durumu günceller.
    func refreshEntitlements() async {
        var resolved = EntitlementStatus.free

        for await result in Transaction.currentEntitlements {
            // Doğrulanmamış işlem yok sayılır — kurcalanmış olabilir.
            guard case .verified(let transaction) = result else { continue }
            guard PremiumProduct(rawValue: transaction.productID) != nil else { continue }
            // İade edilmiş veya iptal edilmiş işlem hak vermez.
            guard transaction.revocationDate == nil else { continue }

            if let expiration = transaction.expirationDate {
                guard expiration > Date() else { continue }
                resolved = Self.merging(resolved, subscriptionExpiring: expiration)
            } else {
                // Süresiz: ömür boyu satın alma. Her şeyin üstünde.
                resolved = .premium(expiresAt: nil)
            }
        }

        status = resolved
    }

    /// Birden fazla geçerli hak varsa en güçlüsünü seçer.
    ///
    /// Ömür boyu satın alma her aboneliği yener; iki abonelik varsa uzun olan
    /// kazanır. Kullanıcı hem aylık hem yıllık almışsa erken bitene göre
    /// kısıtlanmamalı.
    private static func merging(
        _ current: EntitlementStatus,
        subscriptionExpiring expiration: Date
    ) -> EntitlementStatus {
        switch current {
        case .free:
            .premium(expiresAt: expiration)
        case .premium(nil):
            current
        case .premium(let existing?):
            .premium(expiresAt: max(existing, expiration))
        }
    }

    // MARK: - Ürünler

    func loadOffers() async {
        isLoadingOffers = true
        defer { isLoadingOffers = false }

        do {
            let products = try await Product.products(
                for: PremiumProduct.allCases.map(\.rawValue)
            )

            var byProduct: [PremiumProduct: Product] = [:]
            for product in products {
                if let known = PremiumProduct(rawValue: product.id) {
                    byProduct[known] = product
                }
            }
            storeProducts = byProduct

            offers = PremiumProduct.displayOrder.compactMap { product in
                guard let storeProduct = byProduct[product] else { return nil }
                return PremiumOffer(
                    product: product,
                    displayPrice: storeProduct.displayPrice,
                    secondaryPrice: Self.secondaryPrice(for: product, storeProduct: storeProduct),
                    isRecommended: product == .yearly
                )
            }
            errorMessage = nil
        } catch {
            offers = []
            errorMessage = AppStrings.Premium.loadFailed
        }
    }

    /// Yıllık planda aylık karşılığını yazar — karşılaştırmayı kullanıcı
    /// yerine biz yapalım.
    private static func secondaryPrice(
        for product: PremiumProduct,
        storeProduct: Product
    ) -> String? {
        guard product == .yearly else { return nil }
        // Ürünün kendi biçimi kullanılıyor: para birimi ve yerel biçim
        // kullanıcının App Store bölgesinden gelir, elle kurulmaz.
        let monthly = storeProduct.price / 12
        return AppStrings.Premium.perMonth(monthly.formatted(storeProduct.priceFormatStyle))
    }

    // MARK: - Satın alma

    func purchase(_ product: PremiumProduct) async {
        guard let storeProduct = storeProducts[product] else {
            errorMessage = AppStrings.Premium.productUnavailable
            return
        }

        purchasingProduct = product
        defer { purchasingProduct = nil }

        do {
            switch try await storeProduct.purchase() {
            case .success(let verification):
                guard case .verified(let transaction) = verification else {
                    errorMessage = AppStrings.Premium.verificationFailed
                    return
                }
                await transaction.finish()
                await refreshEntitlements()
                errorMessage = nil

            case .userCancelled:
                // Vazgeçmek hata değildir; sessizce geç.
                break

            case .pending:
                // Aile onayı bekleyen satın alma. Onaylanınca
                // Transaction.updates üzerinden gelir.
                errorMessage = AppStrings.Premium.purchasePending

            @unknown default:
                errorMessage = AppStrings.Premium.purchaseFailed
            }
        } catch {
            errorMessage = AppStrings.Premium.purchaseFailed
        }
    }

    /// Satın alımları geri yükler.
    ///
    /// App Store kuralları bu düğmeyi zorunlu kılar: kullanıcı cihaz
    /// değiştirdiğinde ödediği şeye erişebilmeli.
    func restore() async {
        do {
            try await AppStore.sync()
            await refreshEntitlements()
            errorMessage = isPremium ? nil : AppStrings.Premium.nothingToRestore
        } catch {
            errorMessage = AppStrings.Premium.restoreFailed
        }
    }
}

extension PremiumModel {
    /// Önizlemeler için StoreKit'e dokunmayan model.
    ///
    /// Fiyatlar gerçekte StoreKit'ten gelir; burada yalnızca yerleşimin
    /// görülebilmesi için yer tutucu kullanılır.
    static func preview(isPremium: Bool = false) -> PremiumModel {
        let model = PremiumModel()
        model.applyPreviewState(isPremium: isPremium)
        return model
    }

    private func applyPreviewState(isPremium: Bool) {
        status = isPremium ? .premium(expiresAt: nil) : .free
        offers = PremiumProduct.displayOrder.map { product in
            PremiumOffer(
                product: product,
                displayPrice: "—",
                secondaryPrice: product == .yearly ? AppStrings.Premium.perMonth("—") : nil,
                isRecommended: product == .yearly
            )
        }
    }
}
