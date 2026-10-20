import SwiftUI
import UIKit

/// Generated illustrations, matched to the exact catalog model and chassis.
struct VehicleModelArtwork: View {
    let make: String
    let model: String
    let chassis: String

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

    var body: some View {
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
        .accessibilityLabel("\(make) \(model) \(chassis) illustration")
    }
}
