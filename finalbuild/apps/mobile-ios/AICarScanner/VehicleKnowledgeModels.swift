import Foundation

/// DTOs only; canonical make/model/engine/ECU mappings and protocol detection
/// are supplied by the FastAPI backend, not recomputed in native SwiftUI.
struct GlobalVehicleModelsResponse: Decodable {
    let total: Int
    let offset: Int
    let limit: Int
    let vehicles: [GlobalVehicleModel]
}

struct GlobalVehicleModel: Decodable {
    let make: String
    let model: String
    let year_ranges: [[Int]]
    let vehicle_type: String
    let fuel_options: [String]
    let engine_families: [String]
    let fitment_verified: Bool
}

struct CuratedVehicleVariantsResponse: Decodable {
    let total: Int
    let offset: Int
    let limit: Int
    let variants: [CuratedVehicleVariant]
}

struct CuratedVehicleVariant: Decodable {
    let make: String
    let model: String
    let chassis: String?
    let year_ranges: [[Int]]
    let engine: String
    let engine_type: [String]
    let ecu_hints: [String]
    let vin_verified: Bool
    let obd_protocol_confirmed: Bool
}

struct BackendProtocolRegistryResponse: Decodable {
    let protocols: [BackendOBDProtocol]
    let caution: String
}

struct BackendOBDProtocol: Decodable {
    let id: String
    let label: String
    let family: String
    let elm_id: String?
    let supported_by_generic_elm: Bool
    let capability: String
    let server_hardware_integration: String
}

struct VehicleImageMetadata: Decodable {
    let image_kind: String
    let uri: String?
    let file_format: String?
    let is_real_car_photo: Bool
    let attribution: String?
    let photo_search_endpoint: String
}
