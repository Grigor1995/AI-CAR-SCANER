import Foundation
import SwiftUI

@MainActor
final class DiagnosticViewModel: ObservableObject {
    @Published var session: DiagnosticSession?
    @Published var catalog: [VehicleCatalogEntry] = []
    @Published var loading = false
    @Published var error: String?
    @Published var settings = AppSettings()

    private var api: DiagnosticAPI {
        DiagnosticAPI(baseURL: settings.apiURL)
    }

    init() {
        loadSettings()
        Task { await loadCatalog() }
    }

    func loadSettings() {
        let defaults = UserDefaults.standard
        if let raw = defaults.string(forKey: "language"),
           let language = AppLanguage(rawValue: raw) {
            settings.language = language
        }
        settings.darkTheme = defaults.object(forKey: "darkTheme") as? Bool ?? true
        settings.apiURL = defaults.string(forKey: "apiURL") ?? settings.apiURL
    }

    func saveSettings() {
        let defaults = UserDefaults.standard
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
