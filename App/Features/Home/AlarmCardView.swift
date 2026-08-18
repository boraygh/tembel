import SwiftUI
import TembelCore

/// Ana sayfadaki tek alarm kartı.
///
/// Yedi gün rozeti yerine tek satır özet ("Hafta içi") kullanılıyor: liste
/// ekranında okunan şey saat ve başlık, günlerin tek tek hangileri olduğu
/// değil. Ayrıntı düzenleyicide zaten var.
struct AlarmCardView: View {
    let alarm: Alarm
    let onToggle: (Bool) -> Void
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm + 6) {
            timeRow
            subtitleRow
            if alarm.requiresTasks {
                taskRow
            }
        }
        .padding(Theme.Spacing.md + 4)
        .materialCard()
        .opacity(alarm.isEnabled ? 1 : 0.34)
        .contentShape(Rectangle())
        .onTapGesture(perform: onEdit)
        .contextMenu {
            Button(action: onEdit) {
                Label(AppStrings.Home.edit, systemImage: "pencil")
            }
            Button(role: .destructive, action: onDelete) {
                Label(AppStrings.Home.delete, systemImage: "trash")
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("\(alarm.time.displayText) \(alarm.displayTitle)")
    }

    private var timeRow: some View {
        HStack(alignment: .center) {
            Text(alarm.time.displayText)
                .font(Theme.Typography.cardTime)
                .tracking(Theme.Tracking.cardTime)
                .monospacedDigit()
                .foregroundStyle(Theme.Palette.textPrimary)

            Spacer(minLength: Theme.Spacing.sm)

            Toggle("", isOn: Binding(get: { alarm.isEnabled }, set: onToggle))
                .labelsHidden()
                .tint(Theme.Palette.accent)
                .accessibilityLabel(alarm.displayTitle)
        }
    }

    private var subtitleRow: some View {
        HStack(spacing: Theme.Spacing.sm + 2) {
            Text(alarm.displayTitle)
                .font(Theme.Typography.callout)
                .foregroundStyle(Theme.Palette.textPrimary.opacity(0.92))
                .lineLimit(1)

            Circle()
                .fill(Theme.Palette.textQuaternary)
                .frame(width: 3, height: 3)

            Text(alarm.repeatSummary)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)
                .lineLimit(1)

            Spacer(minLength: 0)
        }
    }

    private var taskRow: some View {
        HStack(spacing: 7) {
            ForEach(alarm.tasks) { task in
                TaskIconBox(kind: task.kind, size: 28)
            }
            Text(AppStrings.Home.taskCount(alarm.tasks.count))
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textTertiary)
                .padding(.leading, 2)
            Spacer(minLength: 0)
        }
    }
}

#Preview {
    ZStack {
        Theme.Gradients.page.ignoresSafeArea()
        VStack(spacing: 12) {
            ForEach(Alarm.samples) { alarm in
                AlarmCardView(alarm: alarm, onToggle: { _ in }, onEdit: {}, onDelete: {})
            }
        }
        .padding(Theme.Spacing.lg)
    }
    .preferredColorScheme(.dark)
}
