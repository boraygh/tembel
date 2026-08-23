import 'package:flutter_test/flutter_test.dart';
import 'package:tembel/core/models/alarm.dart';
import 'package:tembel/core/models/alarm_task.dart';
import 'package:tembel/core/models/clock_time.dart';
import 'package:tembel/core/models/weekday.dart';
import 'package:tembel/core/scheduling/alarm_scheduler.dart';

/// Testler yerel saat diliminden bağımsız olmalı: sabit tarih beklemek yerine
/// "hangi gün, hangi saat, referanstan sonra mı" gibi ilişkiler doğrulanıyor.
void main() {
  Alarm makeAlarm({
    int hour = 7,
    int minute = 30,
    Set<Weekday> days = const {},
    bool enabled = true,
    int taskCount = 1,
    String id = 'a1',
  }) => Alarm(
    id: id,
    time: ClockTime(hour, minute),
    repeatDays: days,
    isEnabled: enabled,
    tasks: List.generate(
      taskCount,
      (i) => AlarmTask(id: 't$i', configuration: const ShakeConfiguration(count: 10)),
    ),
    createdAt: DateTime(2026, 1, 1),
  );

  group('Sonraki çalma zamanı', () {
    test('tek seferlik alarm saati geçmediyse bugün çalar', () {
      final reference = DateTime(2026, 8, 17, 6); // Pazartesi 06:00
      final next = AlarmScheduler.nextOccurrence(makeAlarm(), reference);
      expect(next, DateTime(2026, 8, 17, 7, 30));
    });

    test('tek seferlik alarm saati geçtiyse ertesi güne kayar', () {
      final reference = DateTime(2026, 8, 17, 9);
      expect(
        AlarmScheduler.nextOccurrence(makeAlarm(), reference),
        DateTime(2026, 8, 18, 7, 30),
      );
    });

    test('tam alarm saatinde referans verilirse bir sonraki güne geçer', () {
      final reference = DateTime(2026, 8, 17, 7, 30);
      expect(
        AlarmScheduler.nextOccurrence(makeAlarm(), reference),
        DateTime(2026, 8, 18, 7, 30),
      );
    });

    test('tekrarlı alarm bugün de uygunsa bugünü seçer', () {
      final reference = DateTime(2026, 8, 17, 6);
      final alarm = makeAlarm(days: {Weekday.monday, Weekday.wednesday, Weekday.friday});
      expect(
        AlarmScheduler.nextOccurrence(alarm, reference),
        DateTime(2026, 8, 17, 7, 30),
      );
    });

    test('tekrarlı alarm bugünü kaçırdıysa listedeki bir sonraki güne gider', () {
      final reference = DateTime(2026, 8, 17, 9); // Pazartesi, 07:30 kaçtı
      final alarm = makeAlarm(days: {Weekday.monday, Weekday.wednesday, Weekday.friday});
      // Sıradaki Çarşamba.
      expect(
        AlarmScheduler.nextOccurrence(alarm, reference),
        DateTime(2026, 8, 19, 7, 30),
      );
    });

    test('haftanın tek günü seçiliyse bir hafta sonrasına sarar', () {
      final reference = DateTime(2026, 8, 17, 9);
      final alarm = makeAlarm(days: {Weekday.monday});
      expect(
        AlarmScheduler.nextOccurrence(alarm, reference),
        DateTime(2026, 8, 24, 7, 30),
      );
    });

    test('hafta sonu alarmı Cuma gününden Cumartesiye gider', () {
      final reference = DateTime(2026, 8, 21, 12); // Cuma
      final alarm = makeAlarm(hour: 9, minute: 0, days: Weekday.weekend);
      expect(AlarmScheduler.nextOccurrence(alarm, reference), DateTime(2026, 8, 22, 9));
    });

    test('sonuç her zaman referanstan sonradır ve doğru güne düşer', () {
      final reference = DateTime(2026, 8, 17, 9);
      for (final day in Weekday.values) {
        final next = AlarmScheduler.nextOccurrence(makeAlarm(days: {day}), reference);
        expect(next, isNotNull);
        expect(next!.isAfter(reference), isTrue);
        expect(Weekday.fromDateTime(next), day);
        expect(next.hour, 7);
        expect(next.minute, 30);
      }
    });

    test('kapalı alarmın da zamanı hesaplanabilir — süzme işi planlayıcının', () {
      final reference = DateTime(2026, 8, 17, 6);
      final alarm = makeAlarm(enabled: false);
      expect(AlarmScheduler.nextOccurrence(alarm, reference), isNotNull);
      expect(AlarmScheduler.firePlan(alarm, reference), isEmpty);
    });
  });

  group('Takip zinciri', () {
    test('görevli alarm ana alarm ve takip zinciri üretir', () {
      final reference = DateTime(2026, 8, 17, 6);
      final plan = AlarmScheduler.firePlan(makeAlarm(taskCount: 2), reference);
      final main = DateTime(2026, 8, 17, 7, 30);

      expect(plan.length, FollowUpPolicy.standard.totalFireCount);
      expect(plan.map((f) => f.sequence).toList(), [0, 1, 2, 3, 4]);
      expect(plan.map((f) => f.date).toList(), [
        main,
        main.add(const Duration(minutes: 1)),
        main.add(const Duration(minutes: 3)),
        main.add(const Duration(minutes: 6)),
        main.add(const Duration(minutes: 10)),
      ]);
      expect(plan.first.isFollowUp, isFalse);
      expect(plan.skip(1).every((f) => f.isFollowUp), isTrue);
    });

    test('görevsiz alarmda takip zinciri kurulmaz', () {
      final plan = AlarmScheduler.firePlan(
        makeAlarm(taskCount: 0),
        DateTime(2026, 8, 17, 6),
      );
      expect(plan.length, 1);
      expect(plan.first.isFollowUp, isFalse);
    });

    test('zincir kimlikleri benzersiz, kararlı ve geri çözülebilir', () {
      final start = DateTime(2026, 8, 17, 7, 30);
      final first = AlarmScheduler.chainFrom(alarmId: 'abc', firstFireAt: start);
      final second = AlarmScheduler.chainFrom(alarmId: 'abc', firstFireAt: start);

      expect(first, second);
      expect(first.map((f) => f.id).toSet().length, first.length);
      for (final fire in first) {
        expect(ScheduledFire.alarmIdFromFireId(fire.id), 'abc');
      }
      expect(ScheduledFire.alarmIdFromFireId('gecersiz'), isNull);
      // Platform tarafı sayısal kimlik istediğinde de çakışma olmamalı.
      expect(first.map((f) => f.numericId).toSet().length, first.length);
    });

    test('özel politika zincir uzunluğunu değiştirir', () {
      final start = DateTime(2026, 8, 17, 7, 30);
      final policy = FollowUpPolicy(const [Duration(seconds: 30), Duration(seconds: 90)]);
      final plan = AlarmScheduler.chainFrom(
        alarmId: 'x',
        firstFireAt: start,
        policy: policy,
      );

      expect(plan.length, 3);
      expect(plan.map((f) => f.date).toList(), [
        start,
        start.add(const Duration(seconds: 30)),
        start.add(const Duration(seconds: 90)),
      ]);
    });

    test('politika geçersiz gecikmeleri eler ve sıraya sokar', () {
      final policy = FollowUpPolicy(const [
        Duration(minutes: 5),
        Duration(seconds: -10),
        Duration.zero,
        Duration(minutes: 1),
      ]);
      expect(policy.delays, [const Duration(minutes: 1), const Duration(minutes: 5)]);
      expect(policy.totalFireCount, 3);
    });
  });

  group('Çoklu alarm', () {
    test('planlar zamana göre sıralanır', () {
      final reference = DateTime(2026, 8, 17, 5);
      final early = makeAlarm(id: 'early', hour: 6, minute: 0, taskCount: 0);
      final late = makeAlarm(id: 'late', hour: 8, minute: 0, taskCount: 0);

      final plan = AlarmScheduler.firePlanForAll([late, early], reference);
      expect(plan.length, 2);
      expect(plan.map((f) => f.alarmId).toList(), ['early', 'late']);
      expect(plan[0].date.isBefore(plan[1].date), isTrue);
    });

    test('sonraki alarm yalnızca açık alarmlar arasından seçilir', () {
      final reference = DateTime(2026, 8, 17, 5);
      final disabledEarly = makeAlarm(id: 'off', hour: 6, enabled: false);
      final enabledLate = makeAlarm(id: 'on', hour: 8);

      final result = AlarmScheduler.nextAlarm([disabledEarly, enabledLate], reference);
      expect(result?.alarm.id, 'on');
      expect(result?.date, DateTime(2026, 8, 17, 8, 30));
    });

    test('hiç açık alarm yoksa sonuç yok', () {
      final reference = DateTime(2026, 8, 17, 5);
      expect(AlarmScheduler.nextAlarm(const [], reference), isNull);
      expect(AlarmScheduler.nextAlarm([makeAlarm(enabled: false)], reference), isNull);
    });
  });
}
