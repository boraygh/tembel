import Foundation
import Testing

@testable import TembelCore

@Suite("Premium yetkilendirme")
struct EntitlementTests {

    private static let now = Date(timeIntervalSince1970: 1_800_000_000)

    private func gate(_ status: EntitlementStatus) -> FeatureGate {
        FeatureGate(status: status, referenceDate: Self.now)
    }

    // MARK: - Durum

    @Test("Ücretsiz kullanıcı premium değildir")
    func freeIsNotPremium() {
        #expect(gate(.free).isPremium == false)
    }

    @Test("Ömür boyu satın alma süresizdir")
    func lifetimeNeverExpires() {
        let status = EntitlementStatus.premium(expiresAt: nil)
        #expect(status.isLifetime)
        #expect(status.isActive(at: Self.now))
        #expect(status.isActive(at: Self.now.addingTimeInterval(100 * 365 * 86_400)))
    }

    @Test("Süresi dolmuş abonelik ücretsize düşer")
    func expiredSubscriptionFallsBackToFree() {
        let expired = EntitlementStatus.premium(
            expiresAt: Self.now.addingTimeInterval(-1)
        )
        #expect(expired.isActive(at: Self.now) == false)
        #expect(gate(expired).isPremium == false)
        #expect(expired.isLifetime == false)
    }

    @Test("Süresi dolmamış abonelik geçerlidir")
    func activeSubscription() {
        let active = EntitlementStatus.premium(
            expiresAt: Self.now.addingTimeInterval(86_400)
        )
        #expect(active.isActive(at: Self.now))
        #expect(gate(active).isPremium)
    }

    @Test("Yetkilendirme diske yazılıp geri okunabilir")
    func statusIsCodable() throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        for status: EntitlementStatus in [
            .free,
            .premium(expiresAt: nil),
            .premium(expiresAt: Self.now)
        ] {
            let decoded = try decoder.decode(
                EntitlementStatus.self,
                from: encoder.encode(status)
            )
            #expect(decoded == status)
        }
    }

    // MARK: - Alarm sayısı

    @Test("Ücretsiz kullanıcı sınırlı sayıda alarm kurabilir")
    func freeAlarmLimit() {
        let subject = gate(.free)
        #expect(subject.alarmLimit == FeatureGate.freeAlarmLimit)
        #expect(subject.canAddAlarm(currentCount: 0))
        #expect(subject.canAddAlarm(currentCount: FeatureGate.freeAlarmLimit - 1))
        #expect(subject.canAddAlarm(currentCount: FeatureGate.freeAlarmLimit) == false)
    }

    @Test("Premium kullanıcı sınırsız alarm kurabilir")
    func premiumAlarmLimit() {
        let subject = gate(.premium(expiresAt: nil))
        #expect(subject.canAddAlarm(currentCount: 0))
        #expect(subject.canAddAlarm(currentCount: 500))
    }

    // MARK: - Görev sayısı

    @Test("Ücretsizde alarm başına görev sayısı sınırlı")
    func freeTaskLimit() {
        let subject = gate(.free)
        #expect(subject.taskLimitPerAlarm == FeatureGate.freeTaskLimitPerAlarm)
        #expect(subject.canAddTask(currentCount: FeatureGate.freeTaskLimitPerAlarm) == false)
    }

    @Test("Premium görev sınırı modelin üst sınırını aşmaz")
    func premiumTaskLimitMatchesModel() {
        // Sınır, Alarm.normalized()'ın kırptığı değerle aynı olmalı; aksi hâlde
        // kullanıcıya ekleyebileceği söylenen görev sessizce silinir.
        #expect(gate(.premium(expiresAt: nil)).taskLimitPerAlarm == Alarm.maxTaskCount)
    }

    // MARK: - Görev türleri

    @Test("Fotoğraf görevi premium gerektirir")
    func photoTaskIsPremium() {
        let free = gate(.free)
        #expect(free.isAvailable(TaskKind.shake))
        #expect(free.isAvailable(TaskKind.math))
        #expect(free.isAvailable(TaskKind.photo) == false)
        #expect(free.availableTaskKinds == [.shake, .math])
    }

    @Test("Premium tüm görev türlerini açar")
    func premiumUnlocksAllTaskKinds() {
        let subject = gate(.premium(expiresAt: nil))
        #expect(Set(subject.availableTaskKinds) == Set(TaskKind.allCases))
    }

    @Test("Ücretsiz görev türleri uygulamanın vaadini karşılar")
    func freeTierIsUsable() {
        // Ücretsiz kullanıcı en az bir fiziksel ve bir zihinsel görev
        // kurabilmeli; yoksa uygulamanın ne yaptığı anlaşılmaz.
        #expect(FeatureGate.freeTaskKinds.contains(.shake))
        #expect(FeatureGate.freeTaskKinds.contains(.math))
    }

    // MARK: - Sesler

    @Test("Varsayılan ses herkese açıktır")
    func defaultSoundIsFree() {
        #expect(gate(.free).isAvailable(AlarmSound.systemDefault))
    }

    @Test("Özel sesler premium gerektirir")
    func customSoundsArePremium() {
        let free = gate(.free)
        #expect(free.isAvailable(AlarmSound.siren) == false)
        #expect(free.isAvailable(AlarmSound.aggressive) == false)

        let premium = gate(.premium(expiresAt: nil))
        #expect(premium.isAvailable(AlarmSound.siren))
    }

    @Test("Seçilebilir sesler cihaz doğrulamasıyla da sınırlıdır")
    func availableSoundsRespectDeviceVerification() {
        // AlarmSound.availableForSelection özel sesleri gerçek cihazda
        // doğrulanana kadar kapalı tutuyor; premium bunu delmemeli.
        let premium = gate(.premium(expiresAt: nil))
        let expected = AlarmSound.availableForSelection
        #expect(premium.availableSounds == expected)
        #expect(gate(.free).availableSounds == [.systemDefault])
    }

    // MARK: - Yetenekler

    @Test("Tüm premium yetenekler ücretsizde kapalı, premiumda açıktır")
    func featureAvailabilityFollowsStatus() {
        let free = gate(.free)
        let premium = gate(.premium(expiresAt: nil))

        for feature in PremiumFeature.allCases {
            #expect(free.isAvailable(feature) == false)
            #expect(premium.isAvailable(feature))
        }
    }

    @Test("Güvenilirlik özellikleri premium listesinde yer almaz")
    func reliabilityIsNeverPaywalled() {
        // Bu test bir sözleşmedir: alarmın çalması, takip zinciri ve
        // görevlerin zorunlu olması hiçbir zaman satılmaz.
        let names = Set(PremiumFeature.allCases.map(\.rawValue))
        #expect(names.contains("followUpChain") == false)
        #expect(names.contains("alarmReliability") == false)
        #expect(names.contains("taskEnforcement") == false)
    }
}
