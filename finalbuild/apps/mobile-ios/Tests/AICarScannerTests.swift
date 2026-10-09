import Foundation
import XCTest
@testable import AICarScanner

final class AICarScannerTests: XCTestCase {
    override func tearDown() {
        MockURLProtocol.handler = nil
        MockURLProtocol.lastRequest = nil
        super.tearDown()
    }

    func testVehicleRoundTrip() throws {
        let value = Vehicle(make: "Mercedes-Benz", model: "E-Class", chassis: "W211", year: 2006, engine: "M272 E35 3.5", fuel: ["petrol", "lpg"], ecu: "ME9.7")
        let data = try JSONEncoder().encode(value)
        let decoded = try JSONDecoder().decode(Vehicle.self, from: data)
        XCTAssertEqual(decoded.make, "Mercedes-Benz")
        XCTAssertEqual(decoded.year, 2006)
        XCTAssertEqual(decoded.fuel, ["petrol", "lpg"])
    }

    func testLanguages() {
        XCTAssertEqual(AppLanguage.en.label, "EN")
        XCTAssertEqual(AppLanguage.ru.label, "RU")
        XCTAssertEqual(AppLanguage.hy.label, "ARM")
    }

    func testVehicleCatalogRequestAndDecode() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "GET")
            XCTAssertEqual(request.url?.path, "/api/v1/vehicle-catalog/entries")
            return (200, Data("[]".utf8))
        }

        let api = makeAPI()
        let entries = try await api.vehicleCatalog()
        XCTAssertTrue(entries.isEmpty)
        XCTAssertEqual(MockURLProtocol.lastRequest?.url?.path, "/api/v1/vehicle-catalog/entries")
    }

    func testCreateSessionSendsVehiclePayload() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.url?.path, "/api/v1/sessions")
            let body = try XCTUnwrap(Self.bodyData(from: request))
            let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
            XCTAssertEqual(json["make"] as? String, "Mercedes-Benz")
            XCTAssertEqual(json["year"] as? Int, 2006)
            XCTAssertEqual(json["fuel"] as? [String], ["petrol", "lpg"])
            return (201, Self.sessionJSON)
        }

        let vehicle = Vehicle(
            make: "Mercedes-Benz", model: "W211 E350", chassis: "W211",
            year: 2006, engine: "M272 3.5", fuel: ["petrol", "lpg"], ecu: "ME 9.7"
        )
        let session = try await makeAPI().createSession(vehicle)
        XCTAssertEqual(session.session_id, "golden-session")
        XCTAssertEqual(session.vehicle?.make, "Mercedes-Benz")
    }

    func testGoldenCaseAnalysisUsesSelectedLanguageAndPreservesUncertainty() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.url?.path, "/api/v1/analysis/golden-session")
            XCTAssertEqual(URLComponents(url: try XCTUnwrap(request.url), resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "language" })?.value, "ru")
            return (200, Self.goldenAnalysisJSON)
        }

        let session = try await makeAPI().analyze("golden-session", .ru)
        XCTAssertEqual(session.dtcs.map(\.code), ["P0302"])
        XCTAssertTrue(session.hypotheses.contains { $0.category.localizedCaseInsensitiveContains("LPG") })
        XCTAssertTrue(session.hypotheses.allSatisfy { $0.status.lowercased() != "confirmed" })
        XCTAssertFalse(session.hypotheses.contains {
            let text = ($0.category + " " + $0.statement).lowercased()
            return text.contains("confirmed coil failure")
                || text.contains("confirmed injector failure")
                || text.contains("confirmed mechanical failure")
        })
    }

    func testHTTPErrorIsSurfaced() async {
        MockURLProtocol.handler = { _ in (503, Data("service unavailable".utf8)) }
        do {
            _ = try await makeAPI().vehicleCatalog()
            XCTFail("Expected HTTP 503 to throw")
        } catch let error as APIError {
            guard case let .server(code, body) = error else {
                return XCTFail("Expected server error, got \(error)")
            }
            XCTAssertEqual(code, 503)
            XCTAssertEqual(body, "service unavailable")
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func testInvalidBaseURLThrows() async {
        do {
            _ = try await DiagnosticAPI(baseURL: "://invalid").vehicleCatalog()
            XCTFail("Expected invalid URL to throw")
        } catch let error as APIError {
            guard case .invalidURL = error else {
                return XCTFail("Expected invalidURL, got \(error)")
            }
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func testUpdateVehicleUsesPUTAndEncodesPayload() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "PUT")
            XCTAssertEqual(request.url?.path, "/api/v1/sessions/golden-session/vehicle")
            let body = try XCTUnwrap(Self.bodyData(from: request))
            let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
            XCTAssertEqual(json["model"] as? String, "W211 E350")
            return (200, Self.sessionJSON)
        }
        let vehicle = Vehicle(make: "Mercedes-Benz", model: "W211 E350", chassis: "W211", year: 2006, engine: "M272", fuel: ["lpg"], ecu: "ME9.7")
        _ = try await makeAPI().updateVehicle("golden-session", vehicle)
    }

    func testSymptomCreateUpdateAndDeleteRoutes() async throws {
        let api = makeAPI()
        MockURLProtocol.handler = { request in
            switch (request.httpMethod, request.url?.path) {
            case ("POST", "/api/v1/sessions/s1/symptoms"):
                let body = try XCTUnwrap(Self.bodyData(from: request))
                let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
                XCTAssertEqual(json["raw_text"] as? String, "Shakes on LPG")
                XCTAssertEqual(json["symptom"] as? String, "Shakes on LPG")
            case ("PUT", "/api/v1/sessions/s1/symptoms/sym-1"):
                let body = try XCTUnwrap(Self.bodyData(from: request))
                let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
                XCTAssertEqual(json["raw_text"] as? String, "Updated symptom")
            case ("DELETE", "/api/v1/sessions/s1/symptoms/sym-1"):
                XCTAssertNil(request.httpBody)
            default:
                XCTFail("Unexpected request: \(request.httpMethod ?? "?") \(request.url?.path ?? "?")")
            }
            return (200, Self.sessionJSON)
        }
        _ = try await api.addSymptom("s1", "Shakes on LPG")
        _ = try await api.updateSymptom("s1", "sym-1", "Updated symptom")
        _ = try await api.deleteSymptom("s1", "sym-1")
    }

    func testDTCAddUppercasesCodeAndDeleteUsesIdentifier() async throws {
        let api = makeAPI()
        MockURLProtocol.handler = { request in
            if request.httpMethod == "POST" {
                XCTAssertEqual(request.url?.path, "/api/v1/sessions/s1/dtcs")
                let body = try XCTUnwrap(Self.bodyData(from: request))
                let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
                XCTAssertEqual(json["code"] as? String, "P0302")
            } else {
                XCTAssertEqual(request.httpMethod, "DELETE")
                XCTAssertEqual(request.url?.path, "/api/v1/sessions/s1/dtcs/dtc-1")
            }
            return (200, Self.sessionJSON)
        }
        _ = try await api.addDTC("s1", "p0302")
        _ = try await api.deleteDTC("s1", "dtc-1")
    }

    func testRecordTestSendsResultNotesAndLanguage() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.url?.path, "/api/v1/intelligence/sessions/s1/test-results")
            XCTAssertEqual(URLComponents(url: try XCTUnwrap(request.url), resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "language" })?.value, "hy")
            let body = try XCTUnwrap(Self.bodyData(from: request))
            let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
            XCTAssertEqual(json["test_id"] as? String, "test-1")
            XCTAssertEqual(json["result"] as? String, "FAIL")
            XCTAssertEqual(json["notes"] as? String, "Pressure out of range")
            XCTAssertNotNil(json["measurements"] as? [String: String])
            return (200, Self.sessionJSON)
        }
        let recommendation = Recommendation(
            id: "test-1", name: "Check LPG pressure", purpose: "Validate delivery pressure",
            priority_score: 1, expected_observation: nil, expected_information_gain: 0.8,
            estimated_cost: 0, risk_level: "LOW", prerequisites: [], target_hypotheses: [],
            safety_notes: []
        )
        _ = try await makeAPI().recordTest("s1", recommendation, "FAIL", "Pressure out of range", .hy)
    }

    func testInvalidJSONResponseThrowsDecodingError() async {
        MockURLProtocol.handler = { _ in (200, Data("{invalid".utf8)) }
        do {
            _ = try await makeAPI().vehicleCatalog()
            XCTFail("Expected JSON decoding to fail")
        } catch {
            XCTAssertNotNil(error)
        }
    }

    func testAPIBasePathIsPreserved() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.url?.path, "/proxy/api/v1/vehicle-catalog/entries")
            return (200, Data("[]".utf8))
        }
        let api = DiagnosticAPI(baseURL: "https://unit.test/proxy", session: URLSession(configuration: {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [MockURLProtocol.self]
            return configuration
        }()))
        let entries = try await api.vehicleCatalog()
        XCTAssertTrue(entries.isEmpty)
    }

    @MainActor
    func testViewModelSettingsLoadSaveAndSessionGuards() async {
        let defaults = UserDefaults(suiteName: "AICarScannerTests-\(UUID().uuidString)")!
        defaults.set("ru", forKey: "language")
        defaults.set(false, forKey: "darkTheme")
        defaults.set("https://unit.test", forKey: "apiURL")
        let viewModel = DiagnosticViewModel(defaults: defaults, loadCatalogOnInit: false)
        XCTAssertEqual(viewModel.settings.language, .ru)
        XCTAssertFalse(viewModel.settings.darkTheme)
        XCTAssertEqual(viewModel.settings.apiURL, "https://unit.test")

        let vehicle = Vehicle(make: "Mercedes-Benz", model: "W211", chassis: "W211", year: 2006, engine: "M272", fuel: ["lpg"], ecu: "ME9.7")
        await viewModel.updateVehicle(vehicle)
        await viewModel.addSymptom("test")
        await viewModel.updateSymptom(Symptom(id: "s1", raw_text: "old", normalized: [:]), "new")
        await viewModel.deleteSymptom(Symptom(id: "s1", raw_text: "old", normalized: [:]))
        await viewModel.addDTC("P0302")
        await viewModel.deleteDTC(DTC(id: "d1", code: "P0302", description: nil, source: nil))
        await viewModel.analyze()
        let recommendation = Recommendation(
            id: "t1", name: "Check", purpose: "Verify", priority_score: 1,
            expected_observation: nil, expected_information_gain: 0.5, estimated_cost: 0,
            risk_level: "LOW", prerequisites: [], target_hypotheses: [], safety_notes: []
        )
        await viewModel.recordTest(recommendation, "INCOMPLETE", nil)
        XCTAssertNil(viewModel.session)
        XCTAssertFalse(viewModel.loading)

        viewModel.settings.language = .hy
        viewModel.settings.darkTheme = true
        viewModel.settings.apiURL = "https://saved.test"
        viewModel.saveSettings()
        XCTAssertEqual(defaults.string(forKey: "language"), "hy")
        XCTAssertEqual(defaults.object(forKey: "darkTheme") as? Bool, true)
        XCTAssertEqual(defaults.string(forKey: "apiURL"), "https://saved.test")
        viewModel.clearSession()
        XCTAssertNil(viewModel.session)
    }

    @MainActor
    func testViewModelRunsSessionWorkflowAndClearsLoadingOnSuccess() async throws {
        let requests = RequestRecorder()
        MockURLProtocol.handler = { request in
            requests.paths.append(request.url?.path ?? "")
            return (200, Self.sessionJSON)
        }
        let viewModel = makeViewModel()
        await viewModel.loadCatalog()
        XCTAssertTrue(viewModel.catalog.isEmpty)

        let vehicle = Vehicle(make: "Mercedes-Benz", model: "W211 E350", chassis: "W211", year: 2006, engine: "M272", fuel: ["petrol", "lpg"], ecu: "ME9.7")
        await viewModel.newSession(vehicle)
        XCTAssertEqual(viewModel.session?.session_id, "golden-session")
        await viewModel.updateVehicle(vehicle)
        await viewModel.addSymptom("LPG misfire")
        await viewModel.updateSymptom(Symptom(id: "symptom-1", raw_text: "old", normalized: [:]), "updated")
        await viewModel.deleteSymptom(Symptom(id: "symptom-1", raw_text: "old", normalized: [:]))
        await viewModel.addDTC("p0302")
        await viewModel.deleteDTC(DTC(id: "dtc-1", code: "P0302", description: nil, source: nil))
        await viewModel.analyze()
        let recommendation = Recommendation(
            id: "test-1", name: "Check mixture", purpose: "Check LPG pressure",
            priority_score: 1, expected_observation: nil, expected_information_gain: 0.7,
            estimated_cost: 0, risk_level: "LOW", prerequisites: [], target_hypotheses: [],
            safety_notes: []
        )
        await viewModel.recordTest(recommendation, "PASS", "Within range")

        XCTAssertEqual(requests.paths.count, 10)
        XCTAssertTrue(requests.paths.contains("/api/v1/vehicle-catalog/entries"))
        XCTAssertTrue(requests.paths.contains("/api/v1/sessions"))
        XCTAssertTrue(requests.paths.contains("/api/v1/analysis/golden-session"))
        XCTAssertNil(viewModel.error)
        XCTAssertFalse(viewModel.loading)
        viewModel.clearSession()
        XCTAssertNil(viewModel.session)
    }

    @MainActor
    func testViewModelStoresAPIErrorAndResetsLoading() async {
        MockURLProtocol.handler = { _ in (503, Data("backend offline".utf8)) }
        let viewModel = makeViewModel()
        await viewModel.newSession(Vehicle(make: "Kia", model: "Forte", chassis: nil, year: 2017, engine: "2.0", fuel: ["petrol"], ecu: nil))
        XCTAssertNil(viewModel.session)
        XCTAssertTrue(viewModel.error?.contains("503") == true)
        XCTAssertFalse(viewModel.loading)
    }

    @MainActor
    private func makeViewModel() -> DiagnosticViewModel {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        let defaults = UserDefaults(suiteName: "AICarScannerTests-\(UUID().uuidString)")!
        defaults.set("https://unit.test", forKey: "apiURL")
        return DiagnosticViewModel(
            apiSession: URLSession(configuration: configuration),
            defaults: defaults,
            loadCatalogOnInit: false
        )
    }

    private func makeAPI() -> DiagnosticAPI {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        return DiagnosticAPI(
            baseURL: "https://unit.test",
            session: URLSession(configuration: configuration)
        )
    }

    private static func bodyData(from request: URLRequest) -> Data? {
        if let body = request.httpBody { return body }
        guard let stream = request.httpBodyStream else { return nil }
        stream.open()
        defer { stream.close() }

        var data = Data()
        let bufferSize = 4096
        let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: bufferSize)
        defer { buffer.deallocate() }
        while stream.hasBytesAvailable {
            let count = stream.read(buffer, maxLength: bufferSize)
            if count < 0 { return nil }
            if count == 0 { break }
            data.append(buffer, count: count)
        }
        return data.isEmpty ? nil : data
    }

    private static let sessionJSON = Data("""
    {
      "session_id":"golden-session",
      "state":"COLLECTING_EVIDENCE",
      "vehicle":{"make":"Mercedes-Benz","model":"W211 E350","chassis":"W211","year":2006,"engine":"M272 3.5","fuel":["petrol","lpg"],"ecu":"ME 9.7"},
      "symptoms":[{"id":"symptom-1","raw_text":"Misfire on LPG below 2000 RPM","normalized":{}}],
      "dtcs":[{"id":"dtc-1","code":"P0302","description":"Cylinder 2 misfire","source":"manual"}],
      "evidence":[],
      "hypotheses":[],
      "recommendations":[],
      "test_results":[],
      "audit_log":[]
    }
    """.utf8)

    private static let goldenAnalysisJSON = Data("""
    {
      "session_id":"golden-session",
      "state":"ANALYSIS_READY",
      "vehicle":{"make":"Mercedes-Benz","model":"W211 E350","chassis":"W211","year":2006,"engine":"M272 3.5","fuel":["petrol","lpg"],"ecu":"ME 9.7"},
      "symptoms":[{"id":"symptom-1","raw_text":"Runs smoothly on petrol; shakes on LPG under low-RPM load","normalized":{}}],
      "dtcs":[{"id":"dtc-1","code":"P0302","description":"Cylinder 2 misfire","source":"manual"}],
      "evidence":[{"id":"e1","fact":"Misfire is reported only in LPG mode","source":"driver report","status":"reported","confidence":0.9}],
      "hypotheses":[
        {"id":"h1","category":"LPG fuel delivery / mixture","statement":"Verify LPG injector delivery and calibration","supporting_evidence_ids":["e1"],"contradicting_evidence_ids":[],"status":"possible"},
        {"id":"h2","category":"ignition / combustion","statement":"Compare ignition performance under both fuel modes","supporting_evidence_ids":["e1"],"contradicting_evidence_ids":[],"status":"possible"}
      ],
      "recommendations":[],
      "test_results":[],
      "audit_log":[]
    }
    """.utf8)
}

final class RequestRecorder { var paths: [String] = [] }

final class MockURLProtocol: URLProtocol {
    typealias Handler = (URLRequest) throws -> (statusCode: Int, data: Data)
    static var handler: Handler?
    static var lastRequest: URLRequest?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        Self.lastRequest = request
        do {
            let result = try XCTUnwrap(Self.handler)(request)
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: result.statusCode,
                httpVersion: "HTTP/1.1",
                headerFields: ["Content-Type": "application/json"]
            )!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: result.data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
