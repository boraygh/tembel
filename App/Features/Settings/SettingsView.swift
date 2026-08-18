import SwiftUI

/// Ayarlar sekmesi.
///
/// Phase 1'de yalnızca sürüm bilgisi. İzin durumu kontrolleri (AlarmKit,
/// kamera, motion) ve Demo Mode Phase 13'te buraya eklenecek.
struct SettingsView: View {
    private var versionText: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "—"
        let build = info?["CFBundleVersion"] as? String ?? "—"
        return "\(version) (\(build))"
    }

    var body: some View {
        NavigationStack {
            List {
                Section("Hakkında") {
                    LabeledContent("Sürüm", value: versionText)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Theme.Palette.background)
            .navigationTitle("Ayarlar")
        }
    }
}

#Preview {
    SettingsView()
        .preferredColorScheme(.dark)
}
