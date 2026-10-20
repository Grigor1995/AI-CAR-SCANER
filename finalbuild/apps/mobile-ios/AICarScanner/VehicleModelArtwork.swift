import SwiftUI
import WebKit

/// Offline, model-specific illustrated vehicle image.
/// The illustrations are not OEM photographs or VIN-level identification.
struct VehicleModelArtwork: View {
    let make: String
    let model: String
    let chassis: String

    private func piece(_ text: String) -> String {
        text.lowercased()
            .replacingOccurrences(
                of: "[^a-z0-9]+", with: "-", options: .regularExpression
            )
            .trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }

    private var artworkURL: URL? {
        let filename = [make, model, chassis].map(piece).joined(separator: "_")
        return Bundle.main.url(
            forResource: filename, withExtension: "svg", subdirectory: "VehicleModels"
        ) ?? Bundle.main.url(forResource: filename, withExtension: "svg")
    }

    var body: some View {
        Group {
            if let artworkURL {
                VehicleSVGWebView(url: artworkURL)
                    .frame(height: 165)
                    .accessibilityLabel("\(make) \(model) \(chassis) illustrated vehicle")
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "car.side.fill")
                        .font(.system(size: 66))
                        .foregroundStyle(AutomotivePalette.cyan)
                    Text("\(make) \(model) \(chassis)")
                        .font(.caption.weight(.semibold))
                }
                .frame(maxWidth: .infinity, minHeight: 165)
                .background(AutomotivePalette.navy)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }
}

private struct VehicleSVGWebView: UIViewRepresentable {
    let url: URL

    final class Coordinator {
        var lastURL: URL?
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = false
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.isScrollEnabled = false
        webView.isOpaque = false
        webView.backgroundColor = .clear
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        guard context.coordinator.lastURL != url else { return }
        context.coordinator.lastURL = url
        webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }
}
