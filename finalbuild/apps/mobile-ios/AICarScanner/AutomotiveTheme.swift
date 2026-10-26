import SwiftUI
import UIKit

// Shared visual language for the native automotive diagnostics screens.
// The reference mockup is a design guide; actual telemetry and AI confidence
// values continue to come from the ViewModel/backend, never from decorative UI.
enum AutomotivePalette {
    static let navy = Color(red: 3.0 / 255, green: 7.0 / 255, blue: 14.0 / 255)
    static let midnight = Color(red: 5.0 / 255, green: 23.0 / 255, blue: 39.0 / 255)
    static let panel = Color(red: 13.0 / 255, green: 31.0 / 255, blue: 62.0 / 255)
    static let electricBlue = Color(red: 0.0 / 255, green: 174.0 / 255, blue: 239.0 / 255)
    static let cyan = Color(red: 121.0 / 255, green: 227.0 / 255, blue: 255.0 / 255)
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
            .background(shape.fill(LinearGradient(colors: isDark ? [AutomotivePalette.midnight, AutomotivePalette.panel, AutomotivePalette.navy] : [.white, Color(red:0.90,green:0.95,blue:1)], startPoint:.topLeading,endPoint:.bottomTrailing)))
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

// Desktop artwork is packaged as an explicit resource folder on both platforms.
enum DesktopArtwork {
    static let car: UIImage? = load("launcher_car")
    static let background: UIImage? = load("launcher_background")
    private static func load(_ name:String) -> UIImage? {
        guard let url=Bundle.main.url(forResource:name,withExtension:"png",subdirectory:"Launcher") else {return nil}
        return UIImage(contentsOfFile:url.path)
    }
    private static let atlas: UIImage? = load("launcher_icons")
    static let icons: [Int:UIImage] = {
        guard let cg=atlas?.cgImage else { return [:] }
        let w=cg.width/4, h=cg.height/3
        let slots=[11:0, 1:1, 3:2, 8:4, 7:5, 2:6, 6:7, 9:8, 10:9, 5:10, 4:11]
        var result:[Int:UIImage]=[:]
        for (id,slot) in slots {
            if let cell=cg.cropping(to:CGRect(x:CGFloat(slot%4*w),y:CGFloat(slot/4*h),width:CGFloat(w)*0.96,height:CGFloat(h))) {
                result[id]=UIImage(cgImage:cell)
            }
        }
        result[0]=car;result[12]=car
        return result
    }()
}
struct DesktopIcon: View {
    let page:Int
    var body: some View {
        if let image=DesktopArtwork.icons[page] {
            Image(uiImage:image).resizable().scaledToFit().accessibilityHidden(true)
        } else { Image(systemName:"square.grid.2x2").foregroundStyle(AutomotivePalette.cyan) }
    }
}
