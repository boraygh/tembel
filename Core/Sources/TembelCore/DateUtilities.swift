import Foundation

extension Date {
    /// Saniye altı hassasiyeti atar.
    ///
    /// Modelin diske yazılıp geri okunduğunda kendisine eşit kalmasını
    /// garanti eder. ISO8601 gibi bazı kodlamalar milisaniyeyi taşımaz; bu
    /// farkın `==` karşılaştırmasını bozması, "alarm değişti mi?" gibi
    /// kontrollerde sessiz hatalara yol açar.
    func truncatedToSeconds() -> Date {
        Date(timeIntervalSince1970: timeIntervalSince1970.rounded(.down))
    }
}
