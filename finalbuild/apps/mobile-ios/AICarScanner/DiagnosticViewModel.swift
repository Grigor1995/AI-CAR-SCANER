import Foundation
import SwiftUI

@MainActor
final class DiagnosticViewModel: ObservableObject {
    @Published var session: DiagnosticSession?
    @Published var catalog:[VehicleCatalogEntry]=[]
    @Published var loading=false
    @Published var error:String?
    @Published var settings=AppSettings()
    private var api:DiagnosticAPI { DiagnosticAPI(baseURL:settings.apiURL) }

    init(){ loadSettings(); Task { await loadCatalog() } }
    func loadSettings(){
        let d=UserDefaults.standard
        if let x=d.string(forKey:"language"),let l=AppLanguage(rawValue:x){settings.language=l}
        settings.darkTheme=d.object(forKey:"darkTheme") as? Bool ?? true
        settings.apiURL=d.string(forKey:"apiURL") ?? settings.apiURL
    }
    func saveSettings(){let d=UserDefaults.standard;d.set(settings.language.rawValue,forKey:"language");d.set(settings.darkTheme,forKey:"darkTheme");d.set(settings.apiURL,forKey:"apiURL")}
    func loadCatalog() async { catalog=(try? await api.vehicleCatalog()) ?? [] }
    func newSession(_ v:Vehicle) async { await execute{try await self.api.createSession(v)} }
    func updateVehicle(_ v:Vehicle) async { guard let id=session?.session_id else{return};await execute{try await self.api.updateVehicle(id,v)} }
    func addSymptom(_ x:String) async {guard let id=session?.session_id else{return};await execute{try await self.api.addSymptom(id,x)}}
    func updateSymptom(_ x:Symptom,_ value:String) async {guard let id=session?.session_id else{return};await execute{try await self.api.updateSymptom(id,x.id,value)}}\n    func deleteSymptom(_ x:Symptom) async {guard let id=session?.session_id else{return};await execute{try await self.api.deleteSymptom(id,x.id)}}
    func addDTC(_ x:String) async {guard let id=session?.session_id else{return};await execute{try await self.api.addDTC(id,x)}}
    func deleteDTC(_ x:DTC) async {guard let id=session?.session_id,let did=x.id else{return};await execute{try await self.api.deleteDTC(id,did)}}
    func analyze() async {guard let id=session?.session_id else{return};await execute{try await self.api.analyze(id,self.settings.language)}}
    func recordTest(_ x:Recommendation,_ result:String,_ notes:String?) async {guard let id=session?.session_id else{return};await execute{try await self.api.recordTest(id,x,result,notes,self.settings.language)}}
    func clearSession(){session=nil}
    private func execute(_ op:@escaping()async throws->DiagnosticSession)async{loading=true;error=nil;do{session=try await op()}catch{self.error=error.localizedDescription};loading=false}
}