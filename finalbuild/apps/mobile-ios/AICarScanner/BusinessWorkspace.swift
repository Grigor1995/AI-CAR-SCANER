import SwiftUI
import Foundation

private final class BusinessNoRedirect: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session:URLSession, task:URLSessionTask, willPerformHTTPRedirection response:HTTPURLResponse, newRequest request:URLRequest, completionHandler:@escaping (URLRequest?)->Void) {completionHandler(nil)}
}

/// Read-only authenticated account browser. No bearer/password persistence.
struct BusinessWorkspace: View {
    let baseURL:String
    @AppStorage("business_backend_url") private var savedBackendURL=""
    @State private var endpoint=""
    var fixedWorkspace:String? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var businessName=""
    @State private var address=""
    @State private var onboarding=false
    @State private var fullName=""
    @State private var email=""
    @State private var password=""
    @State private var token=""
    @State private var modes:[String]=[]
    @State private var pages:[BusinessPage]=[]
    @State private var language="en"
    @State private var output=""
    @State private var busy=false
    @State private var task:Task<Void,Never>?
    private let prefix="/api/v2/ecosystem"
    struct BusinessPage:Identifiable { let id:String;let label:String;let path:String }
    private func request(_ path:String,_ method:String="GET",_ data:[String:String]?=nil,_ bearer:String?=nil) async throws -> JSONValue {
        guard path.hasPrefix(prefix+"/"),let url=URL(string:endpoint.trimmingCharacters(in:CharacterSet(charactersIn:"/"))+path) else {throw URLError(.badURL)}
        guard ["http","https"].contains(url.scheme ?? ""),url.host != nil,url.user == nil,url.password == nil,url.query == nil,url.fragment == nil else {throw URLError(.badURL)}
        var req=URLRequest(url:url);req.httpMethod=method;req.timeoutInterval=15
        let access=bearer ?? token
        if !access.isEmpty {req.setValue("Bearer "+access,forHTTPHeaderField:"Authorization")}
        if method != "GET" {req.setValue("application/json",forHTTPHeaderField:"Content-Type");req.httpBody=try JSONSerialization.data(withJSONObject:data ?? [:])}
        let transport=URLSession(configuration:.ephemeral,delegate:BusinessNoRedirect(),delegateQueue:nil)
        defer {transport.finishTasksAndInvalidate()}
        let (bytes,response)=try await transport.data(for:req)
        let result=bytes.isEmpty ? JSONValue.object([:]) : try JSONDecoder().decode(JSONValue.self,from:bytes)
        guard let http=response as? HTTPURLResponse,(200..<300).contains(http.statusCode) else {throw NSError(domain:"BusinessAPI",code:(response as? HTTPURLResponse)?.statusCode ?? 0,userInfo:[NSLocalizedDescriptionKey:result["detail"].text])}
        return result
    }
    private func run(_ block:@escaping () async throws -> Void) {
        guard !busy else{return};busy=true
        task=Task { @MainActor in
            defer {busy=false}
            do{try await block()}catch is CancellationError {}catch{output=error.localizedDescription}
        }
    }
    var body:some View {
        NavigationStack {
            ScrollView { VStack(alignment:.leading,spacing:12) {
                Text("Account workspace • ecosystem backend required").font(.caption)
                if token.isEmpty {
                    TextField("Backend URL",text:$endpoint).textInputAutocapitalization(.never).disabled(busy)
                    TextField("Full name",text:$fullName)
                    TextField("Email",text:$email).textInputAutocapitalization(.never)
                    SecureField("Password",text:$password)
                    Button("Create account"){let secret=password;password="";run {output=try await request(prefix+"/accounts","POST",["email":email,"password":secret,"full_name":fullName],"").pretty}}.buttonStyle(.bordered).disabled(busy)
                    Button("Sign in") {let secret=password;password="";run {
                        let result=try await request(prefix+"/auth/login","POST",["email":email,"password":secret],"")
                        savedBackendURL=endpoint
                        token=result["access_token"].text
                        let account=try await request(prefix+"/me")
                        let authorized=(account["modes"].items+account["portals"].items).map{$0.text}
                        modes=fixedWorkspace == nil ? authorized : authorized.filter{$0==fixedWorkspace}
                        onboarding=(fixedWorkspace=="CUSTOMER" || fixedWorkspace=="MARKET") && modes.isEmpty()
                        output=account.pretty
                    }}.buttonStyle(.borderedProminent).disabled(busy)
                } else {
                    Picker("Language",selection:$language){ForEach(["en","hy","ru","fr"],id:\.self){Text($0)}}.pickerStyle(.segmented)
                    if onboarding {
                        TextField("Business name",text:$businessName)
                        TextField("Business address",text:$address)
                        Button(fixedWorkspace=="CUSTOMER" ? "Register workshop" : "Register shop"){run {
                            _ = try await request(prefix+(fixedWorkspace=="CUSTOMER" ? "/service-centers" : "/merchants"),"POST",["name":businessName,"address":address])
                            modes=[fixedWorkspace!];onboarding=false
                        }}.buttonStyle(.borderedProminent).disabled(busy)
                    }
                    ForEach(modes,id:\.self) {mode in
                        Button(mode) {run {
                            let nav=try await request(prefix+"/navigation?workspace="+mode+"&language="+language)
                            pages=nav["pages"].items.map {BusinessPage(id:$0["key"].text,label:$0["label"].text,path:$0["path"].text)}
                        }}.buttonStyle(.bordered).disabled(busy)
                    }
                    ForEach(pages) {page in Button(page.label){run {output=try await request(page.path).pretty}}.buttonStyle(.bordered).disabled(busy)}
                    Button("Sign out"){run {defer{token="";modes=[];pages=[];output=""};_ = try await request(prefix+"/auth/logout","POST")}}.disabled(busy)
                }
                if busy {ProgressView()}
                Text(output).font(.caption.monospaced()).textSelection(.enabled)
            }.padding().modifier(AutomotiveCardStyle()) }
            .background(AutomotivePalette.navy).navigationTitle("AI Car Scanner • "+(fixedWorkspace ?? "Account workspace"))
            .toolbar {Button("Close"){dismiss()}}
        }.onAppear {if endpoint.isEmpty {endpoint=savedBackendURL.isEmpty ? baseURL : savedBackendURL}}.onDisappear {task?.cancel();token="";password=""}
    }
}
