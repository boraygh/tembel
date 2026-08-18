import SwiftUI

struct RootView: View {
    @Environment(AlarmSessionModel.self) private var session

    let motionService: any MotionServicing

    /// Demo Mode'da sahte sensör kullanılır — Simulator'da ivmeölçer yok.
    private let demoMotionService: any MotionServicing = PreviewMotionService()

    var body: some View {
        TabView {
            Tab(AppStrings.Tabs.alarms, systemImage: "alarm.fill") {
                HomeView()
            }
            Tab(AppStrings.Premium.tab, systemImage: "star.fill") {
                PremiumView()
            }
            Tab(AppStrings.Tabs.settings, systemImage: "gearshape.fill") {
                SettingsView()
            }
        }
        .tint(Theme.Palette.accent)
        .fullScreenCover(isPresented: isRingingBinding) {
            AlarmRingingView(
                motionService: session.isDemo ? demoMotionService : motionService
            )
        }
    }

    /// Alarm ekranı yalnızca oturum bittiğinde kapanır; kullanıcı kendi
    /// kapatamaz. Bu yüzden setter bilinçli olarak boş.
    private var isRingingBinding: Binding<Bool> {
        Binding(get: { session.isRinging }, set: { _ in })
    }
}

#Preview {
    RootView(motionService: PreviewMotionService())
        .environment(AlarmListModel.preview())
        .environment(AlarmSessionModel.preview())
        .environment(PremiumModel.preview())
        .preferredColorScheme(.dark)
}
