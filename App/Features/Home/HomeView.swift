import SwiftUI
import TembelCore

/// Ana sayfa — kurulu alarmların listesi.
struct HomeView: View {
    @Environment(AlarmListModel.self) private var model

    /// Düzenleyicide açık olan alarm. `nil` ise düzenleyici kapalı.
    @State private var editedAlarm: Alarm?
    @State private var alarmPendingDeletion: Alarm?

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
        HStack(alignment: .bottom) {
            VStack(alignment: .leading, spacing: 2) {
                Text(AppStrings.Brand.name.uppercased())
                    .font(Theme.Typography.sectionLabel)
                    .tracking(Theme.Tracking.brand)
                    .foregroundStyle(Theme.Palette.accent)
                Text(AppStrings.Home.title)
                    .font(Theme.Typography.largeTitle)
                    .tracking(Theme.Tracking.largeTitle)
                    .foregroundStyle(Theme.Palette.textPrimary)
            }
            Spacer(minLength: Theme.Spacing.md)
            RoundAccentButton(
                systemImage: "plus",
                accessibilityLabel: AppStrings.Home.addAlarm
            ) {
                editedAlarm = Alarm(time: defaultTime)
            }
        }
        .padding(.horizontal, Theme.Spacing.md)
        .padding(.top, Theme.Spacing.sm)
        .padding(.bottom, Theme.Spacing.lg)
    }

    /// "Sonraki alarm 8 saat 42 dakika sonra" satırı.
    ///
    /// Dakikada bir yenilenir; geri sayımın ekranda donup kalmaması için
    /// `TimelineView` kullanılıyor.
    private var nextAlarmSummary: some View {
        TimelineView(.periodic(from: .now, by: 60)) { context in
            let next = AlarmScheduler.nextAlarm(among: model.alarms, after: context.date)
            let remaining = next.flatMap {
                RelativeTimeText.timeRemaining(until: $0.date, from: context.date)
            }

            HStack(spacing: Theme.Spacing.sm) {
                Circle()
                    .fill(remaining == nil ? Theme.Palette.textQuaternary : Theme.Palette.accent)
                    .frame(width: 6, height: 6)

                Group {
                    if let remaining {
                        Text(AppStrings.Home.nextAlarmPrefix)
                            + Text(remaining).foregroundStyle(Theme.Palette.textPrimary)
                    } else {
                        Text(AppStrings.Home.noEnabledAlarm)
                    }
                }
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textSecondary)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, Theme.Spacing.md)
            .padding(.bottom, Theme.Spacing.md + 4)
        }
    }

    private var alarmList: some View {
        ScrollView {
            LazyVStack(spacing: 10) {
                ForEach(model.alarms) { alarm in
                    AlarmCardView(
                        alarm: alarm,
                        onToggle: { model.setEnabled($0, for: alarm) },
                        onEdit: { editedAlarm = alarm },
                        onDelete: { alarmPendingDeletion = alarm }
                    )
                }
            }
            .padding(.horizontal, Theme.Spacing.md)
            .padding(.bottom, Theme.Spacing.xl)
        }
    }

    private var emptyState: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer()

            ZStack {
                Circle()
                    .fill(Theme.Palette.accent.opacity(0.18))
                    .frame(width: 132, height: 132)
                    .blur(radius: 28)
                Circle()
                    .fill(Theme.Palette.surface)
                    .frame(width: 108, height: 108)
                    .overlay(Circle().strokeBorder(Theme.Palette.separator, lineWidth: 1))
                    .overlay {
                        Image(systemName: "alarm")
                            .font(.system(size: 44, weight: .light))
                            .foregroundStyle(Theme.Palette.accent)
                    }
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

            PrimaryButton(
                title: AppStrings.Home.emptyAction,
                systemImage: "plus"
            ) {
                editedAlarm = Alarm(time: defaultTime)
            }
            .fixedSize(horizontal: true, vertical: false)

            Spacer()
            Spacer()
        }
        .padding(.horizontal, Theme.Spacing.xl + 8)
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
        .cardBackground(cornerRadius: Theme.Radius.control)
        .padding(.horizontal, Theme.Spacing.md)
        .padding(.bottom, Theme.Spacing.md)
    }

    /// Yeni alarmın açılış saati — sabah 7:00, en sık kurulan saat.
    private var defaultTime: TimeOfDay {
        TimeOfDay(hour: 7, minute: 0)
    }
}

#Preview("Dolu") {
    HomeView()
        .environment(AlarmListModel.preview())
        .preferredColorScheme(.dark)
}

#Preview("Boş") {
    HomeView()
        .environment(AlarmListModel.preview(alarms: []))
        .preferredColorScheme(.dark)
}
