import Foundation
import XCTest
@testable import AICarScanner
final class NativeParityTests:XCTestCase {
    func testDisplayConversionsKeepOriginalMeasurementsAndNormalBand() {
        let eu=DisplaySignal(name:"coolant_temp",unit:"°C",values:[92,102],us:false)
        let us=DisplaySignal(name:"coolant_temp",unit:"°C",values:[92,102],us:true)
        XCTAssertEqual(eu.values,[92,102]);XCTAssertEqual(us.values[0],197.6,accuracy:0.001)
        XCTAssertEqual(us.bands[2].0,197.6,accuracy:0.001);XCTAssertEqual(us.bands[2].1,215.6,accuracy:0.001)
        XCTAssertEqual(DisplaySignal(name:"Speed",unit:"km/h",values:[160.9344],us:true).values[0],100,accuracy:0.001)
        XCTAssertEqual(DisplaySignal(name:"stft",unit:"%",values:[-5],us:false).bounds.lowerBound,-100)
    }
    func testOperationPreservesSIAndSelectedLanguage() async throws {
        let configuration=URLSessionConfiguration.ephemeral;configuration.protocolClasses=[MockURLProtocol.self]
        let api=DiagnosticAPI(baseURL:"https://unit.test",session:URLSession(configuration:configuration))
        defer {MockURLProtocol.handler=nil}
        MockURLProtocol.handler={request in
            XCTAssertEqual(request.httpMethod,"PUT")
            XCTAssertEqual(request.url?.path,"/api/v1/acquisition/sessions/case/simulator/parameters")
            XCTAssertEqual(URLComponents(url:request.url!,resolvingAgainstBaseURL:false)?.queryItems?.first?.value,"hy")
            return (200,Data("{}".utf8))
        }
        _ = try await api.operation("/api/v1/acquisition/sessions/case/simulator/parameters",method:"PUT",body:["coolant_c":.number(98)],language:"hy")
    }
    func testDiscoveryComesFromBackend() async throws {
        let configuration=URLSessionConfiguration.ephemeral;configuration.protocolClasses=[MockURLProtocol.self]
        let api=DiagnosticAPI(baseURL:"https://unit.test",session:URLSession(configuration:configuration))
        defer {MockURLProtocol.handler=nil}
        MockURLProtocol.handler={request in
            XCTAssertEqual(request.url?.path,"/api/v1/obd/discovery/plan")
            return (200,Data(#"{"commands":["0902"],"restore":["ATH0"]}"#.utf8))
        }
        let plan=try await api.discoveryPlan();XCTAssertEqual(plan.commands,["0902"])
    }
    func testPrivateBackendOutputStripsNestedSessionIDs() throws {
        let value=try JSONDecoder().decode(JSONValue.self,from:Data(#"{"session_id":"secret","rows":[{"session_id":"secret","rpm":1000}]}"#.utf8))
        XCTAssertFalse(value.pretty.contains("secret"));XCTAssertTrue(value.pretty.contains("1000"))
    }
}
