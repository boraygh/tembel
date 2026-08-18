import SwiftUI
import TembelCore

/// Ana sayfadaki tek alarm kartı.
struct AlarmCardView: View {
    let alarm: Alarm
    let onToggle: (Bool) -> Void
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm + 4) {
            header
            WeekdayIndicator(selection: alarm.repeatDays, isDimmed: !alarm.isEnabled)
            Rectangle()
                .fill(Theme.Palette.separator)
                .frame(height: 1)
            footer
        }
        .padding(Theme.Spacing.md)
        .cardBackground()
        .opacity(alarm.isEnabled ? 1 : 0.42)
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

    private var header: some View {
        HStack(alignment: .top, spacing: Theme.Spacing.sm + 4) {
            VStack(alignment: .leading, spacing: 1) {
                Text(alarm.time.displayText)
                    .font(Theme.Typography.cardTime)
                    .tracking(Theme.Tracking.cardTime)
                    .monospacedDigit()
                    .foregroundStyle(Theme.Palette.textPrimary)
                Text(alarm.displayTitle)
                    .font(Theme.Typography.callout)
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .lineLimit(1)
            }
            Spacer(minLength: 0)
            Toggle(
                "",
                isOn: Binding(get: { alarm.isEnabled }, set: onToggle)
            )
            .labelsHidden()
            .tint(Theme.Palette.accent)
            .accessibilityLabel(alarm.displayTitle)
        }
    }

    private var footer: some View {
        HStack(spacing: Theme.Spacing.sm) {
            HStack(spacing: 6) {
                ForEach(alarm.tasks) { task in
                    TaskIconBox(kind: task.kind, size: 26)
                }
            }
            Text(taskSummary)
                .font(Theme.Typography.footnoteEmphasized)
                .foregroundStyle(Theme.Palette.textTertiary)
            Spacer(minLength: 0)
        }
    }

    private var taskSummary: String {
        alarm.repeatDays.isEmpty
            ? "\(AppStrings.Home.taskCount(alarm.tasks.count)) · \(AppStrings.Home.noRepeat)"
            : AppStrings.Home.taskCount(alarm.tasks.count)
    }
}

#Preview {
    ZStack {
        Theme.Palette.background.ignoresSafeArea()
        VStack(spacing: 10) {
            ForEach(Alarm.samples) { alarm in
                AlarmCardView(alarm: alarm, onToggle: { _ in }, onEdit: {}, onDelete: {})
            }
        }
        .padding(Theme.Spacing.md)
    }
    .preferredColorScheme(.dark)
}
