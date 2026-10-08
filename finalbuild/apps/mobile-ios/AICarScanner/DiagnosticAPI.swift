import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case server(Int, String)
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid backend URL"
        case .server(let code, let body): return "HTTP \(code): \(body)"
        }
    }
}

final class DiagnosticAPI {
    var baseURL: String
    private let session = URLSession.shared
    init(baseURL: String) { self.baseURL = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/")) }

    private func request<T: Decodable>(_ path: String, method: String = "GET", body: Encodable? = nil, query: [URLQueryItem] = []) async throws -> T {
        guard var c = URLComponents(string: baseURL + path), let _ = c.url else { throw APIError.invalidURL }
        c.queryItems = query.isEmpty ? nil : query
        guard let url = c.url else { throw APIError.invalidURL }
        var r = URLRequest(url: url); r.httpMethod = method
        r.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body { r.setValue("application/json", forHTTPHeaderField: "Content-Type"); r.httpBody = try JSONEncoder().encode(AnyEncodable(body)) }
        let (data, response) = try await session.data(for: r)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidURL }
        guard (200..<300).contains(http.statusCode) else { throw APIError.server(http.statusCode, String(data: data, encoding: .utf8) ?? "") }
        return try JSONDecoder().decode(T.self, from: data)
    }
    func vehicleCatalog() async throws -> [VehicleCatalogEntry] { try await request("/api/v1/vehicle-catalog/entries") }
    func createSession(_ v: Vehicle) async throws -> DiagnosticSession { try await request("/api/v1/sessions", method:"POST", body:v) }
    func updateVehicle(_ id:String,_ v:Vehicle) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\(id)/vehicle",method:"PUT",body:v) }
    func addSymptom(_ id:String,_ value:String) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\(id)/symptoms",method:"POST",body:SymptomRequest(raw_text:value,normalized:[:],symptom:value)) }
    func updateSymptom(_ id:String,_ sid:String,_ value:String) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\\(id)/symptoms/\\(sid)",method:"PUT",body:SymptomRequest(raw_text:value,normalized:[:],symptom:value)) }\n    func deleteSymptom(_ id:String,_ sid:String) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\(id)/symptoms/\(sid)",method:"DELETE") }
    func addDTC(_ id:String,_ code:String) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\(id)/dtcs",method:"POST",body:DTCRequest(code:code.uppercased())) }
    func deleteDTC(_ id:String,_ did:String) async throws -> DiagnosticSession { try await request("/api/v1/sessions/\(id)/dtcs/\(did)",method:"DELETE") }
    func analyze(_ id:String,_ language:AppLanguage) async throws -> DiagnosticSession { try await request("/api/v1/analysis/\(id)",method:"POST",query:[URLQueryItem(name:"language",value:language.rawValue)]) }
    func recordTest(_ id:String,_ test:Recommendation,_ result:String,_ notes:String?,_ language:AppLanguage) async throws -> DiagnosticSession {
        try await request("/api/v1/intelligence/sessions/\(id)/test-results",method:"POST",body:TestResultRequest(test_id:test.id,result:result,measurements:[:],notes:notes),query:[URLQueryItem(name:"language",value:language.rawValue)])
    }
}
struct AnyEncodable: Encodable {
    private let block:(Encoder)throws->Void
    init(_ value:Encodable){ block=value.encode }
    func encode(to encoder:Encoder)throws{ try block(encoder) }
}