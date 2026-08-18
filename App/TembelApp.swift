import SwiftUI
import TembelCore

@main
struct TembelApp: App {

    @State private var alarms = AlarmListModel(store: TembelApp.makeAlarmStore())
    @State private var session = AlarmSessionModel(store: TembelApp.makeSessionStore())
    @State private var premium = PremiumModel()

    /// Gerçek sensör. Demo Mode kendi sahte kaynağını kullanır.
    private let motionService: any MotionServicing = CoreMotionService()

    var body: some Scene {
        WindowGroup {
            RootView(motionService: motionService)
                .environment(alarms)
                .environment(session)
                .environment(premium)
                .preferredColorScheme(.dark)
                .task {
                    // Ürünleri yükler, cihazdaki hakları okur ve dışarıdan
                    // gelen değişiklikleri (iade, aile paylaşımı) dinler.
                    await premium.start()
                }
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
