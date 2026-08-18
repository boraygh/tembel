import Foundation

/// Planlanmış tek bir alarm çalışı.
///
/// Bir alarm, tek bir çalış değil bir **zincir** üretir: ana alarm ve onu takip
/// eden birkaç alarm. Kullanıcı görevleri tamamlamadan sesi susturursa takip
/// alarmları gelmeye devam eder; görevler tamamlandığında kalan zincir iptal
/// edilir.
///
/// Bu tasarımın nedeni iOS'un temel bir kısıtıdır: uygulama, kullanıcının alarm
/// sesini durdurmasını **engelleyemez** (Stop butonu ve fiziksel butonlar sistem
/// garantisidir). Engelleyemediğimiz için geri gelmeyi garanti ediyoruz.
/// Ayrıntı: `docs/ios-alarm-constraints.md` § 2.
public struct ScheduledFire: Equatable, Sendable, Identifiable, Hashable {

    public let alarmID: UUID
    /// 0 = ana alarm, 1 ve sonrası = takip alarmları.
    public let sequence: Int
    public let date: Date

    public init(alarmID: UUID, sequence: Int, date: Date) {
        self.alarmID = alarmID
        self.sequence = sequence
        self.date = date
    }

    public var isFollowUp: Bool { sequence > 0 }

    /// Sistemde bu çalışı tanımlayan kimlik.
    ///
    /// Alarm kimliği ile sıra numarasından türetilir; aynı alarm için her zaman
    /// aynı değerleri üretir. Görevler tamamlandığında kalan zinciri iptal
    /// edebilmek bu kararlılığa dayanır.
    public var id: String { "\(alarmID.uuidString)#\(sequence)" }

    /// `id`'den alarm kimliğini geri çözer.
    ///
    /// Sistem tarafından gelen bir kimliğin hangi alarma ait olduğunu bulmak
    /// için kullanılır.
    public static func alarmID(fromFireID fireID: String) -> UUID? {
        guard let separatorIndex = fireID.firstIndex(of: "#") else { return nil }
        return UUID(uuidString: String(fireID[fireID.startIndex..<separatorIndex]))
    }
}

/// Ana alarmdan sonra kaç saniye aralıkla takip alarmı kurulacağı.
public struct FollowUpPolicy: Equatable, Sendable {

    /// Ana alarmdan itibaren gecikmeler (saniye).
    public let delays: [TimeInterval]

    public init(delays: [TimeInterval]) {
        self.delays = delays.filter { $0 > 0 }.sorted()
    }

    /// Varsayılan zincir: 1, 3, 6 ve 10 dakika sonra.
    ///
    /// Aralıklar kasıtlı olarak artan: ilk takip hemen gelir (kullanıcı daha
    /// uyanıkken), sonrakiler seyrelir. Zincir sınırlıdır çünkü AlarmKit'in
    /// planlanabilir alarm sayısında bir üst sınırı var (`maximumLimitReached`)
    /// ve bunu tek bir alarmla tüketmek diğer alarmları riske atar.
    public static let standard = FollowUpPolicy(delays: [60, 180, 360, 600])

    /// Takip alarmı kurmaz — görevsiz alarmlar için.
    public static let none = FollowUpPolicy(delays: [])

    /// Ana alarm dahil toplam kaç alarm planlanacağı.
    public var totalFireCount: Int { delays.count + 1 }
}

public enum AlarmScheduler {

    /// Alarmın verilen andan sonraki ilk çalma zamanı.
    ///
    /// Alarmın açık olup olmadığına **bakmaz** — saf zaman hesabıdır.
    /// Kapalı alarmları elemek `firePlan` işidir.
    ///
    /// Yaz saati geçişleri `Calendar.nextDate(after:matching:matchingPolicy:)`
    /// tarafından ele alınır: ileri alınan saatte var olmayan bir zaman
    /// istendiğinde bir sonraki geçerli zamana kayar.
    public static func nextOccurrence(
        of alarm: Alarm,
        after reference: Date,
        calendar: Calendar = .current
    ) -> Date? {
        let hour = alarm.time.hour
        let minute = alarm.time.minute

        if alarm.repeatDays.isEmpty {
            return calendar.nextDate(
                after: reference,
                matching: DateComponents(hour: hour, minute: minute),
                matchingPolicy: .nextTime
            )
        }

        return alarm.repeatDays.compactMap { day in
            calendar.nextDate(
                after: reference,
                matching: DateComponents(hour: hour, minute: minute, weekday: day.rawValue),
                matchingPolicy: .nextTime
            )
        }.min()
    }

    /// Bir alarmın bir sonraki çalışı için kurulacak alarm zinciri.
    ///
    /// Kapalı alarm boş dizi döndürür. Görevi olmayan alarmda takip zinciri
    /// kurulmaz — susturmayı zorlaştırmanın bir anlamı yoktur.
    public static func firePlan(
        for alarm: Alarm,
        after reference: Date,
        policy: FollowUpPolicy = .standard,
        calendar: Calendar = .current
    ) -> [ScheduledFire] {
        guard alarm.isEnabled else { return [] }
        guard let firstDate = nextOccurrence(of: alarm, after: reference, calendar: calendar) else {
            return []
        }
        let effectivePolicy = alarm.requiresTasks ? policy : .none
        return firePlan(alarmID: alarm.id, firstFireAt: firstDate, policy: effectivePolicy)
    }

    /// Verilen anı ana alarm kabul ederek zinciri kurar.
    ///
    /// Test alarmı ve erteleme de bunu kullanır — ikisi de "şu andan itibaren
    /// şu kadar sonra çal" demektir.
    public static func firePlan(
        alarmID: UUID,
        firstFireAt: Date,
        policy: FollowUpPolicy = .standard
    ) -> [ScheduledFire] {
        let main = ScheduledFire(alarmID: alarmID, sequence: 0, date: firstFireAt)
        let followUps = policy.delays.enumerated().map { offset, delay in
            ScheduledFire(
                alarmID: alarmID,
                sequence: offset + 1,
                date: firstFireAt.addingTimeInterval(delay)
            )
        }
        return [main] + followUps
    }

    /// Birden fazla alarmın planlarını birleştirir, zamana göre sıralar.
    public static func firePlan(
        for alarms: [Alarm],
        after reference: Date,
        policy: FollowUpPolicy = .standard,
        calendar: Calendar = .current
    ) -> [ScheduledFire] {
        alarms
            .flatMap { firePlan(for: $0, after: reference, policy: policy, calendar: calendar) }
            .sorted { lhs, rhs in
                lhs.date == rhs.date ? lhs.id < rhs.id : lhs.date < rhs.date
            }
    }

    /// Listedeki alarmlar arasından en yakın çalacak olanı bulur.
    ///
    /// Ana sayfadaki "sonraki alarm ... sonra" satırı bunu kullanır.
    /// Kapalı alarmlar dikkate alınmaz.
    public static func nextAlarm(
        among alarms: [Alarm],
        after reference: Date,
        calendar: Calendar = .current
    ) -> (alarm: Alarm, date: Date)? {
        alarms
            .filter(\.isEnabled)
            .compactMap { alarm in
                nextOccurrence(of: alarm, after: reference, calendar: calendar)
                    .map { (alarm: alarm, date: $0) }
            }
            .min { lhs, rhs in
                lhs.date == rhs.date
                    ? lhs.alarm.id.uuidString < rhs.alarm.id.uuidString
                    : lhs.date < rhs.date
            }
    }
}
