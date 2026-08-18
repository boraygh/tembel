import SwiftUI
import TembelCore

/// Matematik görevi.
///
/// Soru üretimi ve cevap kontrolü `TembelCore`'da; bu ekran yalnızca gösterim
/// ve giriş. Sistem klavyesi yerine kendi tuş takımı kullanılıyor: sabahın
/// köründe klavye açılış animasyonunu beklemek ve küçük tuşlara isabet etmeye
/// çalışmak gereksiz sürtünme yaratıyor.
struct MathTaskView: View {

    let onComplete: () -> Void

    @State private var questions: [MathQuestion]
    @State private var index = 0
    @State private var input = ""
    @State private var isWrong = false

    init(
        difficulty: MathDifficulty,
        questionCount: Int,
        onComplete: @escaping () -> Void
    ) {
        self.onComplete = onComplete
        _questions = State(
            initialValue: MathQuestionGenerator(difficulty: difficulty)
                .makeQuestions(count: questionCount)
        )
    }

    private var currentQuestion: MathQuestion? {
        questions.indices.contains(index) ? questions[index] : nil
    }

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer(minLength: 0)

            if let question = currentQuestion {
                questionArea(question)
            }

            Spacer(minLength: 0)

            keypad
        }
        .padding(.horizontal, Theme.Spacing.md)
        .onAppear {
            // Savunma amaçlı: soru üretilemediyse görevde kilitlenme olmasın.
            if questions.isEmpty { onComplete() }
        }
    }

    private func questionArea(_ question: MathQuestion) -> some View {
        VStack(spacing: Theme.Spacing.md) {
            let progressText = AppStrings.MathTask.questionProgress(
                current: index + 1,
                total: questions.count
            )
            if !progressText.isEmpty {
                Text(progressText)
                    .font(Theme.Typography.sectionLabel)
                    .tracking(Theme.Tracking.sectionLabel)
                    .foregroundStyle(Theme.Palette.textTertiary)
            }

            Text(question.promptText)
                .font(Theme.Typography.numeric)
                .monospacedDigit()
                .foregroundStyle(Theme.Palette.textPrimary)

            answerField
        }
    }

    private var answerField: some View {
        Text(input.isEmpty ? " " : input)
            .font(Theme.Typography.numeric)
            .monospacedDigit()
            .foregroundStyle(isWrong ? Theme.Palette.accent : Theme.Palette.textPrimary)
            .frame(minWidth: 160)
            .padding(.vertical, Theme.Spacing.sm + 4)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .fill(Theme.Palette.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .strokeBorder(
                        isWrong ? Theme.Palette.accent : Theme.Palette.separator,
                        lineWidth: 1
                    )
            )
            .overlay(alignment: .bottom) {
                if isWrong {
                    Text(AppStrings.MathTask.wrongAnswer)
                        .font(Theme.Typography.caption)
                        .foregroundStyle(Theme.Palette.accent)
                        .offset(y: 22)
                }
            }
            .animation(.snappy(duration: 0.15), value: isWrong)
    }

    private var keypad: some View {
        Grid(horizontalSpacing: Theme.Spacing.sm + 2, verticalSpacing: Theme.Spacing.sm + 2) {
            ForEach(Self.keypadRows, id: \.self) { row in
                GridRow {
                    ForEach(row, id: \.self) { key in
                        keyButton(key)
                    }
                }
            }
        }
        .padding(.bottom, Theme.Spacing.md)
    }

    @ViewBuilder
    private func keyButton(_ key: String) -> some View {
        if key.isEmpty {
            Color.clear.frame(height: 62)
        } else {
            Button {
                handle(key)
            } label: {
                Group {
                    if key == Self.deleteKey {
                        Image(systemName: "delete.left")
                            .font(.system(size: 22, weight: .medium))
                    } else {
                        Text(key)
                            .font(Theme.Typography.title)
                    }
                }
                .foregroundStyle(Theme.Palette.textPrimary)
                .frame(maxWidth: .infinity)
                .frame(height: 62)
                .background(
                    RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                        .fill(Theme.Palette.surface)
                )
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Giriş

    private static let deleteKey = "delete"
    private static let keypadRows: [[String]] = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["", "0", deleteKey]
    ]

    private func handle(_ key: String) {
        guard !isWrong else { return }

        if key == Self.deleteKey {
            if !input.isEmpty { input.removeLast() }
            return
        }

        // Aşırı uzun girişi engelle — cevap hiçbir seviyede bu kadar uzun olmaz.
        guard input.count < 6 else { return }
        input.append(key)
        evaluate()
    }

    /// Her tuşta kontrol eder; doğru cevaba ulaşıldığı anda ilerler.
    /// Ayrı bir "onayla" tuşu yok — sabah bir dokunuş bile fazladır.
    private func evaluate() {
        guard let question = currentQuestion else { return }

        if question.isCorrect(input) {
            advance()
            return
        }

        // Girilen sayı cevabın uzunluğuna ulaştıysa ve hâlâ tutmuyorsa yanlış.
        if input.count >= String(question.answer).count {
            markWrong()
        }
    }

    private func advance() {
        input = ""
        if index + 1 >= questions.count {
            onComplete()
        } else {
            index += 1
        }
    }

    private func markWrong() {
        isWrong = true
        Task {
            try? await Task.sleep(for: .milliseconds(600))
            input = ""
            isWrong = false
        }
    }
}

#Preview {
    ZStack {
        Theme.Gradients.page.ignoresSafeArea()
        MathTaskView(difficulty: .medium, questionCount: 2) {}
    }
    .preferredColorScheme(.dark)
}
