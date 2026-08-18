import Foundation

public enum MathOperation: String, Codable, CaseIterable, Sendable {
    case addition
    case subtraction
    case multiplication
    case division

    /// Ekranda gösterilen işaret. Matematik işaretleri dile bağlı olmadığı için
    /// çekirdekte tutulabilir.
    public var symbol: String {
        switch self {
        case .addition: "+"
        case .subtraction: "−"      // U+2212, tire değil
        case .multiplication: "×"
        case .division: "÷"
        }
    }
}

/// Tek bir matematik sorusu.
///
/// Soru ve cevabı birlikte taşır; cevap üretim anında hesaplanır, sonradan
/// tekrar çözülmez. Böylece "gösterilen soru ile beklenen cevap farklı olabilir"
/// sınıfı hatalar mümkün değildir.
public struct MathQuestion: Equatable, Sendable, Identifiable, Hashable {

    public let id: UUID
    public let left: Int
    public let right: Int
    public let operation: MathOperation
    public let answer: Int

    init(id: UUID = UUID(), left: Int, right: Int, operation: MathOperation) {
        self.id = id
        self.left = left
        self.right = right
        self.operation = operation
        self.answer = switch operation {
        case .addition: left + right
        case .subtraction: left - right
        case .multiplication: left * right
        case .division: left / right
        }
    }

    /// "47 + 28" — soru metni, cevap alanı hariç.
    public var promptText: String {
        "\(left) \(operation.symbol) \(right)"
    }

    /// Girilen metnin doğru cevap olup olmadığı.
    ///
    /// Baştaki/sondaki boşluklar yok sayılır. Boş girdi yanlış sayılır, hata
    /// değildir — kullanıcı yazmayı sürdürüyordur.
    public func isCorrect(_ input: String) -> Bool {
        Int(input.trimmed()) == answer
    }
}
