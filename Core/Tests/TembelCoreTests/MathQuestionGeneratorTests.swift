import Foundation
import Testing

@testable import TembelCore

@Suite("Matematik görevi")
struct MathQuestionGeneratorTests {

    /// Her seviyeden bol miktarda soru üretip özellikleri toplu doğrulamak
    /// için — tek örnek bakmak rastgele üretimde yeterli güvence vermez.
    private func sample(
        _ difficulty: MathDifficulty,
        count: Int = 400,
        seed: UInt64 = 20_260_818
    ) -> [MathQuestion] {
        var generator = SeededRandomNumberGenerator(seed: seed)
        return MathQuestionGenerator(difficulty: difficulty)
            .makeQuestions(count: count, using: &generator)
    }

    // MARK: - Değişmezler

    @Test("Cevap hiçbir zaman negatif olmaz", arguments: MathDifficulty.allCases)
    func answersAreNeverNegative(difficulty: MathDifficulty) {
        let negatives = sample(difficulty).filter { $0.answer < 0 }
        #expect(negatives.isEmpty)
    }

    @Test("Gösterilen soru ile cevap her zaman tutarlıdır", arguments: MathDifficulty.allCases)
    func answerMatchesOperation(difficulty: MathDifficulty) {
        let mismatched = sample(difficulty).filter { question in
            let expected = switch question.operation {
            case .addition: question.left + question.right
            case .subtraction: question.left - question.right
            case .multiplication: question.left * question.right
            case .division: question.left / question.right
            }
            return question.answer != expected
        }
        #expect(mismatched.isEmpty)
    }

    @Test("Bölme her zaman tam bölünür", arguments: MathDifficulty.allCases)
    func divisionIsAlwaysExact(difficulty: MathDifficulty) {
        let inexact = sample(difficulty).filter { question in
            question.operation == .division && question.left % question.right != 0
        }
        #expect(inexact.isEmpty)
    }

    @Test("Sıfıra bölme üretilemez", arguments: MathDifficulty.allCases)
    func neverDividesByZero(difficulty: MathDifficulty) {
        let byZero = sample(difficulty).filter { $0.operation == .division && $0.right == 0 }
        #expect(byZero.isEmpty)
    }

    @Test("Anlamsız çarpanlar üretilmez", arguments: MathDifficulty.allCases)
    func noTrivialOperands(difficulty: MathDifficulty) {
        // 0 veya 1 ile çarpma/bölme soruyu uyandırıcı olmaktan çıkarır.
        let trivial = sample(difficulty).filter { question in
            switch question.operation {
            case .multiplication, .division: question.left <= 1 || question.right <= 1
            case .addition, .subtraction: question.left <= 0 || question.right <= 0
            }
        }
        #expect(trivial.isEmpty)
    }

    @Test("Çıkarmada sonuç sıfır olmaz — bedava soru yok", arguments: MathDifficulty.allCases)
    func subtractionIsNeverZero(difficulty: MathDifficulty) {
        let zeros = sample(difficulty).filter { $0.operation == .subtraction && $0.answer == 0 }
        #expect(zeros.isEmpty)
    }

    // MARK: - Seviyeler

    @Test("Kolay seviyede yalnızca toplama ve çıkarma çıkar")
    func easyUsesOnlyAdditionAndSubtraction() {
        let operations = Set(sample(.easy).map(\.operation))
        #expect(operations.isSubset(of: [.addition, .subtraction]))
    }

    @Test("Orta seviyede bölme çıkmaz")
    func mediumHasNoDivision() {
        let operations = Set(sample(.medium).map(\.operation))
        #expect(operations.contains(.multiplication))
        #expect(operations.contains(.division) == false)
    }

    @Test("Zor seviyede dört işlem de çıkar")
    func hardUsesAllOperations() {
        let operations = Set(sample(.hard).map(\.operation))
        #expect(operations == Set(MathOperation.allCases))
    }

