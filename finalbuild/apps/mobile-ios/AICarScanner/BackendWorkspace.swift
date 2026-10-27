import SwiftUI

/// Flexible backend responses: never duplicate diagnostic calculations in the UI.
enum JSONValue: Codable {
    case object([String:JSONValue]), array([JSONValue]), string(String), number(Double), bool(Bool), null
    init(from decoder:Decoder) throws {
        let c=try decoder.singleValueContainer()
        if c.decodeNil() { self = .null }
        else if let v=try? c.decode(Bool.self) { self = .bool(v) }
        else if let v=try? c.decode(Double.self) { self = .number(v) }
        else if let v=try? c.decode(String.self) { self = .string(v) }
        else if let v=try? c.decode([String:JSONValue].self) { self = .object(v) }
        else { self = .array(try c.decode([JSONValue].self)) }
    }
    func encode(to encoder:Encoder) throws {
        var c=encoder.singleValueContainer()
        switch self {
        case .object(let v):try c.encode(v)
        case .array(let v):try c.encode(v)
        case .string(let v):try c.encode(v)
        case .number(let v):try c.encode(v)
        case .bool(let v):try c.encode(v)
        case .null:try c.encodeNil()
        }
    }
    subscript(_ key:String)->JSONValue { if case .object(let d)=self { return d[key] ?? .null };return .null }
    var text:String { if case .string(let s)=self { return s };return "" }
    var items:[JSONValue] { if case .array(let a)=self {return a};return [] }
    var privateValue:JSONValue {
        switch self {
        case .object(let o): return .object(o.filter { !["session_id","connected_device_id"].contains($0.key) }.mapValues { $0.privateValue })
        case .array(let a): return .array(a.map { $0.privateValue })
        default:return self
        }
    }
    var pretty:String {
        let encoder=JSONEncoder();encoder.outputFormatting=[.prettyPrinted,.sortedKeys,.withoutEscapingSlashes]
        return (try? String(decoding:encoder.encode(privateValue),as:UTF8.self)) ?? ""
    }
}

