import SwiftUI

@main
struct AICarScannerApp: App {
    @StateObject private var model = DiagnosticViewModel()
    var body: some Scene {
        WindowGroup {
            BusinessWorkspace(baseURL:Bundle.main.object(forInfoDictionaryKey:"AICarBackendURL") as? String ?? "http://127.0.0.1:8001",fixedWorkspace:Bundle.main.object(forInfoDictionaryKey:"AICarWorkspace") as? String ?? "USER")
                .preferredColorScheme(model.settings.darkTheme ? .dark : .light)
        }
    }
}