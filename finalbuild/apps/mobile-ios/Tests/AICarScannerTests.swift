import XCTest
@testable import AICarScanner

final class AICarScannerTests: XCTestCase {
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
}