import SwiftUI

/// Alarm oluşturma/düzenleme ekranı.
///
/// Phase 1'de yalnızca sunum iskeleti. Saat seçici, tekrar günleri, görev
/// listesi ve ses seçimi Phase 3'te gelecek.
struct AlarmEditorView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Palette.background
                    .ignoresSafeArea()

                Text("Alarm düzenleyici Phase 3'te gelecek.")
                    .font(.footnote)
                    .foregroundStyle(Theme.Palette.textTertiary)
            }
            .navigationTitle("Yeni Alarm")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Vazgeç") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    AlarmEditorView()
        .preferredColorScheme(.dark)
}
