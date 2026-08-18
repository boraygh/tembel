import SwiftUI
import TembelCore

/// Ödeme duvarının gövdesi.
///
/// Hem Premium sekmesinde hem de bir sınıra takıldığında açılan sayfada aynı
/// içerik kullanılır — kullanıcı aynı şeyi iki farklı biçimde görmesin.
struct PaywallContentView: View {
    @Environment(PremiumModel.self) private var premium

    /// Sınıra takılarak gelindiyse üstte gösterilecek başlık.
    var reason: String?

    @State private var selection: PremiumProduct = .yearly

    var body: some View {
        ScrollView {
            VStack(spacing: Theme.Spacing.lg) {
                hero
                featureList
                planPicker
                actions
                legal
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.top, Theme.Spacing.md)
            .padding(.bottom, Theme.Spacing.lg)
        }
        .scrollBounceBehavior(.basedOnSize)
    }

    // MARK: - Bölümler

    private var hero: some View {
        VStack(spacing: Theme.Spacing.sm + 4) {
            ZStack {
                Circle()
                    .fill(Theme.Palette.accent.opacity(0.35))
                    .frame(width: 88, height: 88)
                    .blur(radius: 22)
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Theme.Gradients.ember)
                    .frame(width: 64, height: 64)
                    .shadow(color: Theme.Shadow.ember, radius: 18, y: 9)
                    .overlay {
                        Image(systemName: "star.fill")
                            .font(.system(size: 28, weight: .semibold))
                            .foregroundStyle(Theme.Palette.background)
                    }
            }

            if let reason {
                Text(reason)
                    .font(Theme.Typography.title)
                    .tracking(Theme.Tracking.title)
                    .foregroundStyle(Theme.Palette.textPrimary)
                    .multilineTextAlignment(.center)
            } else {
                Text(AppStrings.Premium.title)
                    .font(Theme.Typography.title)
                    .tracking(Theme.Tracking.title)
                    .foregroundStyle(Theme.Palette.textPrimary)
            }

            Text(AppStrings.Premium.tagline)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(.bottom, Theme.Spacing.xs)
    }

    private var featureList: some View {
        VStack(spacing: 0) {
            ForEach(PremiumFeature.displayOrder) { feature in
                HStack(spacing: Theme.Spacing.sm + 6) {
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .fill(Theme.Palette.fill)
                        .frame(width: 32, height: 32)
                        .overlay {
                            Image(systemName: feature.symbolName)
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundStyle(Theme.Palette.accent)
                        }

                    VStack(alignment: .leading, spacing: 1) {
                        Text(feature.title)
                            .font(Theme.Typography.callout)
                            .foregroundStyle(Theme.Palette.textPrimary)
                        Text(feature.detail)
                            .font(Theme.Typography.footnote)
                            .foregroundStyle(Theme.Palette.textSecondary)
                    }

                    Spacer(minLength: 0)
                }
                .padding(.vertical, Theme.Spacing.sm + 3)
            }
        }
    }

    @ViewBuilder
    private var planPicker: some View {
        if premium.offers.isEmpty {
            // Ürünler yüklenemediyse boş kutular göstermek yerine durumu söyle.
            Text(premium.isLoadingOffers ? "…" : AppStrings.Premium.loadFailed)
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textTertiary)
                .frame(maxWidth: .infinity)
                .frame(height: 96)
        } else {
            HStack(spacing: Theme.Spacing.sm) {
                ForEach(premium.offers) { offer in
                    planCard(offer)
                }
            }
            .padding(.top, offersNeedBadgeSpacing ? Theme.Spacing.sm : 0)
        }
    }

    private var offersNeedBadgeSpacing: Bool {
        premium.offers.contains(where: \.isRecommended)
    }

    private func planCard(_ offer: PremiumOffer) -> some View {
        let isSelected = offer.product == selection

        return Button {
            selection = offer.product
        } label: {
            VStack(spacing: 5) {
                Text(offer.product.title)
                    .font(Theme.Typography.footnoteEmphasized)
                    .foregroundStyle(isSelected ? Theme.Palette.accent : Theme.Palette.textSecondary)
                Text(offer.displayPrice)
                    .font(Theme.Typography.bodyEmphasized)
                    .foregroundStyle(Theme.Palette.textPrimary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
                Text(offer.secondaryPrice ?? offer.product.subtitle)
                    .font(Theme.Typography.caption)
                    .foregroundStyle(Theme.Palette.textTertiary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, Theme.Spacing.md)
            .padding(.horizontal, Theme.Spacing.sm)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                    .fill(isSelected ? AnyShapeStyle(Theme.Gradients.emberFaint)
                                     : AnyShapeStyle(Theme.Gradients.surface))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                    .strokeBorder(
                        isSelected ? AnyShapeStyle(Theme.Palette.accent)
                                   : AnyShapeStyle(Theme.Gradients.edgeHighlight),
                        lineWidth: 1.5
                    )
            )
            .shadow(
                color: isSelected ? Theme.Shadow.ember : .clear,
                radius: 14,
                y: 6
            )
            .overlay(alignment: .top) {
                if offer.isRecommended {
                    Text(AppStrings.Premium.recommended)
                        .font(Theme.Typography.chipSmall)
                        .foregroundStyle(Theme.Palette.background)
                        .padding(.horizontal, 9)
                        .padding(.vertical, 3)
                        .background(Capsule().fill(Theme.Palette.accent))
                        .offset(y: -9)
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
    }

    private var actions: some View {
        VStack(spacing: Theme.Spacing.md) {
            PrimaryButton(
                title: AppStrings.Premium.subscribe,
                isEnabled: !premium.offers.isEmpty && premium.purchasingProduct == nil
            ) {
                Task { await premium.purchase(selection) }
            }
            .overlay {
                if premium.purchasingProduct != nil {
                    ProgressView()
                        .tint(Theme.Palette.background)
                }
            }

            if let message = premium.errorMessage {
                Text(message)
                    .font(Theme.Typography.footnote)
                    .foregroundStyle(Theme.Palette.accent)
                    .multilineTextAlignment(.center)
            }

            VStack(spacing: 6) {
                Text(AppStrings.Premium.cancelAnytime)
                    .font(Theme.Typography.caption)
                    .foregroundStyle(Theme.Palette.textTertiary)

                Button(AppStrings.Premium.restore) {
                    Task { await premium.restore() }
                }
                .font(Theme.Typography.footnoteEmphasized)
                .foregroundStyle(Theme.Palette.textSecondary)
            }
        }
    }

    private var legal: some View {
        HStack(spacing: Theme.Spacing.md) {
            if let terms = LegalLinks.termsOfUse {
                Link(AppStrings.Premium.terms, destination: terms)
            }
            if let privacy = LegalLinks.privacyPolicy {
                Link(AppStrings.Premium.privacy, destination: privacy)
            }
        }
        .font(Theme.Typography.caption)
        .foregroundStyle(Theme.Palette.textQuaternary)
        .padding(.top, Theme.Spacing.xs)
    }
}
