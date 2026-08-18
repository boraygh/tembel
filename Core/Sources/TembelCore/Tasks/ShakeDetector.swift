import Foundation

/// Tek bir ivmeölçer okuması.
///
/// Değerler CoreMotion'ın `userAcceleration` alanından gelir — yerçekimi
/// çıkarılmış hâli, birim g. Cihaz sabitken büyüklük sıfıra yakındır.
public struct MotionSample: Equatable, Sendable {

    public let x: Double
    public let y: Double
    public let z: Double
    /// Cihaz açılışından beri geçen süre (saniye). Yalnızca örnekler arası
    /// fark anlamlıdır; mutlak değeri bir tarih değildir.
    public let timestamp: TimeInterval

    public init(x: Double, y: Double, z: Double, timestamp: TimeInterval) {
        self.x = x
        self.y = y
        self.z = z
        self.timestamp = timestamp
    }

    public var magnitude: Double {
        (x * x + y * y + z * z).squareRoot()
    }
}

public struct ShakeDetectorConfiguration: Equatable, Sendable {

    /// Bu büyüklüğün üzerine çıkmak bir sallama sayılır.
    public let triggerThreshold: Double
    /// Yeni bir sallama sayılabilmesi için önce bu değerin altına inilmelidir.
    /// Tek bir sert hareketin defalarca sayılmasını engeller (histerezis).
    public let releaseThreshold: Double
    /// İki sallama arasında geçmesi gereken en kısa süre. Titreşimin sayıya
    /// dönüşmesini engeller.
    public let minimumInterval: TimeInterval

    public init(triggerThreshold: Double, releaseThreshold: Double, minimumInterval: TimeInterval) {
        self.triggerThreshold = triggerThreshold
        // Bırakma eşiği tetikleme eşiğinin üstünde olamaz; olursa histerezis
        // anlamını yitirir ve her örnek sayılmaya başlar.
        self.releaseThreshold = Swift.min(releaseThreshold, triggerThreshold)
        self.minimumInterval = Swift.max(0, minimumInterval)
    }

    /// Başlangıç değerleri.
    ///
    /// ⚠️ Bu sayılar gerçek cihazda ayarlanmalıdır. Simulator'da ivmeölçer
    /// yoktur, bu yüzden burada doğrulanamazlar — yalnızca algoritmanın
    /// kendisi doğrulanabilir. Bkz. `docs/ios-alarm-constraints.md` § 8.
    public static let `default` = ShakeDetectorConfiguration(
        triggerThreshold: 1.8,
        releaseThreshold: 0.8,
        minimumInterval: 0.18
    )
}

/// İvmeölçer örneklerini sallama sayısına çeviren durum makinesi.
///
/// CoreMotion'a hiç bağlı değildir; örnekleri dışarıdan alır. Bu sayede
/// algoritma gerçek cihaz olmadan test edilebilir ve Demo Mode'da sahte
/// verilerle beslenebilir.
public struct ShakeDetector: Sendable {

    public let target: Int
    public let configuration: ShakeDetectorConfiguration

    public private(set) var count: Int = 0

    /// Bir sonraki eşik aşımının sayılabilir olup olmadığı.
    /// Cihaz zaten sallanıyorken başlanabilsin diye açık başlar.
    private var isArmed = true
    private var lastCountedAt: TimeInterval?
    private var lastSampleAt: TimeInterval?

    public init(target: Int, configuration: ShakeDetectorConfiguration = .default) {
        self.target = Swift.max(0, target)
        self.configuration = configuration
    }

    public var isComplete: Bool { count >= target }

    /// 0…1 arası tamamlanma oranı — ilerleme çubuğu için.
    public var progress: Double {
        guard target > 0 else { return 1 }
        return Swift.min(1, Double(count) / Double(target))
    }

    public var remaining: Int { Swift.max(0, target - count) }

    /// Bir örneği işler. Bu örnek yeni bir sallama saydırdıysa `true` döner.
    @discardableResult
    public mutating func process(_ sample: MotionSample) -> Bool {
        // Zaman geriye giderse örnek güvenilmezdir; yok say.
        if let lastSampleAt, sample.timestamp < lastSampleAt {
            return false
        }
        lastSampleAt = sample.timestamp

        let magnitude = sample.magnitude

        if magnitude < configuration.releaseThreshold {
            isArmed = true
            return false
        }

        guard isArmed, magnitude >= configuration.triggerThreshold else {
            return false
        }

        if let lastCountedAt,
           sample.timestamp - lastCountedAt < configuration.minimumInterval {
            // Çok erken geldi — sayma, ama kurulumu da bozma ki hareket
            // yavaşladığında yeniden sayılabilsin.
            return false
        }

        count += 1
        isArmed = false
        lastCountedAt = sample.timestamp
        return true
    }

    /// Bir dizi örneği sırayla işler, sayılan sallama adedini döndürür.
    @discardableResult
    public mutating func process<S: Sequence<MotionSample>>(contentsOf samples: S) -> Int {
        samples.reduce(into: 0) { total, sample in
            if process(sample) { total += 1 }
        }
    }

    /// Sayacı ve durumu başa alır. Görev yeniden başlatıldığında kullanılır.
    public mutating func reset() {
        count = 0
        isArmed = true
        lastCountedAt = nil
        lastSampleAt = nil
    }
}
