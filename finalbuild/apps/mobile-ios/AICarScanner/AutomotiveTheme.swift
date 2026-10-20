import SwiftUI

// Shared visual language for the native automotive diagnostics screens.
// The reference mockup is a design guide; actual telemetry and AI confidence
// values continue to come from the ViewModel/backend, never from decorative UI.
enum AutomotivePalette {
    static let navy = Color(red: 6.0 / 255, green: 17.0 / 255, blue: 33.0 / 255)
    static let midnight = Color(red: 10.0 / 255, green: 28.0 / 255, blue: 56.0 / 255)
    static let panel = Color(red: 13.0 / 255, green: 31.0 / 255, blue: 62.0 / 255)
    static let electricBlue = Color(red: 24.0 / 255, green: 138.0 / 255, blue: 255.0 / 255)
    static let cyan = Color(red: 40.0 / 255, green: 213.0 / 255, blue: 255.0 / 255)
    static let violet = Color(red: 156.0 / 255, green: 116.0 / 255, blue: 255.0 / 255)
    static let positive = Color(red: 28.0 / 255, green: 211.0 / 255, blue: 150.0 / 255)
    static let negative = Color(red: 255.0 / 255, green: 92.0 / 255, blue: 114.0 / 255)
    static let incomplete = Color(red: 255.0 / 255, green: 198.0 / 255, blue: 99.0 / 255)

    static func background(dark: Bool) -> LinearGradient {
        LinearGradient(
            colors: dark
                ? [navy, midnight, navy]
                : [Color(red: 0.94, green: 0.97, blue: 1.0), .white],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    static func resultColor(_ result: String) -> Color {
        switch result.uppercased() {
        case "PASS": return positive
        case "FAIL": return negative
        default: return incomplete
        }
    }
}

struct AutomotiveCardStyle: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme
    var compact: Bool = false

    func body(content: Content) -> some View {
        let isDark = colorScheme == .dark
        let radius: CGFloat = compact ? 12 : 18
        let shape = RoundedRectangle(cornerRadius: radius, style: .continuous)
        content
            .background(shape.fill(isDark ? AutomotivePalette.panel : .white))
            .overlay(
                shape.strokeBorder(
                    isDark ? AutomotivePalette.electricBlue.opacity(0.50)
                           : AutomotivePalette.electricBlue.opacity(0.22),
                    lineWidth: 1
                )
            )
            .shadow(
                color: isDark ? AutomotivePalette.electricBlue.opacity(0.09) : .clear,
                radius: compact ? 4 : 10,
                y: 3
            )
    }
}
