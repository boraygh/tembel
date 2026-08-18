import SwiftUI
import TembelCore

/// Ayarlar sekmesi.
///
/// İzin durumu kontrolleri (AlarmKit, kamera, motion) AlarmKit bağlantısıyla
/// birlikte gelecek.
struct SettingsView: View {
    @Environment(AlarmSessionModel.self) private var session

    private var versionText: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "—"
        let build = info?["CFBundleVersion"] as? String ?? "—"
        return "\(version) (\(build))"
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Gradients.page.ignoresSafeArea()

                List {
                    #if DEBUG
                    demoSection
                    #endif
                    aboutSection
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle(AppStrings.Settings.title)
        }
    }

    private var aboutSection: some View {
        Section {
            LabeledContent(AppStrings.Settings.version, value: versionText)
                .font(Theme.Typography.body)
                .foregroundStyle(Theme.Palette.textPrimary)
                .listRowBackground(Theme.Palette.surface)
        } header: {
            sectionHeader(AppStrings.Settings.aboutSection)
        }
    }

    #if DEBUG
    /// Yalnızca geliştirme derlemelerinde görünür.
    ///
    /// Alarm beklemeden tüm görev akışını denemeyi sağlar. App Store
    /// derlemelerinde bulunmaz — inceleme sürecinde geliştirici arka kapısı
    /// olarak değerlendirilmemesi için.
    private var demoSection: some View {
        Section {
            Button(AppStrings.Demo.start) {
                session.startDemo(alarm: Self.demoAlarm)
            }
            .font(Theme.Typography.bodyEmphasized)
            .foregroundStyle(Theme.Palette.accent)
            .listRowBackground(Theme.Palette.surface)

            Text(AppStrings.Demo.help)
                .font(Theme.Typography.caption)
                .foregroundStyle(Theme.Palette.textTertiary)
                .listRowBackground(Theme.Palette.surface)
        } header: {
            sectionHeader(AppStrings.Demo.section)
        }
    }

    /// Üç görev türünü de içeren örnek alarm.
    private static var demoAlarm: Alarm {
        Alarm(
            title: AppStrings.Demo.title,
            time: TimeOfDay(hour: 7, minute: 30),
            tasks: [
                AlarmTask(configuration: .shake(count: 5)),
                AlarmTask(configuration: .math(difficulty: .easy, questionCount: 1)),
                AlarmTask(configuration: .photo(prompt: "Bir bardak su"))
            ],
            snooze: SnoozeSetting(isEnabled: true, durationMinutes: 1, maxCount: 1)
        )
    }
    #endif

    private func sectionHeader(_ text: String) -> some View {
        Text(text.uppercased())
            .font(Theme.Typography.sectionLabel)
            .tracking(Theme.Tracking.sectionLabel)
            .foregroundStyle(Theme.Palette.textTertiary)
    }
}

#Preview {
    SettingsView()
        .environment(AlarmSessionModel.preview())
        .preferredColorScheme(.dark)
}
