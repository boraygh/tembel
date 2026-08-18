import Foundation
import Testing

@testable import TembelCore

@Suite("Sallama algılama")
struct ShakeDetectorTests {

    private static let rest = 0.2
    private static let peak = 2.5

    private func sample(_ magnitude: Double, at timestamp: TimeInterval) -> MotionSample {
        // Tek eksende hareket — büyüklük doğrudan bu değere eşit olur.
        MotionSample(x: magnitude, y: 0, z: 0, timestamp: timestamp)
    }

    /// `count` adet temiz sallama dalgası üretir: her döngü önce dinlenme,
    /// sonra tepe noktası. Tepeler 0.2 saniye arayla gelir — varsayılan
    /// 0.18 saniyelik bekleme süresinin üzerinde.
    private func shakeWave(count: Int, startAt: TimeInterval = 0) -> [MotionSample] {
        (0..<count).flatMap { index in
            let base = startAt + Double(index) * 0.2
            return [
                sample(Self.rest, at: base),
                sample(Self.peak, at: base + 0.1)
            ]
        }
    }

    // MARK: - Sayma

    @Test("Temiz dalgada tepe sayısı kadar sallama sayılır")
    func countsCleanShakes() {
        var detector = ShakeDetector(target: 10)
        detector.process(contentsOf: shakeWave(count: 10))
        #expect(detector.count == 10)
        #expect(detector.isComplete)
    }

    @Test("Sürekli yüksek ivme tek sallama sayılır")
    func sustainedMotionCountsOnce() {
        // Telefon havada tutulup sabit hızla sallanmadan yüksek ivmede
        // kalırsa sayaç dönmemeli — arada eşiğin altına inilmesi gerekir.
        var detector = ShakeDetector(target: 10)
        let sustained = (0..<40).map { sample(Self.peak, at: Double($0) * 0.05) }
        detector.process(contentsOf: sustained)
        #expect(detector.count == 1)
    }

    @Test("Çok hızlı tekrar eden tepeler titreşim sayılır, sayılmaz")
    func debouncesRapidPeaks() {
        var detector = ShakeDetector(target: 10)

        detector.process(sample(Self.rest, at: 0.02))
        let firstPeak = detector.process(sample(Self.peak, at: 0.10))

        detector.process(sample(Self.rest, at: 0.12))
        let tooSoon = detector.process(sample(Self.peak, at: 0.14))

        detector.process(sample(Self.rest, at: 0.30))
        let afterInterval = detector.process(sample(Self.peak, at: 0.35))

        #expect(firstPeak)
        #expect(tooSoon == false)
        #expect(afterInterval)
        #expect(detector.count == 2)
    }

    @Test("Eşiğin altındaki hareket hiç sayılmaz")
    func gentleMotionIsIgnored() {
        var detector = ShakeDetector(target: 5)
        let gentle = (0..<60).map { sample(1.2, at: Double($0) * 0.1) }
        detector.process(contentsOf: gentle)
        #expect(detector.count == 0)
        #expect(detector.isComplete == false)
    }

    @Test("Cihaz sabitken sayaç dönmez")
    func stillDeviceCountsNothing() {
        var detector = ShakeDetector(target: 5)
        let still = (0..<100).map { sample(0.03, at: Double($0) * 0.02) }
        detector.process(contentsOf: still)
        #expect(detector.count == 0)
    }

    @Test("Zaten sallanırken başlanırsa ilk tepe sayılır")
    func startsArmed() {
        var detector = ShakeDetector(target: 3)
        let counted = detector.process(sample(Self.peak, at: 0))
        #expect(counted)
        #expect(detector.count == 1)
    }

    // MARK: - İlerleme

    @Test("İlerleme hedefe göre hesaplanır")
    func progressTracking() {
        var detector = ShakeDetector(target: 4)
        #expect(detector.progress == 0)
        #expect(detector.remaining == 4)

        detector.process(contentsOf: shakeWave(count: 2))
        #expect(detector.count == 2)
        #expect(detector.progress == 0.5)
        #expect(detector.remaining == 2)
        #expect(detector.isComplete == false)
    }

