import SwiftUI
import TembelCore

/// Alarm oluşturma ve düzenleme ekranı.
///
/// Üzerinde çalışılan kopya (`draft`) yereldir; "Kaydet"e basılmadan hiçbir
/// değişiklik listeye yansımaz. "Vazgeç" gerçekten vazgeçer.
struct AlarmEditorView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(PremiumModel.self) private var premium

    @State private var draft: Alarm
    @State private var isTimePickerExpanded = true
    @State private var taskEditorContext: TaskEditorContext?
    @State private var isPresentingPaywall = false

    private let isNewAlarm: Bool
    private let onSave: (Alarm) -> Void

    init(alarm: Alarm, isNew: Bool = true, onSave: @escaping (Alarm) -> Void) {
        _draft = State(initialValue: alarm)
        self.isNewAlarm = isNew
        self.onSave = onSave
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Gradients.page.ignoresSafeArea()
                content
            }
            .navigationTitle(isNewAlarm ? AppStrings.Editor.newAlarmTitle : AppStrings.Editor.editAlarmTitle)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(AppStrings.Editor.cancel) { dismiss() }
                        .foregroundStyle(Theme.Palette.textSecondary)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(AppStrings.Editor.save) {
                        onSave(draft.normalized())
                        dismiss()
                    }
                    .font(Theme.Typography.bodyEmphasized)
                    .foregroundStyle(Theme.Palette.accent)
                    .disabled(!draft.canBeSaved)
                }
            }
            .sheet(item: $taskEditorContext) { context in
                TaskEditorView(
                    configuration: context.configuration,
                    isNew: context.isNew
                ) { updated in
                    apply(updated, for: context)
                }
            }
            .sheet(isPresented: $isPresentingPaywall) {
                PaywallSheet(reason: AppStrings.Premium.taskLimitTitle)
            }
        }
    }

    // MARK: - Liste

    private var content: some View {
        List {
            timeRow
            repeatRow
            titleRow

            row {
                SectionLabel(
                    AppStrings.Editor.tasksSection,
                    trailing: "\(draft.tasks.count) / \(premium.gate.taskLimitPerAlarm)"
                )
            }

            ForEach(draft.tasks) { task in
                TaskRowView(task: task)
                    .contentShape(Rectangle())
                    .onTapGesture { taskEditorContext = .edit(task) }
                    .listRowStyling()
            }
            .onMove { source, destination in
                draft = draft.movingTasks(fromOffsets: source, toOffset: destination)
            }
            .onDelete { offsets in
                draft.tasks.remove(atOffsets: offsets)
            }

            row { addTaskArea }

            row { SectionLabel(AppStrings.Editor.alarmSection).padding(.top, Theme.Spacing.sm) }
            row { alarmSettingsCard }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .environment(\.defaultMinListRowHeight, 0)
    }

    // MARK: - Satırlar

    private var timeRow: some View {
        row {
            VStack(spacing: Theme.Spacing.md) {
                Button {
                    withAnimation(.snappy(duration: 0.22)) {
                        isTimePickerExpanded.toggle()
                    }
                } label: {
                    Text(draft.time.displayText)
                        .font(Theme.Typography.hero)
                        .tracking(Theme.Tracking.hero)
                        .monospacedDigit()
                        .foregroundStyle(Theme.Palette.textPrimary)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(draft.time.displayText)
                .accessibilityHint(AppStrings.Accessibility.changeTimeHint)

                if isTimePickerExpanded {
                    DatePicker(
                        "",
                        selection: timeBinding,
                        displayedComponents: .hourAndMinute
                    )
                    .datePickerStyle(.wheel)
                    .labelsHidden()
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.vertical, Theme.Spacing.sm)
        }
    }

    private var repeatRow: some View {
        row {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm + 4) {
                SectionLabel(AppStrings.Editor.repeatSection, trailing: repeatSummary)
                WeekdaySelector(selection: $draft.repeatDays)
            }
            .padding(.bottom, Theme.Spacing.lg)
        }
    }

    private var titleRow: some View {
        row {
            HStack(spacing: Theme.Spacing.sm + 4) {
                Image(systemName: "pencil")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(Theme.Palette.textTertiary)
                TextField(AppStrings.Editor.namePlaceholder, text: $draft.title)
                    .font(Theme.Typography.headline)
                    .foregroundStyle(Theme.Palette.textPrimary)
                    .textInputAutocapitalization(.sentences)
                    .submitLabel(.done)
            }
            .padding(.horizontal, Theme.Spacing.md)
            .frame(height: Theme.Size.row)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .fill(Theme.Gradients.surface)
            )
            .padding(.bottom, Theme.Spacing.lg)
        }
    }

    /// Görev ekleme alanı.
    ///
    /// Üç durum var: ekleyebilir, ücretsiz sınıra takıldı (premium önerilir),
    /// modelin üst sınırına ulaştı (premiumda da eklenemez).
    @ViewBuilder
    private var addTaskArea: some View {
        if premium.gate.canAddTask(currentCount: draft.tasks.count) {
            taskActionButton(
                title: AppStrings.Editor.addTask,
                systemImage: "plus"
            ) {
                taskEditorContext = .add
            }
        } else if draft.tasks.count < Alarm.maxTaskCount {
            taskActionButton(
                title: AppStrings.Editor.addTaskPremium,
                systemImage: "star.fill"
            ) {
                isPresentingPaywall = true
            }
        } else {
            Text(AppStrings.Editor.taskLimitReached)
                .font(Theme.Typography.caption)
                .foregroundStyle(Theme.Palette.textTertiary)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
        }
    }

    private func taskActionButton(
        title: String,
        systemImage: String,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: Theme.Spacing.sm) {
                Image(systemName: systemImage)
                    .font(.system(size: 14, weight: .bold))
                Text(title)
                    .font(Theme.Typography.callout)
            }
            .foregroundStyle(Theme.Palette.accent)
            .frame(maxWidth: .infinity)
            .frame(height: 54)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                    .fill(Theme.Palette.accentFill)
            )
        }
        .buttonStyle(.plain)
    }

    private var alarmSettingsCard: some View {
        VStack(spacing: 0) {
            HStack(spacing: Theme.Spacing.sm + 4) {
                Image(systemName: "speaker.wave.2.fill")
                    .font(.system(size: 15))
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .frame(width: 22)
                Text(AppStrings.Editor.sound)
                    .font(Theme.Typography.body)
                    .foregroundStyle(Theme.Palette.textPrimary)
                Spacer(minLength: Theme.Spacing.sm)
                Text(draft.sound.title)
                    .font(Theme.Typography.subheadline)
                    .foregroundStyle(Theme.Palette.textSecondary)
            }
            .padding(.horizontal, Theme.Spacing.md)
            .frame(height: Theme.Size.row)

            Text(AppStrings.Editor.soundNote)
                .font(Theme.Typography.caption)
                .foregroundStyle(Theme.Palette.textTertiary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.bottom, Theme.Spacing.sm + 4)

            Rectangle()
                .fill(Theme.Palette.separator)
                .frame(height: 1)
                .padding(.leading, Theme.Spacing.md + 22 + Theme.Spacing.sm + 4)

            snoozeRow
        }
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                .fill(Theme.Gradients.surface)
        )
        .padding(.bottom, Theme.Spacing.xl)
    }

    private var snoozeRow: some View {
        VStack(spacing: 0) {
            HStack(spacing: Theme.Spacing.sm + 4) {
                Image(systemName: "zzz")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .frame(width: 22)
                VStack(alignment: .leading, spacing: 1) {
                    Text(AppStrings.Editor.snooze)
                        .font(Theme.Typography.body)
                        .foregroundStyle(Theme.Palette.textPrimary)
                    Text(snoozeCaption)
                        .font(Theme.Typography.caption)
                        .foregroundStyle(Theme.Palette.textTertiary)
                }
                Spacer(minLength: Theme.Spacing.sm)
                Toggle("", isOn: $draft.snooze.isEnabled)
                    .labelsHidden()
                    .tint(Theme.Palette.accent)
                    .accessibilityLabel(AppStrings.Editor.snooze)
            }
            .padding(.horizontal, Theme.Spacing.md)
            .frame(height: 64)

            if draft.snooze.isEnabled {
                stepperRow(
                    title: AppStrings.Editor.snoozeDuration,
                    value: $draft.snooze.durationMinutes,
                    range: SnoozeSetting.durationRange,
                    step: 1,
                    label: AppStrings.Editor.minutes(draft.snooze.durationMinutes)
                )
                stepperRow(
                    title: AppStrings.Editor.snoozeMaxCount,
                    value: $draft.snooze.maxCount,
                    range: SnoozeSetting.maxCountRange,
                    step: 1,
                    label: AppStrings.Editor.times(draft.snooze.maxCount)
                )
            }
        }
    }

    private func stepperRow(
        title: String,
        value: Binding<Int>,
        range: ClosedRange<Int>,
        step: Int,
        label: String
    ) -> some View {
        HStack {
            Text(title)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)
            Spacer(minLength: Theme.Spacing.sm)
            Stepper(value: value, in: range, step: step) {
                Text(label)
                    .font(Theme.Typography.footnoteEmphasized)
                    .foregroundStyle(Theme.Palette.textPrimary)
            }
            .fixedSize()
        }
        .padding(.horizontal, Theme.Spacing.md)
        .frame(height: 48)
    }

    // MARK: - Yardımcılar

    /// Liste satırlarının ortak biçimi — arka plan yok, ayırıcı yok, kenar
    /// boşlukları tek yerden.
    private func row<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        content().listRowStyling()
    }

    private var repeatSummary: String { draft.repeatSummary }

    private var snoozeCaption: String {
        draft.snooze.isEnabled
            ? AppStrings.Editor.snoozeOnCaption(
                minutes: draft.snooze.durationMinutes,
                count: draft.snooze.maxCount
            )
            : AppStrings.Editor.snoozeOffCaption
    }


    /// `TimeOfDay` ile `DatePicker`'ın beklediği `Date` arasında köprü.
    private var timeBinding: Binding<Date> {
        Binding(
            get: {
                Calendar.current.date(
                    bySettingHour: draft.time.hour,
                    minute: draft.time.minute,
                    second: 0,
                    of: Date()
                ) ?? Date()
            },
            set: { newValue in
                let components = Calendar.current.dateComponents(
                    [.hour, .minute],
                    from: newValue
                )
                draft.time = TimeOfDay(
                    hour: components.hour ?? draft.time.hour,
                    minute: components.minute ?? draft.time.minute
                )
            }
        )
    }

    private func apply(_ configuration: TaskConfiguration, for context: TaskEditorContext) {
        switch context {
        case .add:
            guard draft.tasks.count < Alarm.maxTaskCount else { return }
            draft.tasks.append(AlarmTask(configuration: configuration))
        case .edit(let task):
            guard let index = draft.tasks.firstIndex(where: { $0.id == task.id }) else { return }
            draft.tasks[index].configuration = configuration
        }
    }
}

