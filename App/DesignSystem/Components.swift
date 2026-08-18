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
    var tint: Color = Theme.Palette.accent
    var background: Color = Theme.Palette.fill

    var body: some View {
        RoundedRectangle(cornerRadius: size * 0.3, style: .continuous)
            .fill(background)
            .frame(width: size, height: size)
            .overlay {
                Image(systemName: kind.symbolName)
                    .font(.system(size: size * 0.45, weight: .semibold))
                    .foregroundStyle(tint)
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
                        // Seçilmeyen günler zeminsiz: yedi dolu kutucuk
                        // gereksiz görsel gürültü yaratıyordu.
                        .background {
                            if isOn {
                                Capsule()
                                    .fill(Theme.Gradients.ember)
                                    .shadow(color: Theme.Shadow.ember, radius: 8, y: 3)
                            }
                        }
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
                    .fill(Theme.Gradients.ember)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.Radius.control + 2, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.3), .clear],
                            startPoint: .top,
                            endPoint: .bottom
                        ),
                        lineWidth: 1
                    )
            )
            // Gölge butonun kendi renginde: nötr gri gölge yerine sıcak bir
            // ışık halesi, düğmeyi yüzeyden kaldırıyor.
            .shadow(color: Theme.Shadow.ember, radius: 16, y: 8)
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
                .fill(Theme.Gradients.ember)
                .frame(width: Theme.Size.roundButton, height: Theme.Size.roundButton)
                .shadow(color: Theme.Shadow.ember, radius: 12, y: 5)
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

/// Kart malzemesi: gradyan yüzey + üst kenarda ışık çizgisi + yumuşak gölge.
///
/// Bu üçü birlikte kartı ekranın üstünde duruyormuş gibi gösteriyor. Düz
/// dolgu tek başına "premium" durmuyor; asıl fark bu 1px kenar ışığında.
struct MaterialCard: ViewModifier {
    var cornerRadius: CGFloat = Theme.Radius.cardLarge

    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .fill(Theme.Gradients.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(Theme.Gradients.edgeHighlight, lineWidth: 1)
            )
            .shadow(color: Theme.Shadow.card, radius: 16, y: 8)
    }
}

extension View {
    func materialCard(cornerRadius: CGFloat = Theme.Radius.cardLarge) -> some View {
        modifier(MaterialCard(cornerRadius: cornerRadius))
    }
}