    @Test("Hedef aşılsa bile ilerleme 1'i geçmez")
    func progressIsClamped() {
        var detector = ShakeDetector(target: 2)
        detector.process(contentsOf: shakeWave(count: 6))
        #expect(detector.count == 6)
        #expect(detector.progress == 1)
        #expect(detector.remaining == 0)
        #expect(detector.isComplete)
    }

    @Test("Hedef sıfırsa görev baştan tamamlanmış sayılır")
    func zeroTargetIsAlreadyComplete() {
        let detector = ShakeDetector(target: 0)
        #expect(detector.isComplete)
        #expect(detector.progress == 1)
    }

    @Test("Negatif hedef sıfıra çekilir")
    func negativeTargetIsClamped() {
        #expect(ShakeDetector(target: -5).target == 0)
    }

    @Test("Sıfırlama sayacı ve durumu başa alır")
    func resetClearsState() {
        var detector = ShakeDetector(target: 10)
        detector.process(contentsOf: shakeWave(count: 4))
        #expect(detector.count == 4)

        detector.reset()
        #expect(detector.count == 0)
        #expect(detector.isComplete == false)

        // Sıfırlama sonrası ilk tepe yine sayılabilmeli.
        let countedAfterReset = detector.process(sample(Self.peak, at: 99))
        #expect(countedAfterReset)
    }

    // MARK: - Dayanıklılık

    @Test("Zamanı geriye giden örnekler yok sayılır")
    func outOfOrderSamplesAreIgnored() {
        var detector = ShakeDetector(target: 10)
        detector.process(sample(Self.rest, at: 5.0))
        let forward = detector.process(sample(Self.peak, at: 5.1))
        // Geçmişten gelen bir örnek bekleme süresini atlatmamalı.
        let backward = detector.process(sample(Self.peak, at: 1.0))

        #expect(forward)
        #expect(backward == false)
        #expect(detector.count == 1)
    }

    @Test("Bırakma eşiği tetikleme eşiğini geçemez")
    func configurationKeepsHysteresisMeaningful() {
        let configuration = ShakeDetectorConfiguration(
            triggerThreshold: 1.5,
            releaseThreshold: 9.0,
            minimumInterval: -1
        )
        #expect(configuration.releaseThreshold == 1.5)
        #expect(configuration.minimumInterval == 0)
    }

    @Test("Büyüklük üç eksenin bileşkesidir")
    func magnitudeIsEuclidean() {
        let subject = MotionSample(x: 3, y: 4, z: 0, timestamp: 0)
        #expect(subject.magnitude == 5)

        let unit = MotionSample(x: 1, y: 2, z: 2, timestamp: 0)
        #expect(unit.magnitude == 3)
    }

    @Test("Toplu işleme sayılan sallama adedini döndürür")
    func batchProcessingReportsCount() {
        var detector = ShakeDetector(target: 10)
        let counted = detector.process(contentsOf: shakeWave(count: 3))
        #expect(counted == 3)
        #expect(detector.count == 3)
    }

    @Test("Özel yapılandırma ile eşikler değiştirilebilir")
    func customConfiguration() {
        // Daha düşük eşik — hafif hareketler de sayılır.
        let sensitive = ShakeDetectorConfiguration(
            triggerThreshold: 1.0,
            releaseThreshold: 0.5,
            minimumInterval: 0.1
        )
        var detector = ShakeDetector(target: 5, configuration: sensitive)
        let gentle = (0..<10).flatMap { index -> [MotionSample] in
            let base = Double(index) * 0.3
            return [sample(0.2, at: base), sample(1.2, at: base + 0.15)]
        }
        detector.process(contentsOf: gentle)
        #expect(detector.count == 10)
    }
}
