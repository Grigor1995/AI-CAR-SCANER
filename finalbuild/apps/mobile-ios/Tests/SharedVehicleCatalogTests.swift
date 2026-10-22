
import Foundation
import XCTest
@testable import AICarScanner

final class SharedVehicleCatalogTests: XCTestCase {
    func testBundledOfflineCatalogContainsDesktopReferenceVehicle() {
        let rows = SharedVehicleCatalog.offline()
        XCTAssertFalse(rows.isEmpty, "Shared catalog JSON must be bundled as a folder resource")
        XCTAssertTrue(rows.contains { $0.make == "Mercedes-Benz" && $0.model == "E-Class" &&
            $0.chassis == "W211" && $0.year == 2006 && $0.engine == "M272 E35 3.5" })
    }

    func testServerWinsForMatchingSnapshotFitment() {
        let offline = SharedVehicleCatalog.offline()
        guard let first = offline.first else { return XCTFail("Missing offline catalog") }
        let authoritative = VehicleCatalogEntry(make: first.make, model: first.model,
            chassis: first.chassis, year: first.year, engine: first.engine, ecu: first.ecu,
            fuel: ["petrol"], source: "backend", scope: "verified")
        let result = SharedVehicleCatalog.merge(server: [authoritative], offline: offline)
        XCTAssertEqual(result.first?.source, "backend")
        XCTAssertEqual(result.count, offline.count)
    }
}
