import Foundation
import XCTest
@testable import AICarScanner

final class DiagnosticAPIErrorPathTests: XCTestCase {
    override func tearDown() {
        MockURLProtocol.handler = nil
        MockURLProtocol.lastRequest = nil
        super.tearDown()
    }

    func testRejectsNonHTTPBackendURL() async {
        let api = DiagnosticAPI(baseURL: "file:///tmp/not-an-api")
        do {
            _ = try await api.vehicleCatalog()
            XCTFail("Expected invalid backend URL to fail")
        } catch let error as APIError {
            if case .invalidURL = error {
                XCTAssertEqual(error.localizedDescription, "Invalid backend URL")
            } else {
                XCTFail("Unexpected API error: \(error)")
            }
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func testHTTPErrorPreservesStatusAndResponseBody() async {
        MockURLProtocol.handler = { _ in (503, Data("service unavailable".utf8)) }
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        let api = DiagnosticAPI(
            baseURL: "https://unit.test",
            session: URLSession(configuration: configuration)
        )

        do {
            _ = try await api.vehicleCatalog()
            XCTFail("Expected backend failure to throw")
        } catch let APIError.server(code, body) {
            XCTAssertEqual(code, 503)
            XCTAssertEqual(body, "service unavailable")
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func testMalformedBaseURLDoesNotIssueNetworkRequest() async {
        let api = DiagnosticAPI(baseURL: "://invalid")
        do {
            _ = try await api.vehicleCatalog()
            XCTFail("Expected malformed URL to fail")
        } catch let error as APIError {
            if case .invalidURL = error {
                XCTAssertNil(MockURLProtocol.lastRequest)
            } else {
                XCTFail("Unexpected API error: \(error)")
            }
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
}
