import SwiftUI
import TembelCore

/// Ana sayfa — kurulu alarmların listesi.
struct HomeView: View {
    @Environment(AlarmListModel.self) private var model
    @Environment(PremiumModel.self) private var premium

    @State private var editedAlarm: Alarm?
    @State private var alarmPendingDeletion: Alarm?
    @State private var isPresentingPaywall = false

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.Palette.background.ignoresSafeArea()

                VStack(spacing: 0) {
                    header
                    if let message = model.errorMessage {
                        errorBanner(message)
                    }
                    if model.alarms.isEmpty {
                        emptyState
                    } else {
                        nextAlarmSummary
                        alarmList
                    }
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .sheet(item: $editedAlarm) { alarm in
                AlarmEditorView(
                    alarm: alarm,
                    isNew: !model.alarms.contains { $0.id == alarm.id }
                ) { saved in
                    model.save(saved)
                }
            }
            .sheet(isPresented: $isPresentingPaywall) {
                PaywallSheet(reason: AppStrings.Premium.alarmLimitTitle)
            }
            .confirmationDialog(
                AppStrings.Home.delete,
                isPresented: Binding(
                    get: { alarmPendingDeletion != nil },
                    set: { if !$0 { alarmPendingDeletion = nil } }
                ),
                titleVisibility: .visible
            ) {
                Button(AppStrings.Home.delete, role: .destructive) {
                    if let alarm = alarmPendingDeletion {
                        model.delete(alarm)
                    }
                    alarmPendingDeletion = nil
                }
                Button(AppStrings.Editor.cancel, role: .cancel) {
                    alarmPendingDeletion = nil
                }
            } message: {
                Text(alarmPendingDeletion?.displayTitle ?? "")
            }
        }
    }

    // MARK: - Bölümler

    private var header: some View {
        HStack {
            Text(AppStrings.Home.title)
                .font(Theme.Typography.largeTitle)
                .tracking(Theme.Tracking.largeTitle)
                .foregroundStyle(Theme.Palette.textPrimary)

            Spacer(minLength: Theme.Spacing.md)

            Button(action: addAlarm) {
                Circle()
                    .fill(Theme.Palette.fill)
                    .frame(width: Theme.Size.roundButton, height: Theme.Size.roundButton)
                    .overlay {
                        Image(systemName: "plus")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundStyle(Theme.Palette.accent)
                    }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(AppStrings.Home.addAlarm)
        }
        .padding(.horizontal, Theme.Spacing.lg)
        .padding(.top, Theme.Spacing.sm)
        .padding(.bottom, Theme.Spacing.sm + 2)
    }

    /// "Sonraki alarm 8 sa 42 dk sonra" satırı. Dakikada bir yenilenir.
    private var nextAlarmSummary: some View {
        TimelineView(.periodic(from: .now, by: 60)) { context in
            let next = AlarmScheduler.nextAlarm(among: model.alarms, after: context.date)
            let remaining = next.flatMap {
                RelativeTimeText.timeRemaining(until: $0.date, from: context.date)
            }

            HStack(spacing: 0) {
                Group {
                    if let remaining {
                        Text(AppStrings.Home.nextAlarmPrefix)
                            + Text(remaining).foregroundStyle(Theme.Palette.textPrimary.opacity(0.85))
                    } else {
                        Text(AppStrings.Home.noEnabledAlarm)
                    }
                }
                .font(Theme.Typography.subheadline)
                .foregroundStyle(Theme.Palette.textSecondary)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.bottom, Theme.Spacing.lg)
        }
    }

    private var alarmList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(model.alarms) { alarm in
                    AlarmCardView(
                        alarm: alarm,
                        onToggle: { model.setEnabled($0, for: alarm) },
                        onEdit: { editedAlarm = alarm },
                        onDelete: { alarmPendingDeletion = alarm }
                    )
                }

                if !premium.gate.canAddAlarm(currentCount: model.alarms.count) {
                    limitHint
                }
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.bottom, Theme.Spacing.xl)
        }
        .scrollIndicators(.hidden)
    }

    /// Ücretsiz sınıra ulaşıldığında listenin sonundaki yumuşak hatırlatma.
    ///
    /// Modal açmak yerine yerinde durur: kullanıcı sınırı fark etsin ama
    /// akışı kesilmesin.
    private var limitHint: some View {
        Button {
            isPresentingPaywall = true
        } label: {
            HStack(spacing: Theme.Spacing.sm + 4) {
                Image(systemName: "star.fill")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Theme.Palette.accent)
                Text(AppStrings.Home.limitHint)
                    .font(Theme.Typography.footnote)
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Theme.Palette.textQuaternary)
            }
            .padding(Theme.Spacing.md)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.task, style: .continuous)
                    .fill(Theme.Palette.accentFill)
            )
        }
        .buttonStyle(.plain)
        .padding(.top, Theme.Spacing.xs)
    }

    private var emptyState: some View {
        VStack(spacing: Theme.Spacing.lg + 4) {
            Spacer()

            ZStack {
                Circle()
                    .fill(Theme.Palette.accent.opacity(0.18))
                    .frame(width: 120, height: 120)
                    .blur(radius: 26)
                Image(systemName: "alarm")
                    .font(.system(size: 64, weight: .ultraLight))
                    .foregroundStyle(Theme.Palette.accent)
            }

            VStack(spacing: 10) {
                Text(AppStrings.Home.emptyTitle)
                    .font(Theme.Typography.title)
                    .tracking(Theme.Tracking.title)
                    .foregroundStyle(Theme.Palette.textPrimary)
                Text(AppStrings.Home.emptyMessage)
                    .font(Theme.Typography.subheadline)
                    .foregroundStyle(Theme.Palette.textSecondary)
                    .multilineTextAlignment(.center)
            }

            PrimaryButton(title: AppStrings.Home.emptyAction, systemImage: "plus") {
                addAlarm()
            }
            .fixedSize(horizontal: true, vertical: false)

            Spacer()
            Spacer()
        }
        .padding(.horizontal, Theme.Spacing.xl + 12)
    }

    private func errorBanner(_ message: String) -> some View {
        HStack(alignment: .top, spacing: Theme.Spacing.sm + 2) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(Theme.Palette.accent)
            Text(message)
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textSecondary)
            Spacer(minLength: 0)
        }
        .padding(Theme.Spacing.sm + 4)
        .background(
            RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                .fill(Theme.Palette.surface)
        )
        .padding(.horizontal, Theme.Spacing.lg)
        .padding(.bottom, Theme.Spacing.md)
    }

    // MARK: - Eylemler

    private func addAlarm() {
        guard premium.gate.canAddAlarm(currentCount: model.alarms.count) else {
            isPresentingPaywall = true
            return
        }
        editedAlarm = Alarm(time: TimeOfDay(hour: 7, minute: 0))
    }
}

#Preview("Dolu") {
    HomeView()
        .environment(AlarmListModel.preview())
        .environment(PremiumModel.preview(isPremium: true))
        .preferredColorScheme(.dark)
}

#Preview("Ücretsiz sınır") {
    HomeView()
        .environment(AlarmListModel.preview(alarms: Array(Alarm.samples.prefix(2))))
        .environment(PremiumModel.preview(isPremium: false))
        .preferredColorScheme(.dark)
}

#Preview("Boş") {
    HomeView()
        .environment(AlarmListModel.preview(alarms: []))
        .environment(PremiumModel.preview(isPremium: false))
        .preferredColorScheme(.dark)
}
