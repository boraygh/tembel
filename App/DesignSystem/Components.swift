import SwiftUI
import TembelCore

/// Bölüm başlığı — büyük harf, geniş harf aralığı, soluk.
struct SectionLabel: View {
    let text: String
    var trailing: String?

    init(_ text: String, trailing: String? = nil) {
        self.text = text
        self.trailing = trailing
    }

    var body: some View {
        HStack {
            Text(text.uppercased())
                .font(Theme.Typography.sectionLabel)
                .tracking(Theme.Tracking.sectionLabel)
                .foregroundStyle(Theme.Palette.textTertiary)
            Spacer(minLength: Theme.Spacing.sm)
            if let trailing {
                Text(trailing)
                    .font(Theme.Typography.footnoteEmphasized)
                    .foregroundStyle(Theme.Palette.accent)
            }
        }
    }
}

/// Görev türünün ikonunu taşıyan kare kutu.
struct TaskIconBox: View {
    let kind: TaskKind
    var size: CGFloat = Theme.Size.iconBox
    var isProminent = true

    var body: some View {
        RoundedRectangle(cornerRadius: Theme.Radius.iconBox, style: .continuous)
            .fill(isProminent ? Theme.Palette.surfaceElevated : Theme.Palette.fill)
            .frame(width: size, height: size)
            .overlay {
                Image(systemName: kind.symbolName)
                    .font(.system(size: size * 0.45, weight: .semibold))
                    .foregroundStyle(isProminent ? Theme.Palette.accent : Theme.Palette.textSecondary)
            }
    }
}

/// Düzenleyicideki tekrar günü seçici — dokunulabilir.
struct WeekdaySelector: View {
    @Binding var selection: Set<Weekday>

    var body: some View {
        HStack(spacing: Theme.Spacing.xs + 2) {
            ForEach(Weekday.orderedMondayFirst) { day in
                let isOn = selection.contains(day)
                Button {
                    toggle(day)
                } label: {
                    Text(day.shortLabel)
                        .font(Theme.Typography.chip)
                        .foregroundStyle(isOn ? Theme.Palette.background : Theme.Palette.textTertiary)
                        .frame(maxWidth: .infinity)
                        .frame(height: Theme.Size.dayChip)
                        // Capsule, Circle değil: genişlik ekrana göre değişir,
                        // Circle bu durumda elipse dönüşür.
                        .background(
                            Capsule().fill(isOn ? Theme.Palette.accent : Theme.Palette.surface)
                        )
                }
                .buttonStyle(.plain)
                .accessibilityLabel(day.shortLabel)
                .accessibilityAddTraits(isOn ? [.isSelected] : [])
            }
        }
    }

    private func toggle(_ day: Weekday) {
        if selection.contains(day) {
            selection.remove(day)
        } else {
            selection.insert(day)
        }
    }
}

/// Alarm kartındaki tekrar günü göstergesi — okunur, dokunulmaz.
struct WeekdayIndicator: View {
    let selection: Set<Weekday>
    var isDimmed = false

    var body: some View {
        HStack(spacing: Theme.Spacing.xs) {
            ForEach(Weekday.orderedMondayFirst) { day in
                let isOn = selection.contains(day)
                Text(day.shortLabel)
                    .font(Theme.Typography.chipSmall)
                    .foregroundStyle(foreground(isOn: isOn))
                    .frame(width: 30, height: 24)
                    .background(
                        RoundedRectangle(cornerRadius: Theme.Spacing.sm, style: .continuous)
                            .fill(background(isOn: isOn))
                    )
            }
        }
        .accessibilityElement(children: .combine)
    }

    private func foreground(isOn: Bool) -> Color {
        guard isOn else { return Theme.Palette.textQuaternary }
        return isDimmed ? Theme.Palette.textSecondary : Theme.Palette.accent
    }

    private func background(isOn: Bool) -> Color {
        guard isOn else { return .clear }
        return isDimmed ? Theme.Palette.fill : Theme.Palette.accent.opacity(0.12)
    }
}

/// Vurgu renginde, ekran genişliğinde ana buton.
struct PrimaryButton: View {
    let title: String
    var systemImage: String?
    var isEnabled = true
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: Theme.Spacing.sm + 2) {
                if let systemImage {
                    Image(systemName: systemImage)
                        .font(.system(size: 17, weight: .bold))
                }
                Text(title)
                    .font(Theme.Typography.bodyEmphasized)
            }
            .foregroundStyle(Theme.Palette.background)
            .frame(maxWidth: .infinity)
            .frame(height: Theme.Size.primaryButton)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control + 2, style: .continuous)
                    .fill(Theme.Palette.accent)
            )
        }
        .buttonStyle(.plain)
        .opacity(isEnabled ? 1 : 0.4)
        .disabled(!isEnabled)
    }
}

/// Yuvarlak, ikonlu vurgu butonu — ana sayfadaki "+" gibi.
struct RoundAccentButton: View {
    let systemImage: String
    let accessibilityLabel: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Circle()
                .fill(Theme.Palette.accent)
                .frame(width: Theme.Size.roundButton, height: Theme.Size.roundButton)
                .overlay {
                    Image(systemName: systemImage)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundStyle(Theme.Palette.background)
                }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityLabel)
    }
}

/// Kart görünümlü grup — koyu yüzey, yumuşak kenarlık.
struct CardBackground: ViewModifier {
    var cornerRadius: CGFloat = Theme.Radius.card

    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .fill(Theme.Palette.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(Theme.Palette.separator, lineWidth: 1)
            )
    }
}

extension View {
    func cardBackground(cornerRadius: CGFloat = Theme.Radius.card) -> some View {
        modifier(CardBackground(cornerRadius: cornerRadius))
    }
}
