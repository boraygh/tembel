import 'package:flutter_test/flutter_test.dart';
import 'package:tembel/core/models/alarm.dart';
import 'package:tembel/core/models/alarm_task.dart';
import 'package:tembel/core/models/clock_time.dart';
import 'package:tembel/core/models/snooze_setting.dart';
import 'package:tembel/core/models/weekday.dart';

void main() {
  group('ClockTime', () {
    test('saat ve dakika doğru ayrıştırılır', () {
      final time = ClockTime(7, 30);
      expect(time.hour, 7);
      expect(time.minute, 30);
      expect(time.minutesSinceMidnight, 450);
      expect(time.displayText, '07:30');
    });

    test('gün sınırını aşan değerler sarar', () {
      expect(ClockTime(25, 0), ClockTime(1, 0));
      expect(ClockTime(24, 0), ClockTime(0, 0));
      expect(ClockTime.fromMinutes(-30), ClockTime(23, 30));
      expect(ClockTime.fromMinutes(-1), ClockTime(23, 59));
    });

    test('geçersiz ClockTime üretilemez', () {
      for (var raw = -5000; raw <= 5000; raw += 137) {
        final time = ClockTime.fromMinutes(raw);
        expect(time.minutesSinceMidnight, inInclusiveRange(0, ClockTime.minutesPerDay - 1));
        expect(time.hour, inInclusiveRange(0, 23));
        expect(time.minute, inInclusiveRange(0, 59));
      }
    });

    test('dakika ekleme gece yarısını doğru geçer', () {
      final time = ClockTime(23, 50);
      expect(time.adding(20), ClockTime(0, 10));
      expect(time.adding(-20), ClockTime(23, 30));
    });

    test('sıralama saat sırasına göredir', () {
      expect(ClockTime(6, 0) < ClockTime(7, 30), isTrue);
      expect(ClockTime(7, 29) < ClockTime(7, 30), isTrue);
      expect(ClockTime(8, 0) > ClockTime(7, 30), isTrue);
    });

    test('JSON düz sayıdır ve bozuk değer güvenle çözülür', () {
      expect(ClockTime(7, 30).toJson(), 450);
      expect(ClockTime.fromJson(450), ClockTime(7, 30));
      final broken = ClockTime.fromJson(99999);
      expect(broken.minutesSinceMidnight, inInclusiveRange(0, 1439));
      expect(ClockTime.fromJson('bozuk'), ClockTime(0, 0));
    });
  });

  group('Weekday', () {
    test('değerler DateTime.weekday ile birebir eşleşir', () {
      // 2026-08-17 bir Pazartesidir.
      final monday = DateTime(2026, 8, 17);
      expect(Weekday.fromDateTime(monday), Weekday.monday);
      expect(Weekday.monday.value, monday.weekday);

      for (var offset = 0; offset < 7; offset++) {
        final day = DateTime(2026, 8, 17 + offset);
        expect(Weekday.fromDateTime(day).value, day.weekday);
      }
    });

    test('sıralama Pazartesi ile başlar', () {
      expect(Weekday.orderedMondayFirst.first, Weekday.monday);
      expect(Weekday.orderedMondayFirst.last, Weekday.sunday);
      expect(Weekday.monday.mondayFirstIndex, 0);
      expect(Weekday.sunday.mondayFirstIndex, 6);
    });

    test('hazır kümeler doğru içeriğe sahiptir', () {
      expect(Weekday.weekdays.length, 5);
      expect(Weekday.weekend, {Weekday.saturday, Weekday.sunday});
      expect(Weekday.everyday.length, 7);
      expect(Weekday.weekdays.intersection(Weekday.weekend), isEmpty);
      expect(Weekday.weekdays.union(Weekday.weekend), Weekday.everyday);
    });

    test('küme sıralaması kararlıdır', () {
      final ordered = {Weekday.sunday, Weekday.wednesday, Weekday.monday}.ordered;
      expect(ordered, [Weekday.monday, Weekday.wednesday, Weekday.sunday]);
    });
  });

  group('Alarm', () {
    Alarm makeAlarm({List<AlarmTask> tasks = const []}) => Alarm(
          id: 'a1',
          title: 'İşe Kalk',
          time: ClockTime(7, 30),
          repeatDays: Weekday.weekdays,
          tasks: tasks,
          createdAt: DateTime.utc(2026, 8, 17, 6),
        );

    test('varsayılanlar uygulamanın vaadiyle tutarlıdır', () {
      final alarm = Alarm(id: 'x', time: ClockTime(7, 0));
      expect(alarm.isEnabled, isTrue);
      expect(alarm.tasks, isEmpty);
      // Erteleme kapalı gelmeli — açık olması temel fikri zayıflatır.
      expect(alarm.snooze.isEnabled, isFalse);
    });

    test('türetilmiş bayraklar doğru hesaplanır', () {
      final oneShot = Alarm(id: 'x', time: ClockTime(7, 0));
      expect(oneShot.isRepeating, isFalse);
      expect(oneShot.requiresTasks, isFalse);

      final repeating = makeAlarm(
        tasks: [const AlarmTask(id: 't1', configuration: ShakeConfiguration(count: 10))],
      );
      expect(repeating.isRepeating, isTrue);
      expect(repeating.requiresTasks, isTrue);
    });

    test('tekrar günleri Pazartesi\'den başlayarak sıralanır', () {
      final alarm = Alarm(
        id: 'x',
        time: ClockTime(7, 0),
        repeatDays: {Weekday.sunday, Weekday.monday, Weekday.friday},
      );
      expect(alarm.orderedRepeatDays, [Weekday.monday, Weekday.friday, Weekday.sunday]);
    });

    test('görev sırası listedeki sıradır ve taşıma kimlikleri korur', () {
      const shake = AlarmTask(id: 't1', configuration: ShakeConfiguration(count: 10));
      const math = AlarmTask(
        id: 't2',
        configuration: MathConfiguration(difficulty: MathDifficulty.hard, questionCount: 3),
      );
      const photo = AlarmTask(id: 't3', configuration: PhotoConfiguration(prompt: 'Kupa'));

      final alarm = makeAlarm(tasks: const [shake, math, photo]);
      expect(alarm.tasks.map((t) => t.kind).toList(),
          [TaskKind.shake, TaskKind.math, TaskKind.photo]);

      // Sonuncuyu başa taşı.
      final toFront = alarm.movingTask(oldIndex: 2, newIndex: 0);
      expect(toFront.tasks.map((t) => t.id).toList(), ['t3', 't1', 't2']);

      // İlkini sona taşı (ReorderableListView semantiği: hedef = liste uzunluğu).
      final toBack = alarm.movingTask(oldIndex: 0, newIndex: 3);
      expect(toBack.tasks.map((t) => t.id).toList(), ['t2', 't3', 't1']);

      // Sınır dışı indeks çökmemeli.
      final outOfBounds = alarm.movingTask(oldIndex: 99, newIndex: 0);
      expect(outOfBounds.tasks.map((t) => t.id).toList(), ['t1', 't2', 't3']);
    });

    test('normalized() sınır dışı değerleri düzeltir', () {
      final alarm = Alarm(
        id: 'x',
        title: '   ${'y' * 100}   ',
        time: ClockTime(7, 0),
        tasks: const [
          AlarmTask(id: '1', configuration: ShakeConfiguration(count: 9999)),
          AlarmTask(
            id: '2',
            configuration:
                MathConfiguration(difficulty: MathDifficulty.easy, questionCount: 0),
          ),
          AlarmTask(id: '3', configuration: PhotoConfiguration(prompt: '  kupa  ')),
          AlarmTask(id: '4', configuration: ShakeConfiguration(count: 1)),
          AlarmTask(id: '5', configuration: ShakeConfiguration(count: 5)),
          AlarmTask(id: '6', configuration: ShakeConfiguration(count: 6)),
        ],
        snooze: const SnoozeSetting(isEnabled: true, durationMinutes: 999, maxCount: 99),
      ).normalized();

      expect(alarm.title.length, Alarm.titleMaxLength);
      expect(alarm.tasks.length, Alarm.maxTaskCount);
      expect(alarm.tasks[0].configuration,
          const ShakeConfiguration(count: TaskConfiguration.shakeCountMax));
      expect(
        alarm.tasks[1].configuration,
        const MathConfiguration(difficulty: MathDifficulty.easy, questionCount: 1),
      );
      expect(alarm.tasks[2].configuration, const PhotoConfiguration(prompt: 'kupa'));
      expect(alarm.tasks[3].configuration,
          const ShakeConfiguration(count: TaskConfiguration.shakeCountMin));
      expect(alarm.snooze.durationMinutes, SnoozeSetting.durationMax);
      expect(alarm.snooze.maxCount, SnoozeSetting.maxCountMax);
    });

    test('JSON gidiş-dönüşü tüm alanları korur', () {
      final original = Alarm(
        id: 'a9',
        title: 'Spor',
        time: ClockTime(8, 45),
        repeatDays: {Weekday.tuesday, Weekday.thursday},
        isEnabled: false,
        tasks: const [
          AlarmTask(id: 't1', configuration: ShakeConfiguration(count: 15)),
          AlarmTask(
            id: 't2',
            configuration:
                MathConfiguration(difficulty: MathDifficulty.hard, questionCount: 3),
          ),
          AlarmTask(id: 't3', configuration: PhotoConfiguration(prompt: 'Spor çantası')),
        ],
        snooze: const SnoozeSetting(isEnabled: true, durationMinutes: 10, maxCount: 2),
        createdAt: DateTime.utc(2026, 8, 18, 9, 23, 38),
      );

      expect(Alarm.fromJson(original.toJson()), original);
    });

    test('createdAt saniye hassasiyetindedir', () {
      // Saniye altı hassasiyet ISO8601 gidiş-dönüşünde kaybolur ve iki
      // mantıksal olarak aynı alarmın eşitsiz görünmesine yol açar.
      final messy = DateTime.fromMillisecondsSinceEpoch(1755500618123);
      final alarm = Alarm(id: 'x', time: ClockTime(7, 0), createdAt: messy);
      expect(alarm.createdAt.millisecondsSinceEpoch % 1000, 0);
    });

    test('görev türü ve ayarı uyumsuz kalamaz', () {
      for (final kind in TaskKind.values) {
        final config = TaskConfiguration.makeDefault(kind);
        expect(config.kind, kind);
        // Varsayılanlar zaten geçerli aralıkta olmalı.
        expect(config.normalized(), config);
      }
    });

    test('açık alarmlar kapalı olanlardan önce, her grup saate göre sıralanır', () {
      Alarm at(String id, int hour, {bool enabled = true}) => Alarm(
            id: id,
            time: ClockTime(hour, 0),
            isEnabled: enabled,
            createdAt: DateTime.utc(2026, 1, 1),
          );

      final sorted = [
        at('c', 23, enabled: false),
        at('a', 5, enabled: false),
        at('d', 22),
        at('b', 4),
      ].sortedForDisplay();

      expect(sorted.map((a) => a.time.hour).toList(), [4, 22, 5, 23]);
      expect(sorted.map((a) => a.isEnabled).toList(), [true, true, false, false]);
    });

    test('sıralama kararlıdır', () {
      final early = Alarm(
          id: 'z', time: ClockTime(7, 0), createdAt: DateTime.utc(2026, 1, 1, 0, 0, 1));
      final late = Alarm(
          id: 'a', time: ClockTime(7, 0), createdAt: DateTime.utc(2026, 1, 1, 0, 0, 2));

      final once = [late, early].sortedForDisplay();
      final twice = once.sortedForDisplay();
      expect(once.map((a) => a.id).toList(), ['z', 'a']);
      expect(twice.map((a) => a.id).toList(), once.map((a) => a.id).toList());
    });
  });
}
