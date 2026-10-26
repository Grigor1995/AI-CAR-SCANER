import Foundation
import XCTest
@testable import AICarScanner

final class ObdBridgeAPITests: XCTestCase {
    override func tearDown() {
        MockURLProtocol.handler = nil
        MockURLProtocol.lastRequest = nil
        super.tearDown()
    }

    private func api() -> DiagnosticAPI {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        return DiagnosticAPI(baseURL: "https://unit.test", session: URLSession(configuration: configuration))
    }

    func testPollingPlanIsReceivedFromBackend() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.url?.path, "/api/v1/obd/plan")
            return (200, Data(#"{"initialization":["ATSP6"],"commands":["010C"]}"#.utf8))
        }
        let plan = try await api().obdPlan()
        XCTAssertEqual(plan.initialization, ["ATSP6"])
        XCTAssertEqual(plan.commands, ["010C"])
    }

    func testObservedCapabilitiesAreSentToBackendForSelection() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.url?.path, "/api/v1/obd/plan")
            XCTAssertEqual(request.httpMethod, "POST")
            return (200, Data(#"{"initialization":[],"commands":["010C"],"discovery":[],"supported_pids":[12]}"#.utf8))
        }
        let plan = try await api().supportedObdPlan(["0100":"410000100000"])
        XCTAssertEqual(plan.commands,["010C"])
    }

    func testRawFramesUseBackendDecodedValues() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.url?.path, "/api/v1/obd/decode")
            XCTAssertEqual(request.httpMethod, "POST")
            return (200, Data(#"{"values":{"rpm":1234.5,"coolant_c":null},"errors":{"0105":"NO DATA"}}"#.utf8))
        }
        let result = try await api().decodeObd(["010C": "raw bytes"])
        XCTAssertEqual(result.values["rpm"]!, 1234.5)
        XCTAssertEqual(result.errors["0105"], "NO DATA")
    }
}
