import SwiftUI

@main
struct AICarScannerApp: App {
    @StateObject private var model = DiagnosticViewModel()
    var body: some Scene {
        WindowGroup {
            DiagnosticScreen(viewModel: model)
                .preferredColorScheme(model.settings.darkTheme ? .dark : .light)
        }
    }
}