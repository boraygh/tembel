import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:tembel/core/models/alarm.dart';
import 'package:tembel/core/models/alarm_sound.dart';
import 'package:tembel/core/models/alarm_task.dart';
import 'package:tembel/core/models/clock_time.dart';
import 'package:tembel/core/models/snooze_setting.dart';
import 'package:tembel/core/premium/entitlement.dart';
import 'package:tembel/core/session/alarm_session.dart';
import 'package:tembel/core/tasks/math_question.dart';
import 'package:tembel/core/tasks/shake_detector.dart';

void main() {
  group('Matematik görevi', () {
    List<MathQuestion> sample(MathDifficulty difficulty, {int count = 400}) =>
        MathQuestionGenerator(difficulty).makeQuestions(count, random: Random(20260818));

    for (final difficulty in MathDifficulty.values) {
      test('${difficulty.name}: cevap negatif olmaz, soru ile tutarlıdır', () {
        for (final q in sample(difficulty)) {
          expect(q.answer, greaterThanOrEqualTo(0));
          final expected = switch (q.operation) {
            MathOperation.addition => q.left + q.right,
            MathOperation.subtraction => q.left - q.right,
            MathOperation.multiplication => q.left * q.right,
            MathOperation.division => q.left ~/ q.right,
          };
          expect(q.answer, expected);
        }
      });

      test('${difficulty.name}: bölme tam bölünür, sıfıra bölünmez', () {
        for (final q in sample(
          difficulty,
        ).where((q) => q.operation == MathOperation.division)) {
          expect(q.right, isNot(0));
          expect(q.left % q.right, 0);
        }
      });

      test('${difficulty.name}: anlamsız çarpan ve bedava soru yok', () {
        for (final q in sample(difficulty)) {
          switch (q.operation) {
            case MathOperation.multiplication:
            case MathOperation.division:
              expect(q.left, greaterThan(1));
              expect(q.right, greaterThan(1));
            case MathOperation.subtraction:
              expect(q.answer, greaterThan(0));
            case MathOperation.addition:
              expect(q.left, greaterThan(0));
              expect(q.right, greaterThan(0));
          }
        }
      });
    }

    test('seviyeler doğru işlem kümesini kullanır', () {
      expect(sample(MathDifficulty.easy).map((q) => q.operation).toSet(), {
        MathOperation.addition,
        MathOperation.subtraction,
      });
      final medium = sample(MathDifficulty.medium).map((q) => q.operation).toSet();
      expect(medium.contains(MathOperation.multiplication), isTrue);
      expect(medium.contains(MathOperation.division), isFalse);
      expect(
        sample(MathDifficulty.hard).map((q) => q.operation).toSet(),
        MathOperation.values.toSet(),
      );
    });

    test('zorluk arttıkça sorular gerçekten zorlaşır', () {
      double average(MathDifficulty d) {
        final qs = sample(d);
        return qs.map((q) => q.answer).reduce((a, b) => a + b) / qs.length;
      }

      expect(average(MathDifficulty.easy), lessThan(average(MathDifficulty.medium)));
      expect(average(MathDifficulty.medium), lessThan(average(MathDifficulty.hard)));
    });

    test('aynı tohum aynı soruları üretir', () {
      const generator = MathQuestionGenerator(MathDifficulty.hard);
      final left = generator.makeQuestions(20, random: Random(42));
      final right = generator.makeQuestions(20, random: Random(42));
      expect(
        left.map((q) => q.promptText).toList(),
        right.map((q) => q.promptText).toList(),
      );
    });

    test('istenen sayıda soru üretilir', () {
      const generator = MathQuestionGenerator(MathDifficulty.easy);
      expect(generator.makeQuestions(3, random: Random(7)).length, 3);
      expect(generator.makeQuestions(0, random: Random(7)), isEmpty);
      expect(generator.makeQuestions(-5, random: Random(7)), isEmpty);
    });

    test('cevap kontrolü boşlukları yok sayar, geçersiz girdiyi reddeder', () {
      final q = MathQuestion(left: 47, right: 28, operation: MathOperation.addition);
      expect(q.answer, 75);
      expect(q.promptText, '47 + 28');
      expect(q.isCorrect('75'), isTrue);
      expect(q.isCorrect('  75 '), isTrue);
      expect(q.isCorrect('74'), isFalse);
      expect(q.isCorrect(''), isFalse);
      expect(q.isCorrect('yetmişbeş'), isFalse);
      expect(q.isCorrect('75.0'), isFalse);
      expect(q.isCorrect('7 5'), isFalse);
    });

    test('işaretler gerçek matematik karakterleridir', () {
      expect(
        MathQuestion(left: 30, right: 8, operation: MathOperation.subtraction).promptText,
        '30 − 8',
      ); // U+2212
      expect(
        MathQuestion(
          left: 12,
          right: 7,
          operation: MathOperation.multiplication,
        ).promptText,
        '12 × 7',
      );
      expect(
        MathQuestion(left: 40, right: 8, operation: MathOperation.division).promptText,
        '40 ÷ 8',
      );
    });
  });

  group('Sallama algılama', () {
    MotionSample at(double magnitude, int milliseconds) => MotionSample(
      x: magnitude,
      y: 0,
      z: 0,
      timestamp: Duration(milliseconds: milliseconds),
    );

    /// Temiz sallama dalgası: her döngüde önce dinlenme, sonra tepe.
    /// Tepeler 200 ms arayla gelir — varsayılan 180 ms beklemenin üstünde.
    List<MotionSample> wave(int count) => [
      for (var i = 0; i < count; i++) ...[at(0.2, i * 200), at(2.5, i * 200 + 100)],
    ];

    test('temiz dalgada tepe sayısı kadar sallama sayılır', () {
      final detector = ShakeDetector(target: 10);
      detector.processAll(wave(10));
      expect(detector.count, 10);
      expect(detector.isComplete, isTrue);
    });

    test('sürekli yüksek ivme tek sallama sayılır', () {
      final detector = ShakeDetector(target: 10);
      detector.processAll([for (var i = 0; i < 40; i++) at(2.5, i * 50)]);
      expect(detector.count, 1);
    });

    test('çok hızlı tekrar eden tepeler titreşim sayılır', () {
      final detector = ShakeDetector(target: 10);
      detector.process(at(0.2, 20));
      expect(detector.process(at(2.5, 100)), isTrue);
      detector.process(at(0.2, 120));
      expect(detector.process(at(2.5, 140)), isFalse); // çok erken
      detector.process(at(0.2, 300));
      expect(detector.process(at(2.5, 350)), isTrue);
      expect(detector.count, 2);
    });

    test('eşiğin altındaki hareket ve sabit cihaz sayılmaz', () {
      final gentle = ShakeDetector(target: 5)
        ..processAll([for (var i = 0; i < 60; i++) at(1.2, i * 100)]);
      expect(gentle.count, 0);

      final still = ShakeDetector(target: 5)
        ..processAll([for (var i = 0; i < 100; i++) at(0.03, i * 20)]);
      expect(still.count, 0);
    });

    test('zaten sallanırken başlanırsa ilk tepe sayılır', () {
      final detector = ShakeDetector(target: 3);
      expect(detector.process(at(2.5, 0)), isTrue);
    });

    test('ilerleme hedefe göre hesaplanır ve 1\'i geçmez', () {
      final detector = ShakeDetector(target: 4);
      expect(detector.progress, 0);
      expect(detector.remaining, 4);
      detector.processAll(wave(2));
      expect(detector.progress, 0.5);
      detector.processAll(wave(10));
      expect(detector.progress, 1);
      expect(detector.remaining, 0);
    });

    test('hedef sıfır veya negatifse görev baştan tamamlanmıştır', () {
      expect(ShakeDetector(target: 0).isComplete, isTrue);
      expect(ShakeDetector(target: -5).target, 0);
    });

    test('sıfırlama sayacı ve durumu başa alır', () {
      final detector = ShakeDetector(target: 10)..processAll(wave(4));
      expect(detector.count, 4);
      detector.reset();
      expect(detector.count, 0);
      expect(detector.process(at(2.5, 99000)), isTrue);
    });

    test('zamanı geriye giden örnekler yok sayılır', () {
      final detector = ShakeDetector(target: 10);
      detector.process(at(0.2, 5000));
      expect(detector.process(at(2.5, 5100)), isTrue);
      expect(detector.process(at(2.5, 1000)), isFalse);
      expect(detector.count, 1);
    });

    test('bırakma eşiği tetikleme eşiğini geçemez', () {
      final config = ShakeDetectorConfiguration(
        triggerThreshold: 1.5,
        releaseThreshold: 9.0,
        minimumInterval: const Duration(milliseconds: -1),
      );
      expect(config.releaseThreshold, 1.5);
      expect(config.minimumInterval, Duration.zero);
    });

    test('büyüklük üç eksenin bileşkesidir', () {
      expect(const MotionSample(x: 3, y: 4, z: 0, timestamp: Duration.zero).magnitude, 5);
    });
  });

  group('Alarm oturumu', () {
    final start = DateTime(2026, 8, 17, 7, 30);

    AlarmSession session({int taskCount = 3, SnoozeSetting? snooze}) =>
        AlarmSession.start(
          id: 's1',
          alarm: Alarm(
            id: 'a1',
            title: 'Test',
            time: ClockTime(7, 30),
            tasks: List.generate(
              taskCount,
              (i) => AlarmTask(
                id: 't$i',
                configuration: const ShakeConfiguration(count: 10),
              ),
            ),
            snooze: snooze ?? SnoozeSetting.disabled,
            createdAt: DateTime(2026, 1, 1),
          ),
          startedAt: start,
        );

    test('yeni oturum ilk görevden başlar', () {
      final s = session();
      expect(s.completedCount, 0);
      expect(s.currentTaskNumber, 1);
      expect(s.currentTask?.id, 't0');
      expect(s.phase, SessionPhase.running);
      expect(s.progress, 0);
    });

    test('görevsiz alarm anında tamamlanmış sayılır', () {
      final s = session(taskCount: 0);
      expect(s.isComplete, isTrue);
      expect(s.currentTask, isNull);
      expect(s.phase, SessionPhase.finished);
      expect(s.progress, 1);
    });

    test('görevler sırayla tamamlanır ve atlanamaz', () {
      final s = session();
      // Üçüncü görevi tamamlamaya çalışmak reddedilmeli.
      expect(s.completeCurrentTask(taskId: 't2', at: start), isFalse);
      expect(s.completedCount, 0);

      expect(s.completeCurrentTask(at: start), isTrue);
      expect(s.currentTaskNumber, 2);
      // Aynı dokunuş bir kez daha gelirse ikinci görevi tamamlamamalı.
      expect(s.completeCurrentTask(taskId: 't0', at: start), isFalse);
      expect(s.completedCount, 1);

      s.completeCurrentTask(at: start);
      s.completeCurrentTask(at: start);
      expect(s.isComplete, isTrue);
      expect(s.phase, SessionPhase.finished);
      expect(s.completeCurrentTask(at: start), isFalse);
    });

    test('görevler alarmdan kopyalanır', () {
      final alarm = Alarm(
        id: 'a1',
        title: 'Test',
        time: ClockTime(7, 30),
        tasks: const [AlarmTask(id: 't0', configuration: ShakeConfiguration(count: 10))],
        createdAt: DateTime(2026, 1, 1),
      );
      final s = AlarmSession.start(id: 's', alarm: alarm, startedAt: start);
      // Alarm çalarken silinse bile ekranda gösterilecek bilgi durmalı.
      expect(s.alarmTitle, 'Test');
      expect(s.alarmTime, ClockTime(7, 30));
      expect(s.tasks.length, 1);
    });

    test('erteleme sınırlıdır ve kapalıyken çalışmaz', () {
      expect(session().snoozeNow(start), isNull);

      final s = session(
        snooze: const SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 2),
      );
      expect(s.snoozeNow(start), start.add(const Duration(minutes: 5)));
      expect(s.phase, SessionPhase.snoozed);
      // Ertelenmişken görev tamamlanamaz.
      expect(s.completeCurrentTask(at: start), isFalse);
      // Süre dolmadan geri dönülemez.
      expect(s.resumeFromSnooze(start.add(const Duration(minutes: 4))), isFalse);
      expect(s.resumeFromSnooze(start.add(const Duration(minutes: 5))), isTrue);

      s.snoozeNow(start.add(const Duration(minutes: 5)));
      s.resumeFromSnooze(start.add(const Duration(minutes: 10)));
      expect(s.canSnooze, isFalse);
      expect(s.remainingSnoozeCount, 0);
    });

    test('görevleri baştan başlatmak erteleme hakkını geri vermez', () {
      final s = session(
        taskCount: 2,
        snooze: const SnoozeSetting(isEnabled: true, durationMinutes: 5, maxCount: 1),
      );
      s.snoozeNow(start);
      s.resumeFromSnooze(start.add(const Duration(minutes: 5)));
      s.completeCurrentTask(at: start);

      s.restartTasks();
      expect(s.completedCount, 0);
      // Sınırsız erteleme üretilememeli.
      expect(s.snoozeCount, 1);
      expect(s.canSnooze, isFalse);
    });

    test('oturum JSON gidiş-dönüşünden sağ çıkar', () {
      final s = session()..completeCurrentTask(at: start);
      final restored = AlarmSession.fromJson(s.toJson());
      expect(restored, s);
      // Uygulama öldürülüp açıldığında kaldığı görevden devam etmeli.
      expect(restored.currentTaskNumber, 2);
    });
  });

  group('Premium yetkilendirme', () {
    final now = DateTime(2026, 8, 18);
    FeatureGate gate(EntitlementStatus status) =>
        FeatureGate(status: status, referenceDate: now);

    test('ömür boyu süresizdir, süresi dolmuş abonelik ücretsize düşer', () {
      expect(EntitlementStatus.lifetime.isLifetime, isTrue);
      expect(gate(EntitlementStatus.lifetime).isPremium, isTrue);

      final expired = EntitlementStatus.subscription(
        now.subtract(const Duration(seconds: 1)),
      );
      expect(gate(expired).isPremium, isFalse);
      expect(expired.isLifetime, isFalse);

      final active = EntitlementStatus.subscription(now.add(const Duration(days: 1)));
      expect(gate(active).isPremium, isTrue);
    });

    test('yetkilendirme JSON gidiş-dönüşünden sağ çıkar', () {
      for (final status in [
        EntitlementStatus.free,
        EntitlementStatus.lifetime,
        EntitlementStatus.subscription(now),
      ]) {
        expect(EntitlementStatus.fromJson(status.toJson()), status);
      }
    });

    test('ücretsiz sınırlar uygulanır', () {
      final free = gate(EntitlementStatus.free);
      expect(free.canAddAlarm(FeatureGate.freeAlarmLimit - 1), isTrue);
      expect(free.canAddAlarm(FeatureGate.freeAlarmLimit), isFalse);
      expect(free.canAddTask(FeatureGate.freeTaskLimitPerAlarm), isFalse);
      expect(free.availableTaskKinds, [TaskKind.shake, TaskKind.math]);
      expect(free.hasTaskKind(TaskKind.photo), isFalse);
      expect(free.hasSound(AlarmSound.systemDefault), isTrue);
      expect(free.hasSound(AlarmSound.siren), isFalse);
    });

    test('premium sınırları açar ama modelin üst sınırını aşmaz', () {
      final premium = gate(EntitlementStatus.lifetime);
      expect(premium.canAddAlarm(500), isTrue);
      // Sınır, Alarm.normalized()'ın kırptığı değerle aynı olmalı; aksi hâlde
      // kullanıcıya ekleyebileceği söylenen görev sessizce silinir.
      expect(premium.taskLimitPerAlarm, Alarm.maxTaskCount);
      expect(premium.availableTaskKinds.toSet(), TaskKind.values.toSet());
      for (final feature in PremiumFeature.values) {
        expect(gate(EntitlementStatus.free).hasFeature(feature), isFalse);
        expect(premium.hasFeature(feature), isTrue);
      }
    });

    test('güvenilirlik özellikleri premium listesinde yer almaz', () {
      // Bu test bir sözleşmedir: alarmın çalması, takip zinciri ve görevlerin
      // zorunlu olması hiçbir zaman satılmaz.
      final names = PremiumFeature.values.map((f) => f.name).toSet();
      expect(names.contains('followUpChain'), isFalse);
      expect(names.contains('alarmReliability'), isFalse);
      expect(names.contains('taskEnforcement'), isFalse);
    });

    test('ücretsiz kademe uygulamanın ne yaptığını gösterebilmeli', () {
      // En az bir fiziksel ve bir zihinsel görev ücretsiz olmalı.
      expect(FeatureGate.freeTaskKinds.contains(TaskKind.shake), isTrue);
      expect(FeatureGate.freeTaskKinds.contains(TaskKind.math), isTrue);
    });
  });
}
