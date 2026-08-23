import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tembel/localization/strings.dart';
import 'package:tembel/main.dart';

/// Ekranların gerçekten kurulduğunu doğrular.
///
/// Bu dosya iki gerçek hatanın ardından yazıldı; ikisini de `flutter analyze`
/// ve birim testler kaçırmıştı, çünkü hiçbiri widget ağacını kurmuyordu:
/// - `Switch` üstünde `Material` atasosu bulamayınca çalışma anında patlıyordu.
/// - Kaçırılmış `$` yüzünden ekranda değişken yerine `$hours` yazıyordu.
void main() {
  testWidgets('uygulama hatasız açılır ve alarmları gösterir', (tester) async {
    await tester.pumpWidget(const TembelApp());
    await tester.pump();

    // Build sırasında bir istisna oluştuysa burada yakalanır.
    expect(tester.takeException(), isNull);

    expect(find.text('Alarmlar'), findsOneWidget);
    expect(find.text('07:30'), findsOneWidget);
    expect(find.text('İşe Kalk'), findsOneWidget);

    // Switch'ler Material atasosu olmadan kurulamaz; varlıkları o zincirin
    // sağlam olduğunu gösterir.
    expect(find.byType(Switch), findsNWidgets(sampleAlarms.length));
  });

  testWidgets('alarm anahtarı kapatılabilir', (tester) async {
    await tester.pumpWidget(const TembelApp());
    await tester.pump();

    await tester.tap(find.byType(Switch).first);
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });

  group('Kalan süre metni', () {
    final from = DateTime(2026, 8, 22, 12);

    /// Ekranda ham `$degisken` görünmesi, kaçırılmış bir dolar işareti demektir.
    void expectNoRawInterpolation(String? text) {
      expect(text, isNotNull);
      expect(text, isNot(contains(r'$')));
    }

    test('gün + saat', () {
      final text = Strings.timeRemaining(
        from.add(const Duration(days: 1, hours: 3)),
        from,
      );
      expectNoRawInterpolation(text);
      expect(text, '1 gün 3 saat sonra');
    });

    test('saat + dakika', () {
      final text = Strings.timeRemaining(
        from.add(const Duration(hours: 8, minutes: 42)),
        from,
      );
      expectNoRawInterpolation(text);
      expect(text, '8 sa 42 dk sonra');
    });

    test('tam saat ve tam gün', () {
      expectNoRawInterpolation(
        Strings.timeRemaining(from.add(const Duration(hours: 3)), from),
      );
      expect(
        Strings.timeRemaining(from.add(const Duration(hours: 3)), from),
        '3 saat sonra',
      );
      expect(
        Strings.timeRemaining(from.add(const Duration(days: 2)), from),
        '2 gün sonra',
      );
    });

    test('dakika altı ve geçmiş', () {
      expect(
        Strings.timeRemaining(from.add(const Duration(seconds: 30)), from),
        'birazdan',
      );
      expect(
        Strings.timeRemaining(from.subtract(const Duration(minutes: 1)), from),
        isNull,
      );
    });
  });
}
