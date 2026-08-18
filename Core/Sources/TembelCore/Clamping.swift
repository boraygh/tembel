/// Değeri verilen aralığa sıkıştırır.
///
/// Diskteki JSON kullanıcı tarafından düzenlenebilir veya eski bir sürümden
/// kalmış olabilir. Bozuk bir değerin uygulamayı çökertmesi yerine makul bir
/// sınıra çekilmesi tercih edilir — alarm uygulamasında çökme, kaçırılmış
/// alarm demektir.
extension Comparable {
    func clamped(to range: ClosedRange<Self>) -> Self {
        min(max(self, range.lowerBound), range.upperBound)
    }
}
