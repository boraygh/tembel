import CoreMotion
import Foundation
import TembelCore

/// Hareket verisi kaynağı.
///
/// Protokol arkasına alınmasının nedeni Simulator'da ivmeölçerin **hiç
/// olmaması**: sallama görevi orada test edilemez. `PreviewMotionService`
/// sahte veri üreterek akışın gerçek cihaz olmadan denenebilmesini sağlar.
@MainActor
protocol MotionServicing: AnyObject {
    /// Cihazda gerçek hareket verisi var mı.
    var isAvailable: Bool { get }
    /// Örnek akışı. Akış sonlandırıldığında sensör güncellemeleri durur.
    func samples() -> AsyncStream<MotionSample>
}

/// Gerçek cihazdaki CoreMotion bağlantısı.
///
/// ⚠️ Simulator'da veri üretmez ve gerçek iPhone'da doğrulanmadan güvenilir
/// sayılmamalıdır. Eşik değerleri `ShakeDetectorConfiguration` içinde;
/// bkz. `docs/ios-alarm-constraints.md` § 8.
@MainActor
final class CoreMotionService: MotionServicing {

    /// Saniyede 50 örnek — sallama tepelerini yakalamaya yeter, pil tüketimi
    /// makul kalır. Görev ekranı yalnızca ön planda açıkken çalışır.
    private static let updateInterval: TimeInterval = 1.0 / 50.0

    private let manager = CMMotionManager()

    var isAvailable: Bool {
        manager.isDeviceMotionAvailable
    }

    func samples() -> AsyncStream<MotionSample> {
        // `makeStream` kullanılıyor çünkü `AsyncStream { ... }` biçiminin
        // kapanışı içinde CMMotionManager'a dokunmak Swift 6 eşzamanlılık
        // kurallarıyla çakışıyor. Burada her şey MainActor üzerinde kalıyor.
        let (stream, continuation) = AsyncStream.makeStream(of: MotionSample.self)

        guard manager.isDeviceMotionAvailable else {
            // Sensör yoksa akış hemen kapanır; çağıran taraf bunu "veri yok"
            // olarak ele alır.
            continuation.finish()
            return stream
        }

        manager.deviceMotionUpdateInterval = Self.updateInterval
        manager.startDeviceMotionUpdates(to: .main) { motion, _ in
            guard let motion else { return }
            // userAcceleration yerçekimini içermez; cihaz sabitken sıfıra
            // yakındır. Ham accelerometer kullanılsaydı 1g'lik sabit bileşeni
            // ayıklamak gerekirdi.
            let acceleration = motion.userAcceleration
            continuation.yield(
                MotionSample(
                    x: acceleration.x,
                    y: acceleration.y,
                    z: acceleration.z,
                    timestamp: motion.timestamp
                )
            )
        }

        continuation.onTermination = { [weak self] _ in
            Task { @MainActor in
                self?.manager.stopDeviceMotionUpdates()
            }
        }

        return stream
    }
}

/// Simulator, önizleme ve Demo Mode için sahte hareket üreteci.
///
/// Düzenli aralıklarla tepe üreterek sallama görevinin kendiliğinden
/// ilerlemesini sağlar — akışın gerçek cihaz olmadan baştan sona
/// denenebilmesi için.
@MainActor
final class PreviewMotionService: MotionServicing {

    private let shakeInterval: TimeInterval
    private let peakMagnitude: Double

    init(shakeInterval: TimeInterval = 0.6, peakMagnitude: Double = 2.6) {
        self.shakeInterval = shakeInterval
        self.peakMagnitude = peakMagnitude
    }

    let isAvailable = true

    func samples() -> AsyncStream<MotionSample> {
        let (stream, continuation) = AsyncStream.makeStream(of: MotionSample.self)

        // Değerler önceden kopyalanıyor ki üretici görev `self`'i tutmasın.
        let interval = shakeInterval
        let magnitude = peakMagnitude
        let halfInterval = interval / 2

        let producer = Task {
            var elapsed: TimeInterval = 0
            while !Task.isCancelled {
                // Önce dinlenme, sonra tepe — gerçek bir sallama dalgasının
                // sadeleştirilmiş hâli.
                continuation.yield(MotionSample(x: 0.1, y: 0, z: 0, timestamp: elapsed))
                try? await Task.sleep(for: .seconds(halfInterval))
                elapsed += halfInterval

                continuation.yield(MotionSample(x: magnitude, y: 0, z: 0, timestamp: elapsed))
                try? await Task.sleep(for: .seconds(halfInterval))
                elapsed += halfInterval
            }
            continuation.finish()
        }

        continuation.onTermination = { _ in producer.cancel() }
        return stream
    }
}
