import Foundation

public extension Array<Alarm> {

    /// Ana sayfadaki gösterim sırası.
    ///
    /// Açık alarmlar önce gelir — kullanıcının sabah bakacağı şey onlardır.
    /// Her grup kendi içinde saate göre sıralanır. Aynı saatteki alarmlar
    /// oluşturulma zamanına, o da eşitse kimliğe göre ayrışır; böylece sıra
    /// her çağrıda aynı olur ve liste kendiliğinden yer değiştirmez.
    func sortedForDisplay() -> [Alarm] {
        sorted { lhs, rhs in
            if lhs.isEnabled != rhs.isEnabled {
                return lhs.isEnabled
            }
            if lhs.time != rhs.time {
                return lhs.time < rhs.time
            }
            if lhs.createdAt != rhs.createdAt {
                return lhs.createdAt < rhs.createdAt
            }
            return lhs.id.uuidString < rhs.id.uuidString
        }
    }
}
