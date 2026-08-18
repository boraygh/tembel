import SwiftUI
import TembelCore

/// Premium sekmesi.
///
/// Kullanıcı premium değilse ödeme duvarını, premiumsa üyelik durumunu
/// gösterir. Sekme her iki durumda da yerinde kalır — satın aldıktan sonra
/// kaybolan bir sekme kullanıcıyı şaşırtır ve aboneliğini yönetecek yeri
/// bulamamasına yol açar.
struct PremiumView: View {
    @Environment(PremiumModel.self) private var premium

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Gradients.page.ignoresSafeArea()

                if premium.isPremium {
                    PremiumActiveView()
                } else {
                    PaywallContentView()
                }
            }
            .navigationTitle(AppStrings.Premium.tab)
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

/// Üyelik aktifken görünen durum.
struct PremiumActiveView: View {
    @Environment(PremiumModel.self) private var premium
    @Environment(\.openURL) private var openURL

    var body: some View {
        ScrollView {
            VStack(spacing: Theme.Spacing.lg) {
                header
                unlockedList
                manageButton
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.lg)
        }
        .scrollBounceBehavior(.basedOnSize)
    }

    private var header: some View {
        VStack(spacing: Theme.Spacing.sm + 4) {
            ZStack {
                Circle()
                    .fill(Theme.Palette.accent.opacity(0.35))
                    .frame(width: 96, height: 96)
                    .blur(radius: 24)
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(Theme.Gradients.ember)
                    .frame(width: 72, height: 72)
                    .shadow(color: Theme.Shadow.ember, radius: 20, y: 10)
                    .overlay {
                        Image(systemName: "star.fill")
                            .font(.system(size: 32, weight: .semibold))
                            .foregroundStyle(Theme.Palette.background)
                    }
            }

            Text(AppStrings.Premium.activeTitle)
                .font(Theme.Typography.title)
                .tracking(Theme.Tracking.title)
                .foregroundStyle(Theme.Palette.textPrimary)

            Text(statusDescription)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)
                .multilineTextAlignment(.center)
        }
    }

    private var statusDescription: String {
        switch premium.status {
        case .premium(let expiresAt):
            guard let expiresAt else { return AppStrings.Premium.activeLifetime }
            return AppStrings.Premium.activeUntil(
                expiresAt.formatted(date: .abbreviated, time: .omitted)
            )
        case .free:
            return ""
        }
    }

    private var unlockedList: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm + 4) {
            SectionLabel(AppStrings.Premium.unlockedSection)

            VStack(spacing: 0) {
                ForEach(PremiumFeature.displayOrder) { feature in
                    HStack(spacing: Theme.Spacing.sm + 4) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 17))
                            .foregroundStyle(Theme.Palette.accent)
                        Text(feature.title)
                            .font(Theme.Typography.body)
                            .foregroundStyle(Theme.Palette.textPrimary)
                        Spacer(minLength: 0)
                    }
                    .padding(.vertical, Theme.Spacing.sm + 2)
                }
            }
        }
    }

    @ViewBuilder
    private var manageButton: some View {
        // Ömür boyu satın almanın yönetilecek bir aboneliği yok.
        if !premium.status.isLifetime,
           let url = URL(string: "https://apps.apple.com/account/subscriptions") {
            Button(AppStrings.Premium.manage) {
                openURL(url)
            }
            .font(Theme.Typography.callout)
            .foregroundStyle(Theme.Palette.textSecondary)
        }
    }
}

/// Bir sınıra takıldığında açılan ödeme duvarı.
struct PaywallSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(PremiumModel.self) private var premium

    let reason: String

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Gradients.sheet.ignoresSafeArea()
                PaywallContentView(reason: reason)
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(AppStrings.Editor.cancel) { dismiss() }
                        .foregroundStyle(Theme.Palette.textSecondary)
                }
            }
        }
        // Satın alma tamamlanır tamamlanmaz sayfayı kapat: kullanıcı yaptığı
        // işe geri dönsün, kapatma düğmesi aramasın.
        .onChange(of: premium.isPremium) { _, isPremium in
            if isPremium { dismiss() }
        }
    }
}

#Preview("Ödeme duvarı") {
    PremiumView()
        .environment(PremiumModel.preview(isPremium: false))
        .preferredColorScheme(.dark)
}

#Preview("Aktif üyelik") {
    PremiumView()
        .environment(PremiumModel.preview(isPremium: true))
        .preferredColorScheme(.dark)
}
