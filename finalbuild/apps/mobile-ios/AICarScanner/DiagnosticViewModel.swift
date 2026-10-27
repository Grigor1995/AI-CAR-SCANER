import Foundation
import SwiftUI

@MainActor
final class DiagnosticViewModel: ObservableObject {
    @Published var session: DiagnosticSession?
    @Published var history: [DiagnosticSession] = []
    @Published var liveRecords: [LiveRecord] = []
    @Published var liveDataError: String?
    @Published var liveDataLoading = false
    private var liveRequestID = UUID()
    private var liveRequestSessionID: String?
    @Published var catalog: [VehicleCatalogEntry] = SharedVehicleCatalog.offline()
    @Published var catalogOnline = false
    @Published var obdValues: [String: Double?] = [:]
    private let obdWifi = NativeObdWifiBridge()

    func readObdWifi(host: String, port: Int) async {
        do { obdValues = try await obdWifi.poll(host: host, port: port, api: api, sessionID: session?.session_id).values }
        catch {
            obdValues = [:]
            self.error = (error as? NativeObdWifiBridge.BridgeError)?.message(language:settings.language) ?? error.localizedDescription
        }
    }

    func disconnectObdWifi() async {
        let previous=obdTask;previous?.cancel();obdTask=nil
        obdRevision=UUID();obdRunning=false
        discoveryRevision=UUID();discovering=false
        await obdWifi.disconnect()
        await previous?.value
        obdValues=[:]
    }

    @Published var obdRunning = false
    @Published var discovery: DiscoveryResult?
    @Published var discovering=false
    private var discoveryRevision=UUID()
    private var obdTask: Task<Void,Never>?
    private var obdRevision = UUID()

    func startObdWifi(host:String,port:Int) {
        guard !obdRunning && !discovering else { return }
        let revision=UUID(); obdRevision=revision; obdRunning=true
        let sessionID=session?.session_id
        let previous=obdTask;previous?.cancel()
        obdTask=Task {
            await previous?.value
            defer { if obdRevision==revision { obdRunning=false } }
            while !Task.isCancelled && obdRevision==revision && session?.session_id==sessionID {
                do {
                    let snapshot=try await obdWifi.poll(host:host,port:port,api:api,sessionID:sessionID)
                    guard !Task.isCancelled && obdRevision==revision else { return }
                    obdValues=snapshot.values
                    await refreshLiveData()
                    try await Task.sleep(nanoseconds:1_200_000_000)
                } catch is CancellationError { return }
                catch { if obdRevision==revision { obdValues=[:]; self.error=error.localizedDescription }; return }
            }
        }
    }

    func identifyObdWifi(host:String,port:Int) async {
        guard !discovering else {return}
        await disconnectObdWifi()
        let revision=UUID();discoveryRevision=revision;discovering=true;discovery=nil
        defer {if discoveryRevision==revision {discovering=false}}
        do {let result=try await obdWifi.identify(host:host,port:port,api:api);if discoveryRevision==revision {discovery=result}}
        catch {if discoveryRevision==revision {self.error=error.localizedDescription}}
    }

    func startObdBLE(_ transport:OBDService) {
        guard !obdRunning && !discovering else {return}
        let revision=UUID();obdRevision=revision;obdRunning=true
        let id=session?.session_id
        let previous=obdTask;previous?.cancel()
        obdTask=Task {
            await previous?.value
            defer {if obdRevision==revision {obdRunning=false}}
            while !Task.isCancelled && obdRevision==revision && session?.session_id==id {
                do {
                    let snapshot=try await transport.read(api:api,session:id)
                    guard !Task.isCancelled && obdRevision==revision else {return}
                    obdValues=snapshot.values;await refreshLiveData()
                    try await Task.sleep(nanoseconds:1_200_000_000)
                } catch is CancellationError {return}
                catch {if obdRevision==revision {obdValues=[:];self.error=error.localizedDescription};return}
            }
        }
    }
    func identifyObdBLE(_ transport:OBDService) async {
        guard !discovering else {return}
        await disconnectObdWifi()
        let revision=UUID();discoveryRevision=revision;discovering=true;discovery=nil
        defer {if discoveryRevision==revision {discovering=false}}
        do {let result=try await transport.identify(api:api);if discoveryRevision==revision {discovery=result}}
        catch {if discoveryRevision==revision {self.error=error.localizedDescription}}
    }

