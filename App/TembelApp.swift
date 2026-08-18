import SwiftUI
import TembelCore

@main
struct TembelApp: App {
    @State private var alarms = AlarmListModel(store: TembelApp.makeStore())

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(alarms)
                .preferredColorScheme(.dark)
        }
    }

    /// Diske yazan store'u kurar.
    ///
    /// Application Support klasörü açılamazsa uygulamayı çökertmek yerine
    /// bellek içi store'a düşülür: kullanıcı en azından uygulamayı kullanabilir
    /// ve hata mesajını görebilir.
    private static func makeStore() -> any AlarmPersisting {
        do {
            return try JSONFileAlarmStore.defaultStore()
        } catch {
            return InMemoryAlarmStore()
        }
    }
}
