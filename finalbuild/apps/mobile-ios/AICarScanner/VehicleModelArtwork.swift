import SwiftUI
import UIKit

/// Generated illustrations, matched to the exact catalog model and chassis.
struct VehicleModelArtwork: View {
    let make: String
    let model: String
    let chassis: String
    var backendURL: String? = nil
    var photoAttribution: [String: String]? = nil

    private func piece(_ text: String) -> String {
        text.lowercased()
            .replacingOccurrences(of: "[^a-z0-9]+", with: "-", options: .regularExpression)
            .trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }

    private var portrait: UIImage? {
        let name = [make, model, chassis].map(piece).joined(separator: "_")
        guard let url = Bundle.main.url(forResource: name, withExtension: "png",
                                        subdirectory: "VehicleModels"),
              let data = try? Data(contentsOf: url) else { return nil }
        return UIImage(data: data)
    }

    private var remoteURL: URL? {
        guard let backendURL, var url = URLComponents(string: backendURL) else { return nil }
        url.path = url.path.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + "/api/v1/vehicle-reference/image"
        if !url.path.hasPrefix("/") { url.path = "/" + url.path }
        url.queryItems = [URLQueryItem(name: "make", value: make), URLQueryItem(name: "model", value: model), URLQueryItem(name: "chassis", value: chassis)]
        return url.url
    }

    var body: some View {
        if let remoteURL {
            AsyncImage(url: remoteURL) { phase in
                if let image = phase.image {
                    VStack {
                        image.resizable().scaledToFit().frame(maxWidth: .infinity).frame(height: 170)
                        if let credit = photoAttribution, let source = credit["source_page"], let url = URL(string: source) {
                            Link([credit["creator"], credit["license"]].compactMap { $0 }.joined(separator: " • "), destination: url).font(.caption)
                        }
                    }
                }
                else { bundledArtwork }
            }.id(remoteURL)
                .modifier(NeonVehicleFrame())
        } else { bundledArtwork }
    }

    private var bundledArtwork: some View {
        Group {
            if let portrait {
                Image(uiImage: portrait)
                    .resizable()
                    .scaledToFit()
            } else {
                Image(systemName: "car.side.fill")
                    .resizable()
                    .scaledToFit()
                    .foregroundStyle(AutomotivePalette.electricBlue)
                    .padding(35)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: 165)
        .modifier(NeonVehicleFrame())
        .accessibilityLabel("\(make) \(model) \(chassis) illustration")
    }
}

private struct NeonVehicleFrame: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(8)
            .background(
                RoundedRectangle(cornerRadius: 18)
                    .fill(LinearGradient(
                        colors: [AutomotivePalette.navy, AutomotivePalette.panel, AutomotivePalette.navy],
                        startPoint: .topLeading, endPoint: .bottomTrailing
                    ))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18)
                    .strokeBorder(AutomotivePalette.electricBlue.opacity(0.65), lineWidth: 1)
            )
            .shadow(color: AutomotivePalette.cyan.opacity(0.28), radius: 14, y: 5)
    }
}
