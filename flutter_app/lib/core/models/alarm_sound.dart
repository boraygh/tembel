/// Alarm sesi.
///
/// `systemDefault` dışındaki sesler platform tarafına dosya adıyla verilir.
/// Özel seslerin gerçek cihazda çalıştığı henüz doğrulanmadığı için varsayılan
/// `systemDefault`'tur ve diğerleri kullanıcıya kapalıdır.
enum AlarmSound {
  systemDefault,
  aggressive,
  siren,
  digital,
  emergency,
  buzzer;

  /// Paketteki ses dosyasının adı. `systemDefault` için `null` — bu durumda
  /// platformun kendi alarm sesi kullanılır.
  String? get fileName => this == AlarmSound.systemDefault ? null : '$name.caf';

  /// Gerçek cihazda doğrulanana kadar kullanıcıya sunulacak sesler.
  static const List<AlarmSound> availableForSelection = [AlarmSound.systemDefault];

  static AlarmSound fromName(String? name) => AlarmSound.values.firstWhere(
    (s) => s.name == name,
    orElse: () => AlarmSound.systemDefault,
  );
}
