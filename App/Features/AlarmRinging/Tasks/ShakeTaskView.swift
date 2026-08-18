import SwiftUI
import TembelCore

/// Sallama görevi.
///
/// Sayma mantığı `ShakeDetector`'da; bu ekran yalnızca sensör akışını ona
/// bağlar ve ilerlemeyi gösterir.
struct ShakeTaskView: View {

    let target: Int
    let motionService: any MotionServicing
    let onComplete: () -> Void

    @State private var detector: ShakeDetector
    @State private var hasReportedCompletion = false
    @State private var pulse = false

    init(target: Int, motionService: any MotionServicing, onComplete: @escaping () -> Void) {
        self.target = target
        self.motionService = motionService
        self.onComplete = onComplete
        _detector = State(initialValue: ShakeDetector(target: target))
    }

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer()

            if motionService.isAvailable {
                counter
                Text(AppStrings.ShakeTask.instruction)
                    .font(Theme.Typography.headline)
                    .foregroundStyle(Theme.Palette.textSecondary)
            } else {
                unavailableState
            }

            Spacer()

            #if targetEnvironment(simulator)
            // Simulator'da ivmeölçer yoktur. Bu düğme yalnızca Simulator
            // derlemelerinde vardır; gerçek cihaza asla gitmez.
            Button(AppStrings.ShakeTask.simulatorTap) {
                registerSyntheticShake()
            }
            .font(Theme.Typography.footnote)
            .foregroundStyle(Theme.Palette.textTertiary)
            #endif
        }
        .padding(.horizontal, Theme.Spacing.lg)
        .task {
            guard motionService.isAvailable else { return }
            for await sample in motionService.samples() {
                if detector.process(sample) {
                    pulse.toggle()
                }
                if detector.isComplete { break }
            }
            reportCompletionIfNeeded()
        }
        .onChange(of: detector.count) { _, _ in
            reportCompletionIfNeeded()
        }
    }

    private var counter: some View {
        ZStack {
            Circle()
                .stroke(Theme.Palette.fill, lineWidth: 10)
            Circle()
                .trim(from: 0, to: detector.progress)
                .stroke(
                    Theme.Palette.accent,
                    style: StrokeStyle(lineWidth: 10, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(.snappy(duration: 0.2), value: detector.progress)

            Text(AppStrings.ShakeTask.progress(detector.count, target))
                .font(Theme.Typography.numeric)
                .monospacedDigit()
                .foregroundStyle(Theme.Palette.textPrimary)
        }
        .frame(width: 220, height: 220)
        .scaleEffect(pulse ? 1.04 : 1)
        .animation(.snappy(duration: 0.12), value: pulse)
    }

    private var unavailableState: some View {
        VStack(spacing: Theme.Spacing.sm + 4) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 40, weight: .light))
                .foregroundStyle(Theme.Palette.accent)
            Text(AppStrings.ShakeTask.unavailable)
                .font(Theme.Typography.headline)
                .foregroundStyle(Theme.Palette.textPrimary)
            Text(AppStrings.ShakeTask.unavailableHelp)
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textSecondary)
                .multilineTextAlignment(.center)
        }
    }

    private func reportCompletionIfNeeded() {
        guard detector.isComplete, !hasReportedCompletion else { return }
        hasReportedCompletion = true
        onComplete()
    }

    #if targetEnvironment(simulator)
    private func registerSyntheticShake() {
        let now = Date().timeIntervalSince1970
        detector.process(MotionSample(x: 0.1, y: 0, z: 0, timestamp: now))
        if detector.process(MotionSample(x: 3.0, y: 0, z: 0, timestamp: now + 0.5)) {
            pulse.toggle()
        }
    }
    #endif
}

#Preview {
    ZStack {
        Theme.Palette.background.ignoresSafeArea()
        ShakeTaskView(target: 10, motionService: PreviewMotionService()) {}
    }
    .preferredColorScheme(.dark)
}
