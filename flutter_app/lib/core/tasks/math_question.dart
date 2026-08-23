import 'dart:math';

import 'package:meta/meta.dart';

import '../models/alarm_task.dart';

enum MathOperation {
  addition('+'),
  subtraction('−'), // gerçek eksi işareti, kısa çizgi değil
  multiplication('×'),
  division('÷');

  const MathOperation(this.symbol);

  /// Ekranda gösterilen işaret. Matematik işaretleri dile bağlı olmadığı için
  /// çekirdekte tutulabilir.
  final String symbol;
}

/// Tek bir matematik sorusu.
///
/// Soru ve cevabı birlikte taşır; cevap üretim anında hesaplanır. Böylece
/// "gösterilen soru ile beklenen cevap farklı" sınıfı hatalar mümkün değildir.
@immutable
class MathQuestion {
  MathQuestion({
    required this.left,
    required this.right,
    required this.operation,
    String? id,
  }) : answer = switch (operation) {
         MathOperation.addition => left + right,
         MathOperation.subtraction => left - right,
         MathOperation.multiplication => left * right,
         MathOperation.division => left ~/ right,
       },
       id = id ?? '$left${operation.name}$right#${_counter++}';

  static int _counter = 0;

  final String id;
  final int left;
  final int right;
  final MathOperation operation;
  final int answer;

  /// "47 + 28" — soru metni, cevap alanı hariç.
  String get promptText => '$left ${operation.symbol} $right';

  /// Girilen metnin doğru cevap olup olmadığı.
  ///
  /// Baştaki/sondaki boşluklar yok sayılır. Boş girdi yanlış sayılır, hata
  /// değildir — kullanıcı yazmayı sürdürüyordur.
  bool isCorrect(String input) => int.tryParse(input.trim()) == answer;

  @override
  String toString() => '$promptText = $answer';
}

/// Zorluk seviyesine göre matematik sorusu üretir.
///
/// Üretilen her soru şu güvenceleri taşır:
/// - Cevap her zaman pozitiftir (çıkarmada negatif çıkmaz).
/// - Bölme her zaman tam bölünür, kalan olmaz.
/// - Soruyu anlamsızlaştıran 0 veya 1 çarpanları kullanılmaz.
///
/// Rastgelelik dışarıdan verilebilir; testler ve Demo Mode tekrarlanabilir
/// sonuç için tohumlu `Random` kullanır.
class MathQuestionGenerator {
  const MathQuestionGenerator(this.difficulty);

  final MathDifficulty difficulty;

  List<MathOperation> get operations => switch (difficulty) {
    MathDifficulty.easy => const [MathOperation.addition, MathOperation.subtraction],
    MathDifficulty.medium => const [
      MathOperation.addition,
      MathOperation.subtraction,
      MathOperation.multiplication,
    ],
    MathDifficulty.hard => MathOperation.values,
  };

  List<MathQuestion> makeQuestions(int count, {Random? random}) {
    final rng = random ?? Random();
    final safeCount = count < 0 ? 0 : count;
    return List.generate(safeCount, (_) => makeQuestion(random: rng));
  }

  MathQuestion makeQuestion({Random? random}) {
    final rng = random ?? Random();
    final available = operations;
    final operation = available[rng.nextInt(available.length)];
    return _make(operation, rng);
  }

  MathQuestion _make(MathOperation operation, Random rng) {
    switch (operation) {
      case MathOperation.addition:
        final range = _additionRange;
        return MathQuestion(
          left: _pick(range, rng),
          right: _pick(range, rng),
          operation: operation,
        );

      case MathOperation.subtraction:
        // Önce farkı ve çıkanı seçip toplamı hesaplıyoruz; sonucun negatif
        // olması matematiksel olarak imkânsız.
        final difference = _pick(_subtractionResultRange, rng);
        final subtrahend = _pick(_subtractionOperandRange, rng);
        return MathQuestion(
          left: difference + subtrahend,
          right: subtrahend,
          operation: operation,
        );

      case MathOperation.multiplication:
        final range = _multiplicationRange;
        return MathQuestion(
          left: _pick(range, rng),
          right: _pick(range, rng),
          operation: operation,
        );

      case MathOperation.division:
        // Böleni çarpımdan türetiyoruz; kalan olması imkânsız.
        final divisor = _pick(_divisionDivisorRange, rng);
        final quotient = _pick(_divisionQuotientRange, rng);
        return MathQuestion(
          left: divisor * quotient,
          right: divisor,
          operation: operation,
        );
    }
  }

  static int _pick((int, int) range, Random rng) =>
      range.$1 + rng.nextInt(range.$2 - range.$1 + 1);

  (int, int) get _additionRange => switch (difficulty) {
    MathDifficulty.easy => (2, 20),
    MathDifficulty.medium => (12, 89),
    MathDifficulty.hard => (45, 249),
  };

  (int, int) get _subtractionResultRange => switch (difficulty) {
    MathDifficulty.easy => (1, 15),
    MathDifficulty.medium => (6, 60),
    MathDifficulty.hard => (18, 180),
  };

  (int, int) get _subtractionOperandRange => switch (difficulty) {
    MathDifficulty.easy => (2, 9),
    MathDifficulty.medium => (11, 49),
    MathDifficulty.hard => (24, 199),
  };

  (int, int) get _multiplicationRange => switch (difficulty) {
    MathDifficulty.easy => (2, 9),
    MathDifficulty.medium => (3, 12),
    MathDifficulty.hard => (6, 19),
  };

  (int, int) get _divisionDivisorRange => switch (difficulty) {
    MathDifficulty.easy => (2, 5),
    MathDifficulty.medium => (2, 9),
    MathDifficulty.hard => (3, 12),
  };

  (int, int) get _divisionQuotientRange => switch (difficulty) {
    MathDifficulty.easy => (2, 5),
    MathDifficulty.medium => (2, 9),
    MathDifficulty.hard => (3, 15),
  };
}
