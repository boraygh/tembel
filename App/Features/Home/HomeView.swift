import SwiftUI

/// Ana sayfa — kurulu alarmların listesi.
///
/// Phase 1'de yalnızca boş durum ve navigation iskeleti var.
/// Alarm listesi Phase 2'de (model + persistence) gelecek.
struct HomeView: View {
    @State private var isPresentingEditor = false

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Palette.background
                    .ignoresSafeArea()

                emptyState
            }
            .navigationTitle("Alarmlar")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Alarm ekle", systemImage: "plus") {
                        isPresentingEditor = true
                    }
                }
            }
            .sheet(isPresented: $isPresentingEditor) {
                AlarmEditorView()
            }
        }
    }

    private var emptyState: some View {
        ContentUnavailableView {
            Label("Alarm yok", systemImage: "alarm")
        } description: {
            Text("Kalkmak için görev tamamlaman gereken bir alarm kur.")
        } actions: {
            Button("Alarm kur") {
                isPresentingEditor = true
            }
            .buttonStyle(.borderedProminent)
            .tint(Theme.Palette.accent)
        }
    }
}

#Preview {
    HomeView()
        .preferredColorScheme(.dark)
}
