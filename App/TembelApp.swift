import SwiftUI
import TembelCore

@main
struct TembelApp: App {

    @State private var alarms = AlarmListModel(store: TembelApp.makeAlarmStore())
    @State private var session = AlarmSessionModel(store: TembelApp.makeSessionStore())

    /// Gerçek sensör. Demo Mode kendi sahte kaynağını kullanır.
    private let motionService: any MotionServicing = CoreMotionService()

    var body: some Scene {
        WindowGroup {
            RootView(motionService: motionService)
                .environment(alarms)
                .environment(session)
                .preferredColorScheme(.dark)
        }
    }

    /// Alarm listesini saklayan store.
    ///
    /// Application Support klasörü açılamazsa uygulamayı çökertmek yerine
    /// bellek içi store'a düşülür: kullanıcı en azından uygulamayı kullanabilir
    /// ve hata mesajını görebilir.
    private static func makeAlarmStore() -> any AlarmPersisting {
        (try? JSONFileAlarmStore.defaultStore()) ?? InMemoryAlarmStore()
    }

    private static func makeSessionStore() -> any AlarmSessionPersisting {
        (try? JSONFileAlarmSessionStore.defaultStore()) ?? InMemoryAlarmSessionStore()
    }
}
