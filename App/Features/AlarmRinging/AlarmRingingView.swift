import SwiftUI
import TembelCore

/// Alarm çalarken görünen ekran.
///
/// Görevler sırayla burada yürütülür. Ekran kapatılamaz — kapatmanın tek yolu
/// görevleri bitirmektir. (iOS'un alarm **sesini** susturmasını engelleyemeyiz;
/// engellediğimiz şey alarmın "tamamlandı" sayılması ve takip zincirinin
/// iptal edilmesidir. Bkz. `docs/ios-alarm-constraints.md` § 2.)
struct AlarmRingingView: View {
    @Environment(AlarmSessionModel.self) private var sessionModel

    let motionService: any MotionServicing

    var body: some View {
        ZStack {
            Theme.Palette.background.ignoresSafeArea()

            if let session = sessionModel.session {
                if session.isComplete {
                    completionView
                } else {
                    runningView(session)
                }
            }
        }
        .interactiveDismissDisabled()
    }

    // MARK: - Görevler sürerken

    private func runningView(_ session: AlarmSession) -> some View {
        VStack(spacing: 0) {
            header(session)
            progressBar(session)

            if let task = session.currentTask {
                taskView(for: task)
                    // Görev değiştiğinde ekran sıfırdan kurulmalı; aksi hâlde
                    // önceki görevin sayacı veya girdisi taşınır.
                    .id(task.id)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }

            snoozeArea(session)
        }
    }

    private func header(_ session: AlarmSession) -> some View {
        VStack(spacing: Theme.Spacing.xs) {
            Text(AppStrings.Ringing.wakeUp)
                .font(Theme.Typography.sectionLabel)
                .tracking(Theme.Tracking.brand)
                .foregroundStyle(Theme.Palette.accent)

            Text(session.alarmTime.displayText)
                .font(Theme.Typography.cardTime)
                .tracking(Theme.Tracking.cardTime)
                .monospacedDigit()
                .foregroundStyle(Theme.Palette.textPrimary)

            if !session.alarmTitle.isEmpty {
                Text(session.alarmTitle)
                    .font(Theme.Typography.callout)
                    .foregroundStyle(Theme.Palette.textSecondary)
            }
        }
        .padding(.top, Theme.Spacing.lg)
        .padding(.bottom, Theme.Spacing.lg)
    }

    private func progressBar(_ session: AlarmSession) -> some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text(
                AppStrings.Ringing.taskProgress(
                    current: session.currentTaskNumber ?? session.tasks.count,
                    total: session.tasks.count
                )
            )
            .font(Theme.Typography.sectionLabel)
            .tracking(Theme.Tracking.sectionLabel)
            .foregroundStyle(Theme.Palette.textTertiary)

            HStack(spacing: Theme.Spacing.xs) {
                ForEach(Array(session.tasks.enumerated()), id: \.element.id) { index, _ in
                    Capsule()
                        .fill(
                            index < session.completedCount
                                ? Theme.Palette.accent
                                : Theme.Palette.fill
                        )
                        .frame(height: 4)
                }
            }
        }
        .padding(.horizontal, Theme.Spacing.lg)
    }

    @ViewBuilder
    private func taskView(for task: AlarmTask) -> some View {
        switch task.configuration {
        case .shake(let count):
            ShakeTaskView(target: count, motionService: motionService) {
                complete(task)
            }

        case .math(let difficulty, let questionCount):
            MathTaskView(difficulty: difficulty, questionCount: questionCount) {
                complete(task)
            }

        case .photo(let prompt):
            PhotoTaskView(prompt: prompt) {
                complete(task)
            }
        }
    }

    @ViewBuilder
    private func snoozeArea(_ session: AlarmSession) -> some View {
        VStack(spacing: Theme.Spacing.sm) {
            if session.snooze.isEnabled {
                if session.canSnooze {
                    Button {
                        _ = sessionModel.snooze()
                    } label: {
                        Text(AppStrings.Ringing.snooze)
                            .font(Theme.Typography.callout)
                            .foregroundStyle(Theme.Palette.textSecondary)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(
                                RoundedRectangle(
                                    cornerRadius: Theme.Radius.control,
                                    style: .continuous
                                )
                                .fill(Theme.Palette.fill)
                            )
                    }
                    .buttonStyle(.plain)

                    Text(AppStrings.Ringing.snoozeRemaining(session.remainingSnoozeCount))
                        .font(Theme.Typography.caption)
                        .foregroundStyle(Theme.Palette.textTertiary)
                } else {
                    Text(AppStrings.Ringing.noSnoozeLeft)
                        .font(Theme.Typography.caption)
                        .foregroundStyle(Theme.Palette.textTertiary)
                }
            }
        }
        .padding(.horizontal, Theme.Spacing.md)
        .padding(.bottom, Theme.Spacing.lg)
    }

    // MARK: - Tamamlandı

    private var completionView: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer()

            ZStack {
                Circle()
                    .fill(Theme.Palette.accent.opacity(0.18))
                    .frame(width: 140, height: 140)
                    .blur(radius: 30)
                Circle()
                    .fill(Theme.Palette.accent)
                    .frame(width: 96, height: 96)
                    .overlay {
                        Image(systemName: "checkmark")
                            .font(.system(size: 42, weight: .bold))
                            .foregroundStyle(Theme.Palette.background)
                    }
            }

            VStack(spacing: Theme.Spacing.sm) {
                Text(AppStrings.Ringing.completedTitle)
                    .font(Theme.Typography.title)
                    .tracking(Theme.Tracking.title)
                    .foregroundStyle(Theme.Palette.textPrimary)
                Text(AppStrings.Ringing.completedMessage)
                    .font(Theme.Typography.subheadline)
                    .foregroundStyle(Theme.Palette.textSecondary)
            }

            Spacer()

            PrimaryButton(title: AppStrings.Ringing.dismiss) {
                sessionModel.dismiss()
            }
            .padding(.horizontal, Theme.Spacing.md)
            .padding(.bottom, Theme.Spacing.lg)
        }
    }

    private func complete(_ task: AlarmTask) {
        sessionModel.completeCurrentTask(taskID: task.id)
    }
}

#Preview {
    AlarmRingingView(motionService: PreviewMotionService())
        .environment(AlarmSessionModel.preview(alarm: Alarm.samples[0]))
        .preferredColorScheme(.dark)
}
