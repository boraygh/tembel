import SwiftUI
import TembelCore

/// Görev ekleme ve düzenleme sayfası.
///
/// Her görev türünün ayarı ayrı `@State`'te tutulur; kullanıcı türler arasında
/// gezerken önceki seçimleri kaybolmaz.
struct TaskEditorView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(PremiumModel.self) private var premium

    @State private var isPresentingPaywall = false
    @State private var kind: TaskKind
    @State private var shakeCount: Int
    @State private var difficulty: MathDifficulty
    @State private var questionCount: Int
    @State private var prompt: String

    private let isNew: Bool
    private let onCommit: (TaskConfiguration) -> Void

    init(
        configuration: TaskConfiguration,
        isNew: Bool,
        onCommit: @escaping (TaskConfiguration) -> Void
    ) {
        self.isNew = isNew
        self.onCommit = onCommit

        _kind = State(initialValue: configuration.kind)

        // Düzenlenen türün değerleri gelen ayardan, diğerleri varsayılandan.
        var shake = 10
        var mathDifficulty = MathDifficulty.medium
        var mathQuestions = 1
        var photoPrompt = ""

        switch configuration {
        case .shake(let count):
            shake = count
        case .math(let level, let count):
            mathDifficulty = level
            mathQuestions = count
        case .photo(let text):
            photoPrompt = text
        }

        _shakeCount = State(initialValue: shake)
        _difficulty = State(initialValue: mathDifficulty)
        _questionCount = State(initialValue: mathQuestions)
        _prompt = State(initialValue: photoPrompt)
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Gradients.sheet.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: Theme.Spacing.lg) {
                        typeSelector

                        VStack(alignment: .leading, spacing: Theme.Spacing.sm + 4) {
                            SectionLabel(AppStrings.TaskEditor.settingSection)
                            settingCard
                        }
                    }
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.sm)
                    .padding(.bottom, Theme.Spacing.xl)
                }
            }
            .navigationTitle(isNew ? AppStrings.TaskEditor.addTitle : AppStrings.TaskEditor.editTitle)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(AppStrings.TaskEditor.cancel) { dismiss() }
                        .foregroundStyle(Theme.Palette.textSecondary)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isNew ? AppStrings.TaskEditor.add : AppStrings.TaskEditor.done) {
                        onCommit(configuration.normalized())
                        dismiss()
                    }
                    .font(Theme.Typography.bodyEmphasized)
                    .foregroundStyle(Theme.Palette.accent)
                    .disabled(!isValid)
                }
            }
            .sheet(isPresented: $isPresentingPaywall) {
                PaywallSheet(reason: AppStrings.Premium.photoLockedTitle)
            }
        }
    }

    // MARK: - Tür seçimi

    private var typeSelector: some View {
        VStack(spacing: Theme.Spacing.sm) {
            ForEach(TaskKind.allCases) { candidate in
                let isLocked = !premium.gate.isAvailable(candidate)
                let isSelected = candidate == kind && !isLocked

                Button {
                    if isLocked {
                        isPresentingPaywall = true
                    } else {
                        withAnimation(.snappy(duration: 0.18)) { kind = candidate }
                    }
                } label: {
                    HStack(spacing: Theme.Spacing.sm + 6) {
                        TaskIconBox(
                            kind: candidate,
                            size: Theme.Size.iconBoxLarge,
                            tint: isSelected ? Theme.Palette.accent : Theme.Palette.textSecondary,
                            background: isSelected
                                ? Theme.Palette.accent.opacity(0.16)
                                : Theme.Palette.fill
                        )

                        VStack(alignment: .leading, spacing: 3) {
                            HStack(spacing: Theme.Spacing.sm) {
                                Text(candidate.title)
                                    .font(Theme.Typography.bodyEmphasized)
                                    .foregroundStyle(Theme.Palette.textPrimary)
                                if isLocked {
                                    premiumBadge
                                }
                            }
                            Text(candidate.summary)
                                .font(Theme.Typography.footnote)
                                .foregroundStyle(Theme.Palette.textSecondary)
                                .multilineTextAlignment(.leading)
                        }

                        Spacer(minLength: Theme.Spacing.sm)

                        if isSelected {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 22))
                                .foregroundStyle(Theme.Palette.accent)
                        }
                    }
                    .padding(Theme.Spacing.md)
                    .background(
                        RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                            .fill(isSelected ? Theme.Palette.accentFill : Theme.Palette.surface)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                            .strokeBorder(
                                isSelected ? Theme.Palette.accentBorder : .clear,
                                lineWidth: 1
                            )
                    )
                    .opacity(isLocked ? 0.62 : 1)
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(isSelected ? [.isSelected] : [])
            }
        }
    }

    private var premiumBadge: some View {
        HStack(spacing: 4) {
            Image(systemName: "lock.fill")
                .font(.system(size: 8, weight: .bold))
            Text(AppStrings.Editor.premiumBadge)
                .font(Theme.Typography.chipSmall)
        }
        .foregroundStyle(Theme.Palette.accent)
        .padding(.horizontal, 7)
        .padding(.vertical, 3)
        .background(Capsule().fill(Theme.Palette.accentFill))
    }

    // MARK: - Ayar

    @ViewBuilder
    private var settingCard: some View {
        switch kind {
        case .shake: shakeSetting
        case .math: mathSetting
        case .photo: photoSetting
        }
    }

    private var shakeSetting: some View {
        VStack(spacing: Theme.Spacing.md) {
            Text(AppStrings.TaskEditor.shakeQuestion)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)

            HStack(spacing: Theme.Spacing.lg) {
                counterButton(systemImage: "minus", isProminent: false) {
                    shakeCount = max(TaskConfiguration.shakeCountRange.lowerBound, shakeCount - 1)
                }
                Text("\(shakeCount)")
                    .font(Theme.Typography.numeric)
                    .monospacedDigit()
                    .foregroundStyle(Theme.Palette.textPrimary)
                    .frame(minWidth: 92)
                counterButton(systemImage: "plus", isProminent: true) {
                    shakeCount = min(TaskConfiguration.shakeCountRange.upperBound, shakeCount + 1)
                }
            }

            HStack(spacing: 6) {
                ForEach([5, 10, 25, 50], id: \.self) { preset in
                    let isSelected = preset == shakeCount
                    Button {
                        shakeCount = preset
                    } label: {
                        Text("\(preset)")
                            .font(Theme.Typography.chip)
                            .foregroundStyle(isSelected ? Theme.Palette.background : Theme.Palette.textSecondary)
                            .padding(.horizontal, Theme.Spacing.md - 2)
                            .padding(.vertical, 7)
                            .background(
                                Capsule().fill(isSelected ? Theme.Palette.accent : Theme.Palette.fill)
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, Theme.Spacing.lg)
        .padding(.horizontal, Theme.Spacing.md)
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                .fill(Theme.Gradients.surface)
        )
    }

    private var mathSetting: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                Text(AppStrings.TaskEditor.mathDifficulty)
                    .font(Theme.Typography.subheadline)
                    .foregroundStyle(Theme.Palette.textSecondary)
                Picker(AppStrings.TaskEditor.mathDifficulty, selection: $difficulty) {
                    ForEach(MathDifficulty.allCases) { level in
                        Text(level.title).tag(level)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
            }

            Rectangle()
                .fill(Theme.Palette.separator)
                .frame(height: 1)

            HStack {
                Text(AppStrings.TaskEditor.mathQuestionCount)
                    .font(Theme.Typography.subheadline)
                    .foregroundStyle(Theme.Palette.textSecondary)
                Spacer(minLength: Theme.Spacing.sm)
                Stepper(
                    value: $questionCount,
                    in: TaskConfiguration.mathQuestionCountRange,
                    step: 1
                ) {
                    Text("\(questionCount)")
                        .font(Theme.Typography.bodyEmphasized)
                        .monospacedDigit()
                        .foregroundStyle(Theme.Palette.textPrimary)
                }
                .fixedSize()
            }
        }
        .padding(Theme.Spacing.md)
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                .fill(Theme.Gradients.surface)
        )
    }

    private var photoSetting: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm + 4) {
            Text(AppStrings.TaskEditor.photoPrompt)
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)

            TextField(
                AppStrings.TaskEditor.photoPromptPlaceholder,
                text: $prompt,
                axis: .vertical
            )
            .font(Theme.Typography.body)
            .foregroundStyle(Theme.Palette.textPrimary)
            .lineLimit(1...3)
            .textInputAutocapitalization(.sentences)
            .padding(Theme.Spacing.sm + 4)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .fill(Theme.Palette.surfaceElevated)
            )

            Text(AppStrings.TaskEditor.photoPromptHelp)
                .font(Theme.Typography.caption)
                .foregroundStyle(Theme.Palette.textTertiary)
        }
        .padding(Theme.Spacing.md)
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                .fill(Theme.Gradients.surface)
        )
    }

    private func counterButton(
        systemImage: String,
        isProminent: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            Circle()
                .fill(isProminent ? Theme.Palette.accent : Theme.Palette.fill)
                .frame(width: Theme.Size.iconBoxLarge, height: Theme.Size.iconBoxLarge)
                .overlay {
                    Image(systemName: systemImage)
                        .font(.system(size: 17, weight: .bold))
                        .foregroundStyle(isProminent ? Theme.Palette.background : Theme.Palette.textPrimary)
                }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(
            systemImage == "plus"
                ? AppStrings.Accessibility.increase
                : AppStrings.Accessibility.decrease
        )
    }

    // MARK: - Durum

    private var configuration: TaskConfiguration {
        switch kind {
        case .shake: .shake(count: shakeCount)
        case .math: .math(difficulty: difficulty, questionCount: questionCount)
        case .photo: .photo(prompt: prompt)
        }
    }

    /// Fotoğraf görevi boş açıklamayla eklenirse alarm çaldığında kullanıcı ne
    /// yapacağını bilemez — bu yüzden ekleme engellenir.
    private var isValid: Bool {
        // Kilitli bir tür seçili kalmışsa eklemeye izin verme.
        guard premium.gate.isAvailable(kind) else { return false }
        if case .photo(let text) = configuration {
            return !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
        return true
    }
}

#Preview("Ekle — ücretsiz") {
    TaskEditorView(configuration: .makeDefault(for: .shake), isNew: true) { _ in }
        .environment(PremiumModel.preview(isPremium: false))
        .preferredColorScheme(.dark)
}

#Preview("Fotoğraf — premium") {
    TaskEditorView(configuration: .photo(prompt: "Kahve makinesi"), isNew: false) { _ in }
        .environment(PremiumModel.preview(isPremium: true))
        .preferredColorScheme(.dark)
}
