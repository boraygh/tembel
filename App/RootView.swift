import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            Tab("Alarmlar", systemImage: "alarm.fill") {
                HomeView()
            }
            Tab("Ayarlar", systemImage: "gearshape.fill") {
                SettingsView()
            }
        }
        .tint(Theme.Palette.accent)
    }
}

#Preview {
    RootView()
        .preferredColorScheme(.dark)
}
