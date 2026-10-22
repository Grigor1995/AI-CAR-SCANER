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
    var image_attribution: [String: String]? = nil
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
extension Hypothesis {
    var evidenceScore: Double? {
        let parts = status.split(separator: ":", omittingEmptySubsequences: false)
        guard parts.count == 2, let score = Double(parts[1]), score.isFinite,
              (0...1).contains(score) else { return nil }
        return score
    }
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
    var result_label: String? = nil
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
struct DTCUpdateRequest: Encodable {
    let code: String
    let description: String?
    let source: String
}
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
    var apiURL = "https://ai-car-scaner.onrender.com"
}
struct LiveRecord: Decodable {
    let channel: String?
    private let recordedPID: String?
    let numeric_value: Double?
    let unit: String?
    let source_type: String?
    let metadata: LiveRecordMetadata?
    var pid: String { channel ?? recordedPID ?? "Unknown channel" }
    var sourceLabel: String { metadata?.adapter == "simulator" ? "Simulator / synthetic data" : source_type ?? "—" }
    enum CodingKeys: String, CodingKey {
        case channel, numeric_value, unit, source_type, metadata
        case recordedPID = "pid"
    }
}
struct LiveRecordMetadata: Decodable { let adapter: String? }
struct LiveRecordResponse: Decodable { let records: [LiveRecord] }


extension DiagnosticSession {
    var userReportJSON: String {
        guard let data = try? JSONEncoder().encode(self),
              let object = try? JSONSerialization.jsonObject(with: data),
              let report = try? JSONSerialization.data(withJSONObject: reportSnapshot(object), options: [.prettyPrinted, .sortedKeys]),
              let text = String(data: report, encoding: .utf8) else { return "" }
        return text
    }
}

private func reportSnapshot(_ value: Any) -> Any {
    if let dictionary = value as? [String: Any] {
        return dictionary.filter { $0.key != "session_id" }.mapValues { reportSnapshot($0) }
    }
    if let array = value as? [Any] { return array.map { reportSnapshot($0) } }
    return value
}
