/// Tohumlanabilir rastgele sayı üreteci.
///
/// İki yerde işe yarar: testlerde üretimin tekrarlanabilir olması, ve Demo
/// Mode'da her seferinde aynı soruların gelmesi.
///
/// Algoritma splitmix64 — kısa, hızlı ve dağılımı iyi. Kriptografik amaçla
/// kullanılmamalıdır; burada öyle bir ihtiyaç yok.
public struct SeededRandomNumberGenerator: RandomNumberGenerator, Sendable {

    private var state: UInt64

    public init(seed: UInt64) {
        // Tohum 0 verilirse splitmix64 sabit bir diziye düşmez ama yine de
        // belirgin bir başlangıç sabiti eklemek dağılımı iyileştirir.
        self.state = seed &+ 0x9E37_79B9_7F4A_7C15
    }

    public mutating func next() -> UInt64 {
        state = state &+ 0x9E37_79B9_7F4A_7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58_476D_1CE4_E5B9
        z = (z ^ (z >> 27)) &* 0x94D0_49BB_1331_11EB
        return z ^ (z >> 31)
    }
}
