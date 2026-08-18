import Foundation

extension String {
    /// Baştaki ve sondaki boşluk/satır sonlarını temizler.
    func trimmed() -> String {
        trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