struct BackendWorkspace:View {
    @ObservedObject var model:DiagnosticViewModel
    let mode:String
    @State private var expanded=false
    @State private var busy=false
    @State private var output=""
    @State private var task:Task<Void,Never>?
    @State private var title=""
    @State private var note=""
    @State private var devices:[JSONValue]=[]
    @State private var host=""
    @State private var port="35000"
    @State private var pendingDelete:JSONValue?
    @State private var profiles:[JSONValue]=[]
    @State private var rpm="750"
    @State private var coolant="90"
    @State private var speed="40"
    @State private var throttle="32"
    @State private var exportURL:URL?
    private var t:T { T(language:model.settings.language) }
    private var sid:String? {model.session?.session_id}
    private func run(_ block:@escaping () async throws -> String) {
        guard !busy else { return }; busy=true;output=""
        task=Task { @MainActor in
            defer {busy=false}
            do {let result=try await block();try Task.checkCancellation();output=result}
            catch is CancellationError {}
            catch {output=error.localizedDescription}
        }
    }
    private func operation(_ path:String,_ method:String="GET",_ body:[String:JSONValue]?=nil) async throws -> String {
        let value=try await model.backendOperation(path,method:method,body:body)
        return value.pretty.replacingOccurrences(of:sid ?? "\u{0}",with:"[internal]")
    }
    private var heading:String {
        switch mode {
        case "live":return t.tr("Acquisition / telemetry","Сбор / телеметрия","Հավաքում / վերլուծություն")
        case "decision":return t.tr("Diagnostic plan","План диагностики","Ախտորոշման պլան")
        case "network":return t.tr("ECU network","Сеть ЭБУ","ECU ցանց")
        case "teach":return t.tr("Send repair reference","Отправить материал ремонта","Ուղարկել վերանորոգման նյութ")
        case "devices":return t.tr("Server adapters","Адаптеры сервера","Սերվերի ադապտերներ")
        case "profiles":return t.tr("Shared vehicles","Общие автомобили","Ընդհանուր մեքենաներ")
        default:return t.tr("Export report","Экспорт отчёта","Արտահանել հաշվետվություն")
        }
    }
    var body:some View {
        DisclosureGroup(isExpanded:$expanded) {
        VStack(alignment:.leading,spacing:12) {
            if busy { ProgressView() }
            if mode=="devices" {
                Text(t.tr("Server adapters, including USB. Phone-local BLE and Wi-Fi use VCI.","Адаптеры сервера, включая USB. Локальные BLE/Wi-Fi — в VCI.","Սերվերի ադապտերներ՝ ներառյալ USB։ Հեռախոսի BLE/Wi-Fi՝ VCI-ում։")).font(.caption)
                Button(t.tr("Refresh adapters","Обновить адаптеры","Թարմացնել ադապտերները")) {run {devices=try await model.backendOperation("/api/v1/devices")["devices"].items;return ""}}
                ForEach(["usb","ble"],id:\.self) { transport in
                    Button(t.tr("Scan","Поиск","Որոնել")+" "+transport.uppercased()) {run {
                        let result=try await operation("/api/v1/devices/scan/"+transport,"POST",["timeout":.number(3)])
                        devices=try await model.backendOperation("/api/v1/devices")["devices"].items;return result
                    }}
                }
                TextField(t.tr("Wi-Fi host","Адрес Wi-Fi","Wi-Fi հասցե"),text:$host).textInputAutocapitalization(.never)
                TextField(t.tr("Port","Порт","Պորտ"),text:$port)
                Button(t.tr("Find Wi-Fi adapter","Найти Wi-Fi адаптер","Գտնել Wi-Fi ադապտերը")) {run {
                    guard let n=Int(port),(1...65535).contains(n) else {throw APIError.invalidURL}
                    let result=try await operation("/api/v1/devices/wifi/probe","POST",["host":.string(host),"port":.number(Double(n))])
                    devices=try await model.backendOperation("/api/v1/devices")["devices"].items;return result
                }}.disabled(host.isEmpty)
                ForEach(Array(devices.enumerated()),id:\.offset) {_,device in
                    let deviceID=device["device_id"].text
                    Text(device["model"].text.isEmpty ? deviceID : device["model"].text)
                    Button(t.tr("Connect","Подключить","Միացնել")) {run {try await operation("/api/v1/devices/"+deviceID+"/connect","POST",["config":.object([:])])}}
                    Button(t.tr("Disconnect","Отключить","Անջատել")) {run {try await operation("/api/v1/devices/"+deviceID+"/disconnect","POST")}}
                    Button(t.tr("Identify vehicle","Определить автомобиль","Նույնականացնել մեքենան")) {run {try await operation("/api/v1/devices/"+deviceID+"/diagnostic-discovery","POST",["config":.object([:])])}}
                    if let id=sid {
                        Button(t.tr("Start Live Data","Запустить данные","Գործարկել տվյալները")) {run {try await operation("/api/v1/acquisition/sessions/"+id+"/start","POST",["adapter":.string("bound"),"device_id":.string(deviceID)])}}
                    }
                }
            } else if mode=="profiles" {
                Text(t.tr("Shared vehicles","Общие автомобили","Ընդհանուր մեքենաներ")).font(.headline)
                Button(t.tr("Refresh vehicles","Обновить автомобили","Թարմացնել մեքենաները")) { run {profiles=try await model.backendOperation("/api/v1/vehicle-profiles").items;return ""} }
                if let vehicle=model.session?.vehicle {
                    Button(t.tr("Save current vehicle","Сохранить автомобиль","Պահպանել ընթացիկ մեքենան")) {run {
                        let encoded=try JSONEncoder().encode(vehicle); let json=try JSONDecoder().decode(JSONValue.self,from:encoded)
                        _ = try await model.backendOperation("/api/v1/vehicle-profiles",method:"POST",body:["name":.string(""),"vehicle":json])
                        profiles=try await model.backendOperation("/api/v1/vehicle-profiles").items;return ""
                    }}
                }
                ForEach(Array(profiles.enumerated()),id:\.offset) { _,profile in
                    Text(profile["vehicle"]["make"].text+" "+profile["vehicle"]["model"].text)
                    HStack {
                        Button(t.tr("Use","Выбрать","Ընտրել")) {run {
                            let vehicle=try JSONDecoder().decode(Vehicle.self,from:JSONEncoder().encode(profile["vehicle"]))
                            await model.newSession(vehicle);return model.error ?? ""
                        }}
                        if let vehicle=model.session?.vehicle {
                            Button(t.tr("Replace with current","Заменить текущим","Փոխարինել ընթացիկով")) {run {
                                let json=try JSONDecoder().decode(JSONValue.self,from:JSONEncoder().encode(vehicle))
                                _ = try await model.backendOperation("/api/v1/vehicle-profiles/"+profile["id"].text,method:"PUT",body:["name":profile["name"],"vehicle":json])
                                profiles=try await model.backendOperation("/api/v1/vehicle-profiles").items;return ""
                            }}
                        }
                        Button(t.tr("Delete","Удалить","Ջնջել"),role:.destructive) {pendingDelete=profile}
                    }
                }
            } else if mode=="teach" {
                TextField(t.tr("Title","Название","Վերնագիր"),text:$title)
                TextField(t.tr("Verified repair / measurements","Подтверждённый ремонт / измерения","Հաստատված վերանորոգում / չափումներ"),text:$note,axis:.vertical).lineLimit(3...8)
                Text(t.tr("Reference ingestion; no model training","Справочные материалы; без обучения модели","Տեղեկատու նյութի ավելացում․ մոդելը չի ուսուցանվում")).font(.caption)
                Button(t.tr("Send to backend","Отправить на сервер","Ուղարկել backend-ին")) {run {
                    try await operation("/api/v1/knowledge/ingest/text","POST",["title":.string(title),"text":.string(note),"metadata":.object(["source":.string("user-reported-repair"),"document_type":.string("repair_note")])])
                }}.disabled(title.isEmpty || note.isEmpty)
            } else if let id=sid {
                if mode=="live" {
                    Text(t.tr("Simulator values are SI; never change a real vehicle.","Параметры симулятора в СИ; реальный автомобиль не изменяется.","Սիմուլյատորի արժեքները SI են․ իրական մեքենան չեն փոխում։")).font(.caption)
                    Button(t.tr("Start simulator","Запустить симулятор","Գործարկել սիմուլյատորը")) {run {try await operation("/api/v1/acquisition/sessions/"+id+"/start","POST",["adapter":.string("simulator")])}}
                    Button(t.tr("Start server-connected adapter","Запустить адаптер сервера","Գործարկել սերվերի ադապտերը")) {run {try await operation("/api/v1/acquisition/sessions/"+id+"/start","POST",["adapter":.string("bound")])}}
                    TextField("RPM",text:$rpm)
                    TextField(t.tr("Coolant °C","Охлаждение °C","Հովացուցիչ °C"),text:$coolant)
                    TextField(t.tr("Speed km/h","Скорость км/ч","Արագություն կմ/ժ"),text:$speed)
                    TextField(t.tr("Throttle %","Дроссель %","Դրոսել %"),text:$throttle)
                    Button(t.tr("Apply simulator values","Применить параметры","Կիրառել սիմուլյատորի արժեքները")) {run {
                        let fields=["rpm":rpm,"coolant_c":coolant,"speed_kmh":speed,"throttle_percent":throttle]
                        var values:[String:JSONValue]=[:]
                        for (key,text) in fields {guard let n=Double(text),n.isFinite else {throw APIError.server(422,"Invalid number")};values[key] = .number(n)}
                        return try await operation("/api/v1/acquisition/sessions/"+id+"/simulator/parameters","PUT",values)
                    }}
                    Button(t.tr("Stop acquisition","Остановить сбор","Դադարեցնել հավաքումը")) {run {try await operation("/api/v1/acquisition/sessions/"+id+"/stop","POST")}}
                    Button(t.tr("Telemetry summary","Сводка телеметрии","Տվյալների ամփոփում")) {run {try await operation("/api/v1/telemetry/sessions/"+id+"/summary")}}
                    Button(t.tr("Analyze telemetry","Анализ телеметрии","Վերլուծել տվյալները")) {run {let result=try await operation("/api/v1/telemetry/sessions/"+id+"/analyze","POST");await model.analyze();return result}}
                    Button(t.tr("AI live analysis","ИИ-анализ данных","AI տվյալների վերլուծություն")) {run {try await operation("/api/v1/telemetry/sessions/"+id+"/ai-analyze-live","POST")}}
                } else if mode=="decision" {
                    Button(t.tr("Refresh plan / missing information","Обновить план / недостающие данные","Թարմացնել պլանը / բացակայող տվյալները")) {run {try await operation("/api/v1/decision/sessions/"+id+"/plan")}}
                    Button(t.tr("AI provider status","Состояние ИИ","AI ծառայության վիճակ")) {run {try await operation("/api/v1/ai/provider")}}
                } else if mode=="network" {
                    Button(t.tr("Refresh ECU map","Обновить карту ЭБУ","Թարմացնել ECU քարտեզը")) {run {try await operation("/api/v1/network-discovery/sessions/"+id+"/map")}}
                    Button(t.tr("Active read-only probe","Активный опрос без записи","Ակտիվ միայն ընթերցման հարցում")) {run {try await operation("/api/v1/network-discovery/sessions/"+id+"/active-probe","POST",[:])}}
                } else {
                    ForEach(["pdf","json"],id:\.self) { format in
                        Button(t.tr("Export","Экспорт","Արտահանել")+" "+format.uppercased()) {run {
                            let data=try await model.reportData(format:format)
                            try Task.checkCancellation()
                            let directory=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
                            try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
                            let file=directory.appendingPathComponent("diagnostic-report."+format)
                            try data.write(to:file,options:.atomic);exportURL=file;return ""
                        }}
                    }
                    if let exportURL { ShareLink(item:exportURL) {Label(t.tr("Share report","Поделиться отчётом","Կիսվել հաշվետվությամբ"),systemImage:"square.and.arrow.up")} }
                }
            } else {Text(t.noSession)}
            if !output.isEmpty {Text(output.replacingOccurrences(of:sid ?? "\u{0}",with:"[internal]")).font(.caption).textSelection(.enabled)}
        }.textFieldStyle(.roundedBorder).buttonStyle(.bordered).disabled(busy)
            .onDisappear {task?.cancel()}
            .onChange(of:sid) {_,_ in task?.cancel();output="";exportURL=nil}
        } label: {Text(heading).font(.headline)}
        .alert(t.tr("Delete shared vehicle?","Удалить общий автомобиль?","Ջնջե՞լ ընդհանուր մեքենան։"),isPresented:Binding(get:{pendingDelete != nil},set:{if !$0 {pendingDelete=nil}})) {
            Button(t.tr("Delete","Удалить","Ջնջել"),role:.destructive) {
                guard let profile=pendingDelete else {return};pendingDelete=nil
                run {
                    _ = try await model.backendOperation("/api/v1/vehicle-profiles/"+profile["id"].text,method:"DELETE")
                    profiles=try await model.backendOperation("/api/v1/vehicle-profiles").items;return ""
                }
            }
            Button(t.tr("Cancel","Отмена","Չեղարկել"),role:.cancel) {pendingDelete=nil}
        }
    }
}