    func changeBackend(_ url:String) async {
        guard let parts=URLComponents(string:url.trimmingCharacters(in:.whitespacesAndNewlines)),
              ["http","https"].contains(parts.scheme?.lowercased() ?? ""),parts.host != nil,
              parts.user==nil,parts.password==nil,parts.query==nil,parts.fragment==nil else {error=APIError.invalidURL.localizedDescription;return}
        await disconnectObdWifi();clearSession();history=[]
        settings.apiURL=url.trimmingCharacters(in:CharacterSet(charactersIn:"/ "))
        saveSettings();await loadCatalog()
    }

    func backendOperation(_ path:String,method:String="GET",body:[String:JSONValue]?=nil) async throws -> JSONValue {
        try await api.operation(path,method:method,body:body,language:settings.language.rawValue)
    }
    func reportData(format:String) async throws -> Data {
        guard let id=session?.session_id else { throw APIError.server(409,"Open a session") }
        return try await api.reportData(id,format:format,language:settings.language)
    }

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
        settings.usUnits = defaults.bool(forKey:"usUnits")
        settings.analogDisplay = defaults.object(forKey:"analogDisplay") as? Bool ?? true
        let savedAPIURL = defaults.string(forKey: "apiURL")
        if let savedAPIURL,
           !savedAPIURL.isEmpty {
            settings.apiURL = savedAPIURL
        } else {
            // A saved LAN/Simulator URL is an explicit user choice; preserve it.
            settings.apiURL = "https://ai-car-scaner.onrender.com"
        }
    }

    func saveSettings() {
        let defaults = self.defaults
        defaults.set(settings.language.rawValue, forKey: "language")
        defaults.set(settings.darkTheme, forKey: "darkTheme")
        defaults.set(settings.usUnits,forKey:"usUnits")
        defaults.set(settings.analogDisplay,forKey:"analogDisplay")
        defaults.set(settings.apiURL, forKey: "apiURL")
    }

    func loadCatalog() async {
        do {
            let server = try await api.vehicleCatalog()
            catalog = SharedVehicleCatalog.merge(server: server, offline: SharedVehicleCatalog.offline())
            catalogOnline = true
        } catch {
            catalog = SharedVehicleCatalog.offline()
            catalogOnline = false
        }
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

    func loadHistory() async {
        do { history = try await api.listSessions() }
        catch { self.error = error.localizedDescription }
    }

    func openSession(_ id: String) async {
        discoveryRevision=UUID();discovering=false;discovery=nil;obdValues=[:]
        obdRevision=UUID();obdTask?.cancel();obdRunning=false
        invalidateLiveRequest()
        liveRecords = []
        liveDataError = nil
        await execute { try await self.api.getSession(id, language: self.settings.language) }
    }

    func refreshLiveData() async {
        guard let id = session?.session_id else {
            invalidateLiveRequest()
            liveRecords = []
            liveDataError = nil
            return
        }
        if liveDataLoading && liveRequestSessionID == id { return }
        let requestID = UUID()
        liveRequestID = requestID
        liveRequestSessionID = id
        liveDataLoading = true
        defer { if liveRequestID == requestID { liveDataLoading = false } }
        do {
            let response = try await api.liveRecords(id)
            if liveRequestID == requestID && session?.session_id == id {
                liveRecords = response.records
                liveDataError = nil
            }
        } catch {
            guard liveRequestID == requestID && session?.session_id == id else { return }
            liveDataError = error.localizedDescription
        }
    }

    private func invalidateLiveRequest() {
        liveRequestID = UUID()
        liveRequestSessionID = nil
        liveDataLoading = false
    }

    func clearSession() {
        discoveryRevision=UUID();discovering=false;discovery=nil
        obdRevision=UUID();obdTask?.cancel();obdRunning=false
        obdValues=[:]
        invalidateLiveRequest()
        liveDataError = nil
        liveRecords = []
        session = nil
        error = nil
    }

    private func execute(
        _ operation: @escaping () async throws -> DiagnosticSession
    ) async {
        loading = true
        error = nil

        do {
            let result = try await operation()
            if session?.session_id != result.session_id {
                discoveryRevision=UUID();discovering=false;discovery=nil
                obdRevision=UUID();obdTask?.cancel();obdRunning=false;obdValues=[:]
                invalidateLiveRequest()
                liveRecords = []
                liveDataError = nil
            }
            session = result
        } catch {
            self.error = error.localizedDescription
        }

        loading = false
    }
}
