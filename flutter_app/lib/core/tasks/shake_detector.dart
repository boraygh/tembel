import 'dart:math' as math;

import 'package:meta/meta.dart';

/// Tek bir ivmeölçer okuması.
///
/// Değerler yerçekimi çıkarılmış ivmedir (birim g). Cihaz sabitken büyüklük
/// sıfıra yakındır.
@immutable
class MotionSample {
  const MotionSample({
    required this.x,
    required this.y,
    required this.z,
    required this.timestamp,
  });

  final double x;
  final double y;
  final double z;

  /// Örnekler arası fark anlamlıdır; mutlak değeri bir tarih değildir.
  final Duration timestamp;

  double get magnitude => math.sqrt(x * x + y * y + z * z);
}

@immutable
class ShakeDetectorConfiguration {
  ShakeDetectorConfiguration({
    required this.triggerThreshold,
    required double releaseThreshold,
    required Duration minimumInterval,
  })  :
        // Bırakma eşiği tetikleme eşiğinin üstünde olamaz; olursa histerezis
        // anlamını yitirir ve her örnek sayılmaya başlar.
        releaseThreshold = math.min(releaseThreshold, triggerThreshold),
        minimumInterval =
            minimumInterval.isNegative ? Duration.zero : minimumInterval;

  /// Bu büyüklüğün üzerine çıkmak bir sallama sayılır.
  final double triggerThreshold;

  /// Yeni bir sallama sayılabilmesi için önce bu değerin altına inilmelidir.
  /// Tek bir sert hareketin defalarca sayılmasını engeller.
  final double releaseThreshold;

  /// İki sallama arasında geçmesi gereken en kısa süre. Titreşimin sayıya
  /// dönüşmesini engeller.
  final Duration minimumInterval;

  /// Başlangıç değerleri.
  ///
  /// ⚠️ Bu sayılar gerçek cihazda ayarlanmalıdır. Emülatör/tarayıcıda ivmeölçer
  /// yoktur; burada yalnızca algoritmanın kendisi doğrulanabilir.
  static final ShakeDetectorConfiguration standard = ShakeDetectorConfiguration(
    triggerThreshold: 1.8,
    releaseThreshold: 0.8,
    minimumInterval: const Duration(milliseconds: 180),
  );
}

/// İvmeölçer örneklerini sallama sayısına çeviren durum makinesi.
///
/// Sensöre hiç bağlı değildir; örnekleri dışarıdan alır. Bu sayede algoritma
/// gerçek cihaz olmadan test edilebilir ve Demo Mode'da sahte verilerle
/// beslenebilir.
class ShakeDetector {
  ShakeDetector({required int target, ShakeDetectorConfiguration? configuration})
      : target = target < 0 ? 0 : target,
        configuration = configuration ?? ShakeDetectorConfiguration.standard;

  final int target;
  final ShakeDetectorConfiguration configuration;

  int _count = 0;

  /// Bir sonraki eşik aşımının sayılabilir olup olmadığı.
  /// Cihaz zaten sallanıyorken başlanabilsin diye açık başlar.
  bool _isArmed = true;
  Duration? _lastCountedAt;
  Duration? _lastSampleAt;

  int get count => _count;

  bool get isComplete => _count >= target;

  /// 0…1 arası tamamlanma oranı — ilerleme göstergesi için.
  double get progress => target <= 0 ? 1 : math.min(1, _count / target);

  int get remaining => math.max(0, target - _count);

  /// Bir örneği işler. Bu örnek yeni bir sallama saydırdıysa `true` döner.
  bool process(MotionSample sample) {
    // Zaman geriye giderse örnek güvenilmezdir; yok say.
    final last = _lastSampleAt;
    if (last != null && sample.timestamp < last) return false;
    _lastSampleAt = sample.timestamp;

    final magnitude = sample.magnitude;

    if (magnitude < configuration.releaseThreshold) {
      _isArmed = true;
      return false;
    }

    if (!_isArmed || magnitude < configuration.triggerThreshold) return false;

    final lastCounted = _lastCountedAt;
    if (lastCounted != null &&
        sample.timestamp - lastCounted < configuration.minimumInterval) {
      // Çok erken geldi — sayma, ama kurulumu da bozma ki hareket
      // yavaşladığında yeniden sayılabilsin.
      return false;
    }

    _count += 1;
    _isArmed = false;
    _lastCountedAt = sample.timestamp;
    return true;
  }

  /// Bir dizi örneği sırayla işler, sayılan sallama adedini döndürür.
  int processAll(Iterable<MotionSample> samples) {
    var counted = 0;
    for (final sample in samples) {
      if (process(sample)) counted += 1;
    }
    return counted;
  }

  /// Sayacı ve durumu başa alır.
  void reset() {
    _count = 0;
    _isArmed = true;
    _lastCountedAt = null;
    _lastSampleAt = null;
  }
}
