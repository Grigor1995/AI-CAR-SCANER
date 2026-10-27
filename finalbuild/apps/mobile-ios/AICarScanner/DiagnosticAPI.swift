import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case server(Int, String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid backend URL"
        case .server(let code, let body):
            return "HTTP \(code): \(body)"
        }
    }
}

final class DiagnosticAPI {
    var baseURL: String
    private let session: URLSession

    init(baseURL: String, session: URLSession = .shared) {
        self.baseURL = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        self.session = session
    }

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        body: Encodable? = nil,
        query: [URLQueryItem] = []
    ) async throws -> T {
        guard var components = URLComponents(string: baseURL),
              let scheme = components.scheme?.lowercased(),
              ["http", "https"].contains(scheme),
              components.host != nil else {
            throw APIError.invalidURL
        }

        let basePath = components.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        let endpointPath = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        components.path = "/" + [basePath, endpointPath].filter { !$0.isEmpty }.joined(separator: "/")
        components.queryItems = query.isEmpty ? nil : query

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = path.contains("ai-analyze-live") ? 300 : 60
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        }

        let (data, response) = try await session.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidURL
        }

        guard (200..<300).contains(http.statusCode) else {
            throw APIError.server(
                http.statusCode,
                String(data: data, encoding: .utf8) ?? ""
            )
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    func operation(_ path: String, method: String = "GET", body: [String: JSONValue]? = nil, language: String? = nil) async throws -> JSONValue {
        try await request(path, method: method, body: body, query: language.map { [URLQueryItem(name:"language", value:$0)] } ?? [])
    }

    func discoveryPlan() async throws -> DiscoveryPlan {
        try await request("/api/v1/obd/discovery/plan")
    }
    func decodeDiscovery(_ responses: [String:String]) async throws -> DiscoveryResult {
        try await request("/api/v1/obd/discovery/decode", method:"POST", body:ObdRawSnapshot(responses:responses,session_id:nil))
    }
    func reportData(_ id: String, format: String, language: AppLanguage) async throws -> Data {
        guard var parts=URLComponents(string:baseURL + "/api/v1/sessions/" + id + "/report") else { throw APIError.invalidURL }
        parts.queryItems=[URLQueryItem(name:"format",value:format),URLQueryItem(name:"language",value:language.rawValue)]
        guard let url=parts.url else { throw APIError.invalidURL }
        let (data,response)=try await session.data(from:url)
        guard let http=response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw APIError.server((response as? HTTPURLResponse)?.statusCode ?? 0,String(decoding:data,as:UTF8.self)) }
        return data
    }

    func obdPlan() async throws -> ObdPollingPlan {
        try await request("/api/v1/obd/plan")
    }

    func supportedObdPlan(_ responses: [String: String]) async throws -> ObdPollingPlan {
        try await request("/api/v1/obd/plan", method: "POST", body: ObdRawSnapshot(responses:responses, session_id:nil))
    }

    func decodeObd(_ responses: [String: String], sessionID: String? = nil) async throws -> ObdDecodedSnapshot {
        try await request("/api/v1/obd/decode", method: "POST", body: ObdRawSnapshot(responses: responses, session_id: sessionID))
    }

    func listSessions() async throws -> [DiagnosticSession] {
        try await request("/api/v1/sessions")
    }

    func getSession(_ id: String, language: AppLanguage = .en) async throws -> DiagnosticSession {
        try await request("/api/v1/sessions/\(id)", query: [URLQueryItem(name: "language", value: language.rawValue)])
    }

    func liveRecords(_ id: String) async throws -> LiveRecordResponse {
        try await request("/api/v1/acquisition/sessions/\(id)/records")
    }

    func vehicleCatalog() async throws -> [VehicleCatalogEntry] {
        try await request("/api/v1/vehicle-catalog/entries")
    }

    // Canonical global vehicle registry: no locally invented engine or OBD rules.
    func vehicleRegistryMakes() async throws -> [String] {
        try await request("/api/v1/vehicle-registry/makes")
    }

    func vehicleRegistryModels(make: String, year: Int? = nil) async throws -> [GlobalVehicleModel] {
        var query = [URLQueryItem(name: "make", value: make)]
        if let year { query.append(URLQueryItem(name: "year", value: String(year))) }
        return try await request("/api/v1/vehicle-registry/models", query: query)
    }

    func vehicleProtocolHints(year: Int, market: String, make: String) async throws -> ProtocolCompatibility {
        try await request("/api/v1/vehicle-registry/compatibility", query: [
            URLQueryItem(name: "year", value: String(year)),
            URLQueryItem(name: "market", value: market),
            URLQueryItem(name: "make", value: make)
        ])
    }

    func vehiclePhotoMetadata(make: String, model: String, chassis: String) async throws -> VehiclePhotoMetadata {
        try await request("/api/v1/vehicle-registry/photo", query: [
            URLQueryItem(name: "make", value: make),
            URLQueryItem(name: "model", value: model),
            URLQueryItem(name: "chassis", value: chassis)
        ])
    }

    func createSession(_ vehicle: Vehicle) async throws -> DiagnosticSession {
        try await request("/api/v1/sessions", method: "POST", body: vehicle)
    }

    func updateVehicle(_ id: String, _ vehicle: Vehicle) async throws -> DiagnosticSession {
        try await request("/api/v1/sessions/\(id)/vehicle", method: "PUT", body: vehicle)
    }

    func addSymptom(_ id: String, _ value: String) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/symptoms",
            method: "POST",
            body: SymptomRequest(raw_text: value, normalized: [:], symptom: value)
        )
    }

    func updateSymptom(_ id: String, _ symptomID: String, _ value: String) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/symptoms/\(symptomID)",
            method: "PUT",
            body: SymptomRequest(raw_text: value, normalized: [:], symptom: value)
        )
    }

    func deleteSymptom(_ id: String, _ symptomID: String) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/symptoms/\(symptomID)",
            method: "DELETE"
        )
    }

    func addDTC(_ id: String, _ code: String) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/dtcs",
            method: "POST",
            body: DTCRequest(code: code.uppercased())
        )
    }

    func updateDTC(_ id: String, _ dtcID: String, _ code: String, _ description: String?, _ source: String?) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/dtcs/\(dtcID)",
            method: "PUT",
            body: DTCUpdateRequest(
                code: code.trimmingCharacters(in: .whitespacesAndNewlines).uppercased(),
                description: description,
                source: source ?? "USER_REPORTED"
            )
        )
    }

    func deleteDTC(_ id: String, _ dtcID: String) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/sessions/\(id)/dtcs/\(dtcID)",
            method: "DELETE"
        )
    }

    func analyze(_ id: String, _ language: AppLanguage) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/analysis/\(id)",
            method: "POST",
            query: [URLQueryItem(name: "language", value: language.rawValue)]
        )
    }

    func recordTest(
        _ id: String,
        _ test: Recommendation,
        _ result: String,
        _ notes: String?,
        _ language: AppLanguage
    ) async throws -> DiagnosticSession {
        try await request(
            "/api/v1/intelligence/sessions/\(id)/test-results",
            method: "POST",
            body: TestResultRequest(
                test_id: test.id,
                result: result,
                measurements: [:],
                notes: notes
            ),
            query: [URLQueryItem(name: "language", value: language.rawValue)]
        )
    }
}

struct AnyEncodable: Encodable {
    private let block: (Encoder) throws -> Void

    init(_ value: Encodable) {
        block = value.encode
    }

    func encode(to encoder: Encoder) throws {
        try block(encoder)
    }
}

struct ObdPollingPlan: Decodable { let initialization: [String]; let commands: [String]; let discovery: [String]? }
struct ObdRawSnapshot: Encodable { let responses: [String: String]; let session_id: String? }
struct ObdDecodedSnapshot: Decodable { let values: [String: Double?]; let errors: [String: String] }

struct DiscoveryPlan: Decodable { let commands:[String]; let restore:[String] }
struct DiscoveryResult: Decodable {
    let vin:String?; let identification_status:String
    let vehicle:[String:JSONValue]?; let modules:[JSONValue]
    let detectedProtocol:JSONValue?
    enum CodingKeys:String,CodingKey {case vin, identification_status, vehicle, modules;case detectedProtocol="protocol"}
}
