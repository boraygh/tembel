import Foundation

/// Zorluk seviyesine göre matematik sorusu üretir.
///
/// Üretilen her soru şu güvenceleri taşır:
/// - Cevap her zaman sıfır veya pozitif tam sayıdır (çıkarmada negatif çıkmaz).
/// - Bölme her zaman tam bölünür, kalan olmaz.
/// - Hiçbir işlemde 0 veya 1 gibi soruyu anlamsızlaştıran çarpan kullanılmaz.
///
/// Rastgelelik dışarıdan verilebilir; testler ve Demo Mode tekrarlanabilir
/// sonuç almak için `SeededRandomNumberGenerator` kullanır.
public struct MathQuestionGenerator: Sendable {

    public let difficulty: MathDifficulty

    public init(difficulty: MathDifficulty) {
        self.difficulty = difficulty
    }

    /// Seviyede kullanılabilecek işlemler.
    public var operations: [MathOperation] {
        switch difficulty {
        case .easy: [.addition, .subtraction]
        case .medium: [.addition, .subtraction, .multiplication]
        case .hard: [.addition, .subtraction, .multiplication, .division]
        }
    }

    public func makeQuestion<G: RandomNumberGenerator>(using generator: inout G) -> MathQuestion {
        // `operations` hiçbir seviyede boş olamaz; yine de zorlamayla
        // çökmemek için toplama'ya düşülür.
        let operation = operations.randomElement(using: &generator) ?? .addition
        return makeQuestion(operation: operation, using: &generator)
    }

    public func makeQuestions<G: RandomNumberGenerator>(
        count: Int,
        using generator: inout G
    ) -> [MathQuestion] {
        let safeCount = max(0, count)
        return (0..<safeCount).map { _ in makeQuestion(using: &generator) }
    }

    /// Sistem rastgeleliğiyle üretir — uygulama içi normal kullanım.
    public func makeQuestions(count: Int) -> [MathQuestion] {
        var generator = SystemRandomNumberGenerator()
        return makeQuestions(count: count, using: &generator)
    }

    // MARK: - İşlem bazlı üretim

    private func makeQuestion<G: RandomNumberGenerator>(
        operation: MathOperation,
        using generator: inout G
    ) -> MathQuestion {
        switch operation {
        case .addition:
            let range = additionRange
            return MathQuestion(
                left: Int.random(in: range, using: &generator),
                right: Int.random(in: range, using: &generator),
                operation: .addition
            )

        case .subtraction:
            // Önce farkı ve çıkanı seçip toplamı hesaplıyoruz; böylece sonucun
            // negatif olması matematiksel olarak imkânsız.
            let difference = Int.random(in: subtractionResultRange, using: &generator)
            let subtrahend = Int.random(in: subtractionOperandRange, using: &generator)
            return MathQuestion(
                left: difference + subtrahend,
                right: subtrahend,
                operation: .subtraction
            )

        case .multiplication:
            let range = multiplicationRange
            return MathQuestion(
                left: Int.random(in: range, using: &generator),
                right: Int.random(in: range, using: &generator),
                operation: .multiplication
            )

        case .division:
            // Bölüneni çarpımdan türetiyoruz; kalan olması imkânsız.
            let divisor = Int.random(in: divisionDivisorRange, using: &generator)
            let quotient = Int.random(in: divisionQuotientRange, using: &generator)
            return MathQuestion(
                left: divisor * quotient,
                right: divisor,
                operation: .division
            )
        }
    }

    // MARK: - Seviye aralıkları

    private var additionRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 2...20
        case .medium: 12...89
        case .hard: 45...249
        }
    }

    private var subtractionResultRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 1...15
        case .medium: 6...60
        case .hard: 18...180
        }
    }

    private var subtractionOperandRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 2...9
        case .medium: 11...49
        case .hard: 24...199
        }
    }

    private var multiplicationRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 2...9
        case .medium: 3...12
        case .hard: 6...19
        }
    }

    private var divisionDivisorRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 2...5
        case .medium: 2...9
        case .hard: 3...12
        }
    }

    private var divisionQuotientRange: ClosedRange<Int> {
        switch difficulty {
        case .easy: 2...5
        case .medium: 2...9
        case .hard: 3...15
        }
    }
}
