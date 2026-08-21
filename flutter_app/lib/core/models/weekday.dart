/// Haftanın bir günü.
///
/// [value] kasıtlı olarak Dart'ın `DateTime.weekday` değerleriyle birebir
/// aynıdır (1 = Pazartesi … 7 = Pazar). Böylece tarih hesaplarında dönüşüm
/// yapmak gerekmez — alarm uygulamalarında en sık hata çıkan yer burasıdır.
///
/// Not: Swift sürümü Foundation'ın `Calendar.weekday` değerlerini kullanır
/// (1 = Pazar). İki uygulamanın kayıt dosyaları bu yüzden birbiriyle uyumlu
/// değildir; ikisi ayrı uygulamalardır.
enum Weekday {
  monday(1),
  tuesday(2),
  wednesday(3),
  thursday(4),
  friday(5),
  saturday(6),
  sunday(7);

  const Weekday(this.value);

  /// `DateTime.weekday` karşılığı.
  final int value;

  /// Pazartesi'yi haftanın ilk günü kabul eden sıralama indeksi (0…6).
  int get mondayFirstIndex => value - 1;

  static Weekday fromDateTime(DateTime date) => Weekday.values[date.weekday - 1];

  static Weekday? fromValue(int value) =>
      (value >= 1 && value <= 7) ? Weekday.values[value - 1] : null;

  /// Pazartesi'den Pazar'a sıralı.
  static List<Weekday> get orderedMondayFirst => Weekday.values;

  static const Set<Weekday> weekdays = {
    Weekday.monday,
    Weekday.tuesday,
    Weekday.wednesday,
    Weekday.thursday,
    Weekday.friday,
  };

  static const Set<Weekday> weekend = {Weekday.saturday, Weekday.sunday};

  static Set<Weekday> get everyday => Weekday.values.toSet();
}

/// Kümeleri kararlı bir sırayla listeye çevirir.
extension WeekdaySetOrdering on Set<Weekday> {
  List<Weekday> get ordered {
    final list = toList()
      ..sort((a, b) => a.mondayFirstIndex.compareTo(b.mondayFirstIndex));
    return list;
  }
}