    @Test("Zorluk arttıkça sorular gerçekten zorlaşır")
    func harderDifficultyProducesLargerNumbers() {
        // Ortalama cevap büyüklüğü kaba ama anlamlı bir ölçü.
        func averageAnswer(_ difficulty: MathDifficulty) -> Double {
            let questions = sample(difficulty)
            return Double(questions.map(\.answer).reduce(0, +)) / Double(questions.count)
        }

        #expect(averageAnswer(.easy) < averageAnswer(.medium))
        #expect(averageAnswer(.medium) < averageAnswer(.hard))
    }

    // MARK: - Üretim davranışı

    @Test("Aynı tohum aynı soruları üretir")
    func generationIsReproducible() {
        var first = SeededRandomNumberGenerator(seed: 42)
        var second = SeededRandomNumberGenerator(seed: 42)
        let generator = MathQuestionGenerator(difficulty: .hard)

        let left = generator.makeQuestions(count: 20, using: &first)
        let right = generator.makeQuestions(count: 20, using: &second)

        #expect(left.map(\.promptText) == right.map(\.promptText))
        #expect(left.map(\.answer) == right.map(\.answer))
    }

    @Test("Farklı tohum farklı sorular üretir")
    func differentSeedsDiverge() {
        var first = SeededRandomNumberGenerator(seed: 1)
        var second = SeededRandomNumberGenerator(seed: 2)
        let generator = MathQuestionGenerator(difficulty: .medium)

        let left = generator.makeQuestions(count: 20, using: &first)
        let right = generator.makeQuestions(count: 20, using: &second)

        #expect(left.map(\.promptText) != right.map(\.promptText))
    }

    @Test("İstenen sayıda soru üretilir")
    func questionCountIsRespected() {
        var generator = SeededRandomNumberGenerator(seed: 7)
        let subject = MathQuestionGenerator(difficulty: .easy)

        #expect(subject.makeQuestions(count: 3, using: &generator).count == 3)
        #expect(subject.makeQuestions(count: 0, using: &generator).isEmpty)
        #expect(subject.makeQuestions(count: -5, using: &generator).isEmpty)
    }

    @Test("Her sorunun kimliği benzersizdir")
    func questionIdentifiersAreUnique() {
        let questions = sample(.medium, count: 200)
        #expect(Set(questions.map(\.id)).count == questions.count)
    }

    // MARK: - Cevap kontrolü

    @Test("Doğru cevap kabul edilir, boşluklar yok sayılır")
    func correctAnswerIsAccepted() {
        let question = MathQuestion(left: 47, right: 28, operation: .addition)
        #expect(question.answer == 75)
        #expect(question.isCorrect("75"))
        #expect(question.isCorrect("  75 "))
        #expect(question.isCorrect("\n75\n"))
    }

    @Test("Yanlış ve geçersiz girdiler reddedilir")
    func wrongAnswerIsRejected() {
        let question = MathQuestion(left: 47, right: 28, operation: .addition)
        #expect(question.isCorrect("74") == false)
        #expect(question.isCorrect("") == false)
        #expect(question.isCorrect("   ") == false)
        #expect(question.isCorrect("yetmişbeş") == false)
        #expect(question.isCorrect("75.0") == false)
        #expect(question.isCorrect("7 5") == false)
    }

    @Test("Soru metni okunabilir biçimdedir")
    func promptTextFormatting() {
        #expect(MathQuestion(left: 47, right: 28, operation: .addition).promptText == "47 + 28")
        #expect(MathQuestion(left: 12, right: 7, operation: .multiplication).promptText == "12 × 7")
        #expect(MathQuestion(left: 40, right: 8, operation: .division).promptText == "40 ÷ 8")
        // Kısa çizgi değil gerçek eksi işareti kullanılmalı.
        #expect(MathQuestion(left: 30, right: 8, operation: .subtraction).promptText == "30 − 8")
    }
}
