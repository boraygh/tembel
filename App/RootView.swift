import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            Tab(AppStrings.Tabs.alarms, systemImage: "alarm.fill") {
                HomeView()
            }
            Tab(AppStrings.Tabs.settings, systemImage: "gearshape.fill") {
                SettingsView()
            }
        }
        .tint(Theme.Palette.accent)
    }
}

#Preview {
    RootView()
        .environment(AlarmListModel.preview())
        .preferredColorScheme(.dark)
}
