import XCTest
@testable import AICarScanner

final class LauncherOrderTests: XCTestCase {
    func testDiagnosticsCanBecomeFirstWithoutChangingWorkflowIds() {
        let defaults=[11,1,3,0,8]
        let moved=LauncherOrder.moving(defaults,source:1,target:11)
        XCTAssertEqual(moved,[1,11,3,0,8])
        XCTAssertEqual(Set(moved),Set(defaults))
        let saved=moved.map(String.init).joined(separator:",")
        XCTAssertEqual(LauncherOrder.normalized(saved,defaults:defaults),moved)
    }
    func testOldOrCorruptPreferencesCannotRemoveANewSection() {
        XCTAssertEqual(LauncherOrder.normalized("1,1,999,bad,11",defaults:[11,1,3,8]),[1,11,3,8])
        XCTAssertEqual(LauncherOrder.moving([11,1,3],source:999,target:1),[11,1,3])
    }
}
