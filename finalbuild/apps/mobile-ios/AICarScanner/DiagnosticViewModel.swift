import Foundation
import SwiftUI

@MainActor
final class DiagnosticViewModel: ObservableObject {
    @Published var session: DiagnosticSession?
    @Published var catalog: [VehicleCatalogEntry] = []
    @Published var loading = false
    @Published var error: String?
    @Published var settings = AppSettings()

    private let apiSession: URLSession?
    private let defaults: UserDefaults

    private var api: DiagnosticAPI {
        DiagnosticAPI(baseURL: settings.apiURL, session: apiSession ?? .shared)
    }

    init(
        apiSession: URLSession? = nil,
        defaults: UserDefaults = .standard,
        loadCatalogOnInit: Bool = true
    ) {
        self.apiSession = apiSession
        self.defaults = defaults
        loadSettings()
        if loadCatalogOnInit {
            Task { await loadCatalog() }
        }
    }

    func loadSettings() {
        let defaults = self.defaults
        if let raw = defaults.string(forKey: "language"),
           let language = AppLanguage(rawValue: raw) {
            settings.language = language
        }
        settings.darkTheme = defaults.object(forKey: "darkTheme") as? Bool ?? true
        let savedAPIURL = defaults.string(forKey: "apiURL")
        if let savedAPIURL,
           !savedAPIURL.isEmpty,
           !savedAPIURL.contains("127.0.0.1:8001"),
           !savedAPIURL.contains("localhost:8001") {
            settings.apiURL = savedAPIURL
        } else {
            // Upgrade existing installs that persisted the simulator-only URL.
            settings.apiURL = "https://ai-car-scaner.onrender.com"
        }
    }

    func saveSettings() {
        let defaults = self.defaults
        defaults.set(settings.language.rawValue, forKey: "language")
        defaults.set(settings.darkTheme, forKey: "darkTheme")
        defaults.set(settings.apiURL, forKey: "apiURL")
    }

    func loadCatalog() async {
        catalog = (try? await api.vehicleCatalog()) ?? []
    }

    func newSession(_ vehicle: Vehicle) async {
        await execute {
            try await self.api.createSession(vehicle)
        }
    }

    func updateVehicle(_ vehicle: Vehicle) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.updateVehicle(id, vehicle)
        }
    }

    func addSymptom(_ value: String) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.addSymptom(id, value)
        }
    }

    func updateSymptom(_ symptom: Symptom, _ value: String) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.updateSymptom(id, symptom.id, value)
        }
    }

    func deleteSymptom(_ symptom: Symptom) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.deleteSymptom(id, symptom.id)
        }
    }

    func addDTC(_ code: String) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.addDTC(id, code)
        }
    }

    func updateDTC(_ dtc: DTC, _ code: String) async {
        guard let id = session?.session_id, let dtcID = dtc.id else { return }
        await execute {
            try await self.api.updateDTC(id, dtcID, code, dtc.description, dtc.source)
        }
    }

    func deleteDTC(_ dtc: DTC) async {
        guard let id = session?.session_id, let dtcID = dtc.id else { return }
        await execute {
            try await self.api.deleteDTC(id, dtcID)
        }
    }

    func analyze() async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.analyze(id, self.settings.language)
        }
    }

    func recordTest(_ recommendation: Recommendation, _ result: String, _ notes: String?) async {
        guard let id = session?.session_id else { return }
        await execute {
            try await self.api.recordTest(
                id,
                recommendation,
                result,
                notes,
                self.settings.language
            )
        }
    }

    func clearSession() {
        session = nil
    }

    private func execute(
        _ operation: @escaping () async throws -> DiagnosticSession
    ) async {
        loading = true
        error = nil

        do {
            session = try await operation()
        } catch {
            self.error = error.localizedDescription
        }

        loading = false
    }
}
