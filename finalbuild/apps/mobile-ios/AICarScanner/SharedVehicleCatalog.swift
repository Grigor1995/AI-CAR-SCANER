
import Foundation

/// Reads the byte-identical shared catalog snapshot bundled with Android and Desktop.
enum SharedVehicleCatalog {
    static func offline(bundle: Bundle = .main) -> [VehicleCatalogEntry] {
        guard let url = bundle.url(forResource: "vehicle_catalog", withExtension: "json", subdirectory: "VehicleCatalog"),
              let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let rows = root["vehicles"] as? [[String: Any]] else { return [] }
        return rows.compactMap { row in
            guard let make = row["make"] as? String, let model = row["model"] as? String,
                  let year = row["year"] as? Int, let engine = row["engine"] as? String else { return nil }
            let fuel = (row["fuel"] as? String ?? "").lowercased()
                .components(separatedBy: CharacterSet(charactersIn: "+/,"))
                .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
            return VehicleCatalogEntry(make: make, model: model, chassis: row["chassis"] as? String,
                year: year, engine: engine, ecu: row["ecu"] as? String, fuel: fuel,
                source: "shared-offline-snapshot", scope: "offline-reference-not-vin-fitment")
        }
    }

    static func merge(server: [VehicleCatalogEntry], offline: [VehicleCatalogEntry]) -> [VehicleCatalogEntry] {
        var seen = Set<String>()
        return (server + offline).filter { item in
            let key = [item.make, item.model, item.chassis ?? "", String(item.year), item.engine, item.ecu ?? ""].joined(separator: "|")
            return seen.insert(key).inserted
        }
    }
}
