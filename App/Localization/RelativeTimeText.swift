import Foundation

/// "8 saat 42 dakika sonra" gibi metinleri üretir.
///
/// `RelativeDateTimeFormatter` yerine elle yazıldı çünkü o, tek birim
/// gösterip ("8 saat sonra") dakikayı yutuyor; alarm uygulamasında kullanıcının
/// asıl merak ettiği şey dakika.
enum RelativeTimeText {

    private enum Unit {
        static let minute: TimeInterval = 60
        static let hour: TimeInterval = 60 * 60
        static let day: TimeInterval = 24 * 60 * 60
    }

    /// Verilen ana kalan süreyi Türkçe olarak yazar.
    /// Geçmiş bir an verilirse `nil` döner.
    static func timeRemaining(until date: Date, from reference: Date = Date()) -> String? {
        let interval = date.timeIntervalSince(reference)
        guard interval > 0 else { return nil }

        if interval < Unit.minute {
            return "birazdan"
        }

        if interval < Unit.hour {
            let minutes = Int(interval / Unit.minute)
            return "\(minutes) dakika sonra"
        }

        if interval < Unit.day {
            let hours = Int(interval / Unit.hour)
            let minutes = Int((interval - Double(hours) * Unit.hour) / Unit.minute)
            return minutes == 0
                ? "\(hours) saat sonra"
                : "\(hours) saat \(minutes) dakika sonra"
        }

        let days = Int(interval / Unit.day)
        let hours = Int((interval - Double(days) * Unit.day) / Unit.hour)
        return hours == 0
            ? "\(days) gün sonra"
            : "\(days) gün \(hours) saat sonra"
    }
}
