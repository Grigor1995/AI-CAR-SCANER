import Foundation

struct VehicleCatalogEntry: Codable, Identifiable, Hashable {
    var id: String { "\(make)|\(model)|\(chassis ?? "")|\(year)|\(engine)" }
    let make: String
    let model: String
    let chassis: String?
    let year: Int
    let engine: String
    let ecu: String?
    let fuel: [String]
    let source: String
    let scope: String
}
struct Vehicle: Codable {
    let make: String
    let model: String
    let chassis: String?
    let year: Int?
    let engine: String?
    let fuel: [String]
    let ecu: String?
}
struct Symptom: Codable, Identifiable {
    let id: String
    let raw_text: String
    let normalized: [String:String]
}
struct DTC: Codable, Identifiable {
    let id: String?
    let code: String
    let description: String?
    let source: String?
}
struct Evidence: Codable, Identifiable {
    let id: String
    let fact: String
    let source: String
    let status: String
    let confidence: Double?
}
struct Hypothesis: Codable, Identifiable {
    let id: String
    let category: String
    let statement: String
    let supporting_evidence_ids: [String]
    let contradicting_evidence_ids: [String]
    let status: String
}
struct Recommendation: Codable, Identifiable {
    let id: String
    let name: String
    let purpose: String
    let priority_score: Double
    let expected_observation: String?
    let expected_information_gain: Double
    let estimated_cost: Double
    let risk_level: String
    let prerequisites: [String]
    let target_hypotheses: [String]
    let safety_notes: [String]
}
struct TestResult: Codable, Identifiable {
    var id: String { test_id }
    let test_id: String
    let result: String
    let measurements: [String:String]
    let notes: String?
    let test_name: String?
}
struct AuditEvent: Codable, Identifiable {
    var id: String { event + String(hypotheses ?? 0) + String(evidence_count ?? 0) }
    let event: String
    let hypotheses: Int?
    let evidence_count: Int?
    let hypothesis_count: Int?
    let questions: [String]?
}
struct DiagnosticSession: Codable {
    let session_id: String
    let state: String
    let vehicle: Vehicle?
    let symptoms: [Symptom]
    let dtcs: [DTC]
    let evidence: [Evidence]
    let hypotheses: [Hypothesis]
    let recommendations: [Recommendation]
    let test_results: [TestResult]
    let audit_log: [AuditEvent]
}
struct SymptomRequest: Encodable {
    let raw_text: String
    let normalized: [String:String]
    let symptom: String
}
struct DTCRequest: Encodable { let code: String }
struct TestResultRequest: Encodable {
    let test_id: String
    let result: String
    let measurements: [String:String]
    let notes: String?
}
enum AppLanguage: String, CaseIterable, Identifiable {
    case en, ru, hy
    var id: String { rawValue }
    var label: String { self == .en ? "EN" : self == .ru ? "RU" : "ARM" }
}
struct AppSettings {
    var language: AppLanguage = .en
    var darkTheme = true
    var apiURL = "http://127.0.0.1:8001"
}