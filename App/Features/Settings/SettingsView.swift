import SwiftUI

/// Ayarlar sekmesi.
///
/// Phase 1'de yalnızca sürüm bilgisi. İzin durumu kontrolleri (AlarmKit,
/// kamera, motion) ve Demo Mode sonraki fazlarda buraya eklenecek.
struct SettingsView: View {
    private var versionText: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "—"
        let build = info?["CFBundleVersion"] as? String ?? "—"
        return "\(version) (\(build))"
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Palette.background.ignoresSafeArea()

                List {
                    Section {
                        LabeledContent(AppStrings.Settings.version, value: versionText)
                            .font(Theme.Typography.body)
                            .foregroundStyle(Theme.Palette.textPrimary)
                            .listRowBackground(Theme.Palette.surface)
                    } header: {
                        Text(AppStrings.Settings.aboutSection.uppercased())
                            .font(Theme.Typography.sectionLabel)
                            .tracking(Theme.Tracking.sectionLabel)
                            .foregroundStyle(Theme.Palette.textTertiary)
                    }
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle(AppStrings.Settings.title)
        }
    }
}

#Preview {
    SettingsView()
        .preferredColorScheme(.dark)
}
