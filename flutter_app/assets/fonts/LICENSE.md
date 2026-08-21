# Archivo

Bu klasördeki yazı tipi dosyaları **Archivo** ailesine aittir.

- Tasarım: Omnibus-Type
- Lisans: **SIL Open Font License 1.1** (OFL-1.1)
- Kaynak: Google Fonts (fonts.gstatic.com)
- Proje sayfası: https://github.com/Omnibus-Type/Archivo

SIL OFL 1.1, yazı tipinin ücretsiz olarak kullanılmasına, uygulamaya
gömülmesine ve ticari ürünlerde dağıtılmasına izin verir. Tek koşul, yazı
tipinin kendisinin tek başına satılmamasıdır — uygulamanın parçası olarak
dağıtılması serbesttir.

Lisansın tam metni: https://openfontlicense.org

## Dosyalar ve PostScript adları

`Font.custom(_:size:)` çağrılarında **PostScript adı** kullanılır, dosya adı
değil. Bu iki değer burada birebir aynı olacak şekilde seçildi:

| Dosya | PostScript adı | Ağırlık |
|---|---|---|
| `Archivo-Regular.ttf` | `Archivo-Regular` | 400 |
| `Archivo-Medium.ttf` | `Archivo-Medium` | 500 |
| `Archivo-SemiBold.ttf` | `Archivo-SemiBold` | 600 |
| `Archivo-Bold.ttf` | `Archivo-Bold` | 700 |
| `Archivo-ExtraBold.ttf` | `Archivo-ExtraBold` | 800 |

Dosyalar `project.yml` içindeki `UIAppFonts` listesinde kayıtlıdır. Yeni bir
ağırlık eklenirse hem bu tabloya hem o listeye eklenmelidir; kayıtlı olmayan
bir yazı tipi sessizce sistem yazı tipine düşer.