// MARK: - Görev satırı

private struct TaskRowView: View {
    let task: AlarmTask

    var body: some View {
        HStack(spacing: Theme.Spacing.sm + 6) {
            TaskIconBox(kind: task.kind, size: 38)

            VStack(alignment: .leading, spacing: 2) {
                Text(task.kind.title)
                    .font(Theme.Typography.callout)
                    .foregroundStyle(Theme.Palette.textPrimary)
                Text(task.configuration.detailText)
                    .font(Theme.Typography.footnote)
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .lineLimit(1)
            }

            Spacer(minLength: Theme.Spacing.sm)

            // Sürükleme ipucu — sıra numarası yerine. Sıra zaten konumdan
            // okunuyor, rozet gereksiz gürültüydü.
            VStack(spacing: 3.5) {
                ForEach(0..<3, id: \.self) { _ in
                    Capsule()
                        .fill(Theme.Palette.textQuaternary)
                        .frame(width: 15, height: 1.5)
                }
            }
        }
        .padding(.horizontal, Theme.Spacing.md)
        .padding(.vertical, Theme.Spacing.sm + 6)
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                .fill(Theme.Gradients.surface)
        )
    }
}

// MARK: - Görev düzenleyici bağlamı

/// Görev sayfasının neyi düzenlediğini taşır.
enum TaskEditorContext: Identifiable {
    case add
    case edit(AlarmTask)

    var id: String {
        switch self {
        case .add: "add"
        case .edit(let task): task.id.uuidString
        }
    }

    var isNew: Bool {
        if case .add = self { return true }
        return false
    }

    var configuration: TaskConfiguration {
        switch self {
        case .add: .makeDefault(for: .shake)
        case .edit(let task): task.configuration
        }
    }
}

// MARK: - Liste satırı biçimi

private extension View {
    func listRowStyling() -> some View {
        self
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
            .listRowInsets(EdgeInsets(top: 4, leading: Theme.Spacing.md, bottom: 4, trailing: Theme.Spacing.md))
    }
}

#Preview("Yeni") {
    AlarmEditorView(alarm: Alarm(time: TimeOfDay(hour: 7, minute: 0))) { _ in }
        .environment(PremiumModel.preview(isPremium: false))
        .preferredColorScheme(.dark)
}

#Preview("Düzenleme — premium") {
    AlarmEditorView(alarm: Alarm.samples[0], isNew: false) { _ in }
        .environment(PremiumModel.preview(isPremium: true))
        .preferredColorScheme(.dark)
}
