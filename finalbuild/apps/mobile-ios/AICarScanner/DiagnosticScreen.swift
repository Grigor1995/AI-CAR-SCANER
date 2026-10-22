import SwiftUI
import Charts

struct DiagnosticScreen: View {
    @ObservedObject var viewModel: DiagnosticViewModel
    @StateObject private var obd = OBDService()
    @State private var obdHost = ""
    @State private var obdPort = "35000"
    @State private var tab = 5
    @AppStorage("repairTitle") private var repairTitle = ""
    @AppStorage("repairDraft") private var repairDraft = ""
    @State private var make = "Mercedes-Benz"
    @State private var model = "E-Class"
    @State private var chassis = "W211"
    @State private var year = "2006"
    @State private var engine = "M272 E35 3.5"
    @State private var ecu = "ME9.7"
    @State private var petrol = true
    @State private var lpg = true
    @State private var symptom = ""
    @State private var dtc = ""
    @State private var settingsOpen = false
    @State private var newSessionOpen = false
    @State private var editSymptom:Symptom?
    @State private var editDTC:DTC?
    @State private var editDTCText=""
    @State private var editText=""
    @State private var test:Recommendation?
    @State private var testResult = "INCOMPLETE"
    @State private var testNotes = ""

    private var t:T { T(language:viewModel.settings.language) }

    init(viewModel: DiagnosticViewModel, initialTab: Int = 5) {
        self.viewModel = viewModel
        self._tab = State(initialValue: initialTab)
    }

    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:12) {
                    HStack {
                        Image(systemName:"car.side.fill")
                            .font(.system(size:28,weight:.bold))
                            .foregroundStyle(AutomotivePalette.cyan)
                            .accessibilityHidden(true)
                        VStack(alignment:.leading,spacing:3) {
                            Text("AI CAR SCANNER")
                                .font(.title2.weight(.heavy))
                                .foregroundStyle(viewModel.settings.darkTheme ? .white : AutomotivePalette.navy)
                            Text(t.tr("SMART DIAGNOSTICS • AI ANALYSIS", "УМНАЯ ДИАГНОСТИКА • ИИ-АНАЛИЗ", "ԽԵԼԱՑԻ ԱԽՏՈՐՈՇՈՒՄ • AI ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ"))
                                .font(.system(size:9,weight:.bold))
                                .tracking(1.1)
                                .foregroundStyle(AutomotivePalette.electricBlue)

                        }
                        Spacer()
                        Button("⚙"){settingsOpen=true}
                        if viewModel.session != nil { Button("＋"){newSessionOpen=true} }
                    }
                    ScrollView(.horizontal, showsIndicators:false) {
                        HStack(spacing:8) {
                            ForEach([
                                (5, t.tr("Dashboard", "Обзор", "Գլխավոր"), "house.fill"),
                                (0, t.tr("Vehicles", "Автомобили", "Մեքենաներ"), "car.side.fill"),
                                (3, t.tr("VCI / Devices", "Устройства", "Սարքեր"), "cable.connector"),
                                (1, t.tr("Diagnostic", "Диагностика", "Ախտորոշում"), "stethoscope"),
                                (8, t.tr("Live Data", "Данные", "Ուղիղ տվյալներ"), "chart.xyaxis.line"),
                                (7, t.tr("Tests", "Тесты", "Թեստեր"), "checklist"),
                                (6, "DTC", "exclamationmark.triangle"),
                                (2, t.tr("AI Analysis", "ИИ-анализ", "AI վերլուծություն"), "brain.head.profile"),
                                (9, t.tr("Reports", "Отчёты", "Հաշվետվություններ"), "doc.text"),
                                (10, t.tr("Teach AI", "Обучить ИИ", "Սովորեցնել AI-ին"), "graduationcap"),
                                (4, t.tr("Activity", "История", "Պատմություն"), "clock.arrow.circlepath")
                            ], id: \.0) { item in
                                let index = item.0
                                Button {
                                    tab = index
                                } label: {
                                    Label(item.1, systemImage:item.2)
                                        .font(.subheadline.weight(.semibold))
                                        .lineLimit(1)
                                        .padding(.horizontal,13)
                                        .padding(.vertical,11)
                                        .foregroundStyle(tab == index ? Color.white :
                                            (viewModel.settings.darkTheme ? Color.white.opacity(0.82) :
                                             AutomotivePalette.navy))
                                        .background(
                                            RoundedRectangle(cornerRadius:12)
                                                .fill(tab == index ? AutomotivePalette.electricBlue :
                                                      (viewModel.settings.darkTheme ?
                                                       AutomotivePalette.panel : Color.white))
                                        )
                                        .overlay(
                                            RoundedRectangle(cornerRadius:12)
                                                .strokeBorder(AutomotivePalette.electricBlue.opacity(tab == index ? 0.95 : 0.38))
                                        )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    switch tab {
                    case 0: vehicleView
                    case 1: inputsView
                    case 2: analysisView
                    case 3: obdView
                    case 4: activityView
                    case 5: demoHome
                    case 6: demoDTC
                    case 7: demoTests
                    case 8: demoLive
                    case 9: demoReports
                    default: demoTeach
                    }
                }.padding(16)
            }
            .safeAreaInset(edge: .bottom) {
                HStack {
                    ForEach(Array(zip([5, 0, 8, 7, 9], ["house.fill", "car.side.fill", "chart.xyaxis.line", "checklist", "doc.text"])), id: \.0) { item in
                        Button { tab = item.0 } label: {
                            Image(systemName: item.1).frame(maxWidth: .infinity).padding(.vertical, 14)
                        }.foregroundStyle(tab == item.0 ? AutomotivePalette.cyan : Color.secondary)
                        .accessibilityLabel([5:t.tr("Home", "Обзор", "Գլխավոր"), 0:t.vehicle, 8:t.tr("Live Data", "Текущие данные", "Ուղիղ տվյալներ"), 7:t.nextTests, 9:t.tr("Reports", "Отчёты", "Հաշվետվություններ")][item.0] ?? "")
                    }
                }.background(viewModel.settings.darkTheme ? AutomotivePalette.panel : .white)
            }
            .background(AutomotivePalette.background(dark:viewModel.settings.darkTheme).ignoresSafeArea())
            .tint(AutomotivePalette.electricBlue)
            .overlay{if viewModel.loading{ProgressView().scaleEffect(1.3)}}
            .alert(t.newSession,isPresented:$newSessionOpen){
                Button(t.cancel,role:.cancel){}
                Button(t.start){viewModel.clearSession();reset()}
            }message:{Text(t.confirm)}
            .sheet(isPresented:$settingsOpen){settingsView}
            .sheet(item: $test) { recommendation in
                TestSheet(test: recommendation, language: viewModel.settings.language,
                          loading: viewModel.loading, error: viewModel.error,
                          result: $testResult, notes: $testNotes) {
                    Task {
                        await viewModel.recordTest(recommendation, testResult, testNotes.isEmpty ? nil : testNotes)
                        if viewModel.error == nil {
                            test = nil
                            tab = 2
                        }
                    }
                }
            }
            .alert(t.editSymptom,isPresented:Binding(get:{editSymptom != nil},set:{if !$0{editSymptom=nil}})){
                TextField(t.symptom, text:$editText)
                Button(t.cancel,role:.cancel){editSymptom=nil}
                Button(t.save){ if let s=editSymptom { Task{ await updateSymptomLocally(s); editSymptom=nil } } }
            }
            .alert(t.tr("Error", "Ошибка", "Սխալ"),isPresented:Binding(get:{viewModel.error != nil},set:{if !$0{viewModel.error=nil}})){Button("OK"){}}
            .onChange(of: viewModel.settings.language) { _, _ in
                if let id = viewModel.session?.session_id { Task { await viewModel.openSession(id) } }
            }
            .onChange(of: viewModel.session?.session_id) { _, _ in
                guard let vehicle = viewModel.session?.vehicle else { return }
                make = vehicle.make; model = vehicle.model; chassis = vehicle.chassis ?? ""
                year = vehicle.year.map(String.init) ?? ""; engine = vehicle.engine ?? ""; ecu = vehicle.ecu ?? ""
                petrol = vehicle.fuel.contains { $0.lowercased() == "petrol" }
                lpg = vehicle.fuel.contains { $0.lowercased() == "lpg" }
            }
            .preferredColorScheme(viewModel.settings.darkTheme ? .dark:.light)
        }
    }

    private var demoHome: some View {
        VStack(alignment: .leading, spacing: 16) {
            VehicleModelArtwork(make: viewModel.session?.vehicle?.make ?? make,
                                model: viewModel.session?.vehicle?.model ?? model,
                                chassis: viewModel.session?.vehicle?.chassis ?? chassis, backendURL: viewModel.settings.apiURL, photoAttribution: viewModel.catalog.first { $0.make == (viewModel.session?.vehicle?.make ?? make) && $0.model == (viewModel.session?.vehicle?.model ?? model) && $0.chassis == (viewModel.session?.vehicle?.chassis ?? chassis) }?.image_attribution)
            Text("\(viewModel.session?.vehicle?.make ?? make) \(viewModel.session?.vehicle?.model ?? model)")
                .font(.title2.bold()).frame(maxWidth: .infinity)
            Text(viewModel.session?.vehicle.map { "\($0.chassis ?? "") • \($0.year.map(String.init) ?? "") • \($0.engine ?? "")" } ?? "\(chassis) • \(year) • \(engine)")
                .font(.caption).foregroundStyle(.secondary).frame(maxWidth: .infinity)
            HStack(spacing: 10) {
                demoMetric("DTC", viewModel.session?.dtcs.count ?? 0, "exclamationmark.triangle.fill", .red)
                demoMetric(t.tr("Tests", "Тесты", "Թեստեր"), viewModel.session?.test_results.count ?? 0, "checkmark.shield.fill", .green)
                demoMetric(t.hypotheses, viewModel.session?.hypotheses.count ?? 0, "brain.head.profile", AutomotivePalette.violet)
            }
            Text(t.tr("Quick actions", "Быстрые действия", "Արագ գործողություններ")).font(.headline)
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                demoShortcut("DTC", "exclamationmark.triangle", 6)
                demoShortcut(t.tr("Live Data", "Текущие данные", "Ուղիղ տվյալներ"), "chart.xyaxis.line", 8)
                demoShortcut(t.nextTests, "checklist", 7)
                demoShortcut(t.analysis, "brain.head.profile", 2)
            }
            Button(t.vehicle) { tab = 0 }.buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity)
            if let session = viewModel.session {
                SectionCard(t.tr("Testing progress", "Прогресс тестов", "Փորձարկման ընթացք")) {
                    let latest = session.test_results.reduce(into: [String: String]()) { $0[$1.test_id] = $1.result }
                    let finished = latest.filter { $0.value == "PASS" || $0.value == "FAIL" }
                    let total = Set(session.recommendations.map(\.id)).union(latest.keys)
                    let count = finished.count
                    ProgressView(value: Double(count), total: Double(max(total.count, 1)))
                    Text("\(count)/\(total.count)").font(.caption.monospacedDigit())
                }
            }
        }.padding(16).modifier(AutomotiveCardStyle())
    }

    private func demoMetric(_ title: String, _ value: Int, _ symbol: String, _ color: Color) -> some View {
        VStack(spacing: 9) {
            Image(systemName: symbol).font(.title2).foregroundStyle(color)
            Text(String(value)).font(.title2.bold())
            Text(title).font(.caption2).lineLimit(2)
        }.frame(maxWidth: .infinity, minHeight: 110).modifier(AutomotiveCardStyle(compact: true))
    }

    private func demoShortcut(_ title: String, _ symbol: String, _ destination: Int) -> some View {
        Button { tab = destination } label: {
            Label(title, systemImage: symbol).font(.subheadline.weight(.semibold))
                .frame(maxWidth: .infinity, minHeight: 62)
                .modifier(AutomotiveCardStyle(compact: true))
        }.buttonStyle(.plain)
    }

    private var demoDTC: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("DTC").font(.title2.bold())
            ForEach(viewModel.session?.dtcs ?? []) { code in
                HStack(alignment: .top, spacing: 12) {
                    Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.red)
                    VStack(alignment: .leading, spacing: 6) {
                        Text(code.code).font(.headline).foregroundStyle(.red)
                        Text(code.description ?? code.source ?? "—").font(.subheadline)
                    }
                    Spacer()
                }.padding(16).modifier(AutomotiveCardStyle())
            }
            if (viewModel.session?.dtcs ?? []).isEmpty { Text(t.tr("No recorded DTCs", "Нет записанных DTC", "Գրանցված DTC չկա")) }
            Button(t.inputs) { tab = 1 }.buttonStyle(.borderedProminent)
        }
    }

    private var demoTests: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t.nextTests).font(.title2.bold())
            ForEach(viewModel.session?.recommendations ?? []) { recommendation in
                VStack(alignment: .leading, spacing: 10) {
                    Label(recommendation.name, systemImage: "checklist").font(.headline)
                    Text(recommendation.purpose)
                    ForEach(recommendation.prerequisites, id: \.self) { Text("• " + $0).font(.caption) }
                    ForEach(recommendation.safety_notes, id: \.self) { Text($0).foregroundStyle(.orange).font(.caption) }
                    Button(t.record) { testResult = "INCOMPLETE"; testNotes = ""; test = recommendation }.buttonStyle(.borderedProminent)
                }.padding(16).modifier(AutomotiveCardStyle())
            }
            ForEach(viewModel.session?.test_results ?? []) { result in
                HStack { Text(result.test_name ?? result.test_id); Spacer(); Text(t.testResultLabel(result.result, fallback: result.result_label)).bold().foregroundStyle(AutomotivePalette.resultColor(result.result)) }
                    .padding(14).modifier(AutomotiveCardStyle())
            }
            if (viewModel.session?.recommendations ?? []).isEmpty { Text(t.noSession) }
        }
    }

    private var demoLive: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t.tr("Live Data", "Текущие данные", "Ուղիղ տվյալներ")).font(.title2.bold())
            Text(t.tr("Backend acquisition samples • no generated measurements", "Данные сбора сервера", "Սերվերից ստացված չափումներ")).font(.caption).foregroundStyle(.secondary)
            Button(t.tr("Refresh channels", "Обновить каналы", "Թարմացնել ալիքները")) { Task { await viewModel.refreshLiveData() } }
                .buttonStyle(.borderedProminent).disabled(viewModel.session == nil)
            ForEach(Array(Dictionary(grouping: viewModel.liveRecords, by: \.pid).keys.sorted()), id: \.self) { pid in
                let records = viewModel.liveRecords.filter { $0.pid == pid }
                SectionCard(pid) {
                    if let last = records.last, let value = last.numeric_value {
                        Text("\(value, specifier: "%.2f") \(last.unit ?? "")").font(.title2.bold())
                    }
                    Chart(Array(records.enumerated()), id: \.offset) { item in
                        if let value = item.element.numeric_value {
                            LineMark(x: .value("Sample", item.offset), y: .value("Value", value))
                                .foregroundStyle(AutomotivePalette.cyan)
                        }
                    }.frame(height: 110)
                    Text(records.last?.sourceLabel ?? "—").font(.caption).foregroundStyle(.secondary)
                }
            }
            if viewModel.liveRecords.isEmpty { Text(t.tr("No samples. Start backend acquisition to view channels.", "Нет данных. Запустите сбор на сервере.", "Տվյալներ չկան․ գործարկեք սերվերի չափումների հավաքումը։")) }
        }.task {
            while !Task.isCancelled && viewModel.session != nil {
                await viewModel.refreshLiveData()
                if viewModel.error != nil { return }
                do { try await Task.sleep(nanoseconds: 2_000_000_000) }
                catch { return }
            }
        }
    }

    private var demoReports: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t.tr("Reports / History", "Отчёты / История", "Հաշվետվություններ / Պատմություն")).font(.title2.bold())
            Button(t.tr("Refresh history", "Обновить историю", "Թարմացնել պատմությունը")) { Task { await viewModel.loadHistory() } }
            ForEach(viewModel.history, id: \.session_id) { previous in
                SectionCard("\(previous.vehicle?.make ?? "") \(previous.vehicle?.model ?? "")") {
                    Text("DTC: \(previous.dtcs.count) • \(t.protocolLabel(previous.state))").font(.caption)
                    Button(t.tr("Open session", "Открыть сеанс", "Բացել սեսիան")) { Task { await viewModel.openSession(previous.session_id); tab = 5 } }
                }
            }
            if let session = viewModel.session {
                SectionCard(t.tr("Diagnostic report", "Диагностический отчёт", "Ախտորոշման հաշվետվություն")) {
                    Text("DTC: \(session.dtcs.count) • \(t.nextTests): \(session.test_results.count)")
                    ShareLink(item: session.userReportJSON) {
                        Label(t.tr("Share session report", "Поделиться отчётом", "Կիսվել հաշվետվությամբ"), systemImage: "square.and.arrow.up")
                    }.buttonStyle(.borderedProminent)
                }
                activityView
            } else { Text(t.noSession) }
        }.task { await viewModel.loadHistory() }
    }

    private var demoTeach: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t.tr("Teach AI / Your solution", "Обучить ИИ / Ваше решение", "Սովորեցրու AI-ին / Քո լուծումը")).font(.title2.bold())
            TextField(t.tr("Repair title", "Название ремонта", "Վերանորոգման վերնագիր"), text: $repairTitle).textFieldStyle(.roundedBorder)
            TextEditor(text: $repairDraft).frame(minHeight: 180).padding(8).modifier(AutomotiveCardStyle())
            Text(t.tr("Draft stored on this device. Sharing does not train the AI model.", "Черновик на этом устройстве. Это не обучение модели.", "Սևագիրը պահվում է սարքում․ սա մոդելի ուսուցում չէ։")).font(.caption).foregroundStyle(.secondary)
            ShareLink(item: repairTitle + "\n" + repairDraft) { Label(t.tr("Share repair note", "Поделиться заметкой", "Կիսվել վերանորոգման նշումով"), systemImage: "square.and.arrow.up") }
                .buttonStyle(.borderedProminent).disabled(repairDraft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
    }

    private var catalogFuel: [String] {
        viewModel.catalog.first { $0.make == make && $0.model == model && $0.chassis == chassis && $0.engine == engine }?.fuel ?? []
    }
    private var usesCatalogFuel: Bool { catalogFuel.contains { !["petrol", "lpg"].contains($0.lowercased()) } }

    private var vehicleView:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(t.vehicle).font(.title3.bold())
            VehicleModelArtwork(make: make, model: model, chassis: chassis, backendURL: viewModel.settings.apiURL, photoAttribution: viewModel.catalog.first { $0.make == make && $0.model == model && $0.chassis == chassis }?.image_attribution)
            if viewModel.catalog.isEmpty {
                Text(t.tr(
                    "Offline catalog: options may differ from the server catalog.",
                    "Офлайн-каталог: список может отличаться от серверного каталога.",
                    "Օֆլայն կատալոգ․ ցանկը կարող է տարբերվել սերվերի կատալոգից։"
                ))
                .font(.footnote)
                .foregroundStyle(.orange)
            }
            PickerField(t.make,$make,makes);PickerField(t.model,$model,models);PickerField(t.chassis,$chassis,chassisOptions)
            PickerField(t.year,$year,years);PickerField(t.engine,$engine,engines);PickerField("ECU",$ecu,ecus)
            if usesCatalogFuel {
                Text(catalogFuel.map { code in
                    switch code.lowercased() {
                    case "diesel": return t.tr("Diesel", "Дизель", "Դիզել")
                    case "hybrid": return t.tr("Hybrid", "Гибрид", "Հիբրիդ")
                    default: return code
                    }
                }.joined(separator: " + "))
            } else { HStack{Toggle(t.petrol,isOn:$petrol);Toggle(t.lpg,isOn:$lpg)} }
            if viewModel.catalog.contains(where: { $0.scope == "generation-reference-not-vin-fitment" }) {
                Text(t.tr("Engine options vary by year and market. Confirm VIN and ECU.", "Варианты двигателя зависят от года и рынка. Проверьте VIN и ЭБУ.", "Շարժիչը կախված է տարեթվից ու շուկայից։ Ստուգեք VIN-ը և ECU-ն։")).font(.caption).foregroundStyle(.secondary)
            }
            Button(viewModel.session == nil ? t.create:t.save){Task{await saveVehicle()}}
                .buttonStyle(.borderedProminent).frame(maxWidth:.infinity)
        }
        .onChange(of: make) { _, _ in if !models.contains(model) { model = models.first ?? "" } }
        .onChange(of: model) { _, _ in if !chassisOptions.contains(chassis) { chassis = chassisOptions.first ?? "" } }
        .onChange(of: chassis) { _, _ in if !years.contains(year) { year = years.first ?? "" } }
        .onChange(of: year) { _, _ in if !engines.contains(engine) { engine = engines.first ?? "" } }
        .onChange(of: engine) { _, _ in if !ecus.contains(ecu) { ecu = ecus.first ?? "" } }
    }

    private var inputsView:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(t.symptoms).font(.title3.bold())
            HStack{TextField(t.driverSymptom,text:$symptom,axis:.vertical).textFieldStyle(.roundedBorder)
                Button("＋"){let x=symptom;symptom="";Task{await viewModel.addSymptom(x)}}.disabled(viewModel.session == nil || symptom.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)}
            ForEach(viewModel.session?.symptoms ?? []){x in
                InputRow(title:x.raw_text,edit:{editSymptom=x;editText=x.raw_text},delete:{Task{await viewModel.deleteSymptom(x)}})
            }
            Text("DTC").font(.title3.bold())
            HStack{TextField("P0302",text:$dtc).textFieldStyle(.roundedBorder).textInputAutocapitalization(.characters)
                Button("＋"){let x=dtc;dtc="";Task{await viewModel.addDTC(x)}}.disabled(viewModel.session == nil || dtc.isEmpty)}
            ForEach(viewModel.session?.dtcs ?? []){x in VStack(alignment:.leading,spacing:6){InputRow(title:x.code,subtitle:x.description ?? x.source ?? "",edit:{editDTC=x;editDTCText=x.code},delete:{Task{await viewModel.deleteDTC(x)}});if editDTC?.id == x.id {HStack{TextField("DTC",text:$editDTCText).textInputAutocapitalization(.characters).textFieldStyle(.roundedBorder);Button(t.save){Task{await viewModel.updateDTC(x,editDTCText);editDTC=nil}}.disabled(editDTCText.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty);Button(t.cancel){editDTC=nil}}}}}
            Button(t.analyze){Task{await viewModel.analyze()}}.buttonStyle(.borderedProminent).frame(maxWidth:.infinity)
        }
    }

    private var analysisView:some View {
        VStack(alignment:.leading,spacing:10) {
            if let s=viewModel.session {
                StatusCard(title:t.state,value:t.protocolLabel(s.state))
                AnalysisDiagram(session: s, language: viewModel.settings.language)
                SectionCard("\(t.evidence) (\(s.evidence.count))"){ForEach(s.evidence){x in Text("\(x.fact)\n\(t.protocolLabel(x.status)) • \(t.protocolLabel(x.source))").font(.subheadline)}}
                SectionCard("\(t.hypotheses) (\(s.hypotheses.count))"){ForEach(s.hypotheses){x in VStack(alignment:.leading){Text(x.statement).bold();Text("\(x.category) • \(x.status)").font(.caption).foregroundStyle(.secondary)}}}
                SectionCard("\(t.nextTests) (\(s.recommendations.count))"){ForEach(s.recommendations){x in
                    VStack(alignment:.leading,spacing:5){Text(x.name).bold();Text(x.purpose);Text("\(t.tr("Information gain", "Информационная ценность", "Տեղեկատվական արժեք")): \(x.expected_information_gain,specifier:"%.2f") • \(t.tr("Cost", "Стоимость", "Արժեք")): \(x.estimated_cost,specifier:"%.2f")").font(.caption).foregroundStyle(.secondary)
                    Button(t.record){testResult="INCOMPLETE";testNotes="";test=x}.buttonStyle(.bordered)}
                }}
            } else {Text(t.noSession)}
        }
    }

    private var obdView:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(t.obd).font(.title3.bold())
            SectionCard("BLE"){Text(obd.status).font(.subheadline);Button(t.scan){obd.scan()}.buttonStyle(.borderedProminent)
                ForEach(obd.devices,id:\.identifier){x in Text(x.name ?? t.tr("Unknown adapter", "Неизвестный адаптер", "Անհայտ ադապտեր"))}}
            SectionCard("Wi-Fi OBD") {
                TextField(t.tr("Adapter host", "Адрес адаптера", "Ադապտերի հասցե"), text: $obdHost).textInputAutocapitalization(.never).autocorrectionDisabled()
                TextField(t.tr("Port", "Порт", "Պորտ"), text: $obdPort).keyboardType(.numberPad)
                Button(t.tr("Connect / Read", "Подключить / Считать", "Միացնել / Կարդալ")) {
                    Task { await viewModel.readObdWifi(host: obdHost, port: Int(obdPort) ?? 0) }
                }.buttonStyle(.borderedProminent).disabled(obdHost.isEmpty)
                Button(t.tr("Disconnect", "Отключить", "Անջատել")) { Task { await viewModel.disconnectObdWifi() } }
                ForEach(viewModel.obdValues.keys.sorted(), id: \.self) { key in
                    HStack { Text(key); Spacer(); Text(viewModel.obdValues[key].flatMap { $0 }.map { String(format: "%.1f", $0) } ?? "—") }
                }
            }
            Text(t.tr("USB on iOS requires an Apple-approved accessory path (MFi/ExternalAccessory).", "USB в iOS требует одобренного Apple аксессуара (MFi/ExternalAccessory).", "iOS-ում USB կապը պահանջում է Apple-ի հաստատած պարագա (MFi/ExternalAccessory)։")).font(.caption).foregroundStyle(.secondary)
        }
    }

    private var activityView:some View {
        VStack(alignment:.leading,spacing:8){Text(t.activity).font(.title3.bold())
            ForEach(viewModel.session?.audit_log ?? []){x in SectionCard(x.event){if let h=x.hypotheses{Text("\(t.hypotheses): \(h)")};if let e=x.evidence_count{Text("\(t.evidence): \(e)")};if let q=x.questions{Text(q.joined(separator:"\n"))}}}
            if (viewModel.session?.audit_log ?? []).isEmpty{Text(t.activityEmpty)}
        }
    }

    private var settingsView:some View {
        NavigationStack{Form{
            Section(t.languageLabel){Picker(t.languageLabel,selection:Binding(get:{viewModel.settings.language},set:{viewModel.settings.language=$0;viewModel.saveSettings()})){ForEach(AppLanguage.allCases){Text($0.label).tag($0)}}}
            Section(t.theme){Toggle(t.dark,isOn:Binding(get:{viewModel.settings.darkTheme},set:{viewModel.settings.darkTheme=$0;viewModel.saveSettings()}))}
            Section(t.tr("Server", "Сервер", "Սերվեր")){TextField(t.tr("API URL", "Адрес API", "API հասցե"),text:Binding(get:{viewModel.settings.apiURL},set:{viewModel.settings.apiURL=$0;viewModel.saveSettings()})).textInputAutocapitalization(.never).autocorrectionDisabled()}
        }.navigationTitle(t.settings).toolbar{ToolbarItem(placement:.confirmationAction){Button(t.close){settingsOpen=false}}}}
    }

    private var makes:[String]{viewModel.catalog.map(\.make).unique().sorted()}
    private var models:[String]{viewModel.catalog.filter{$0.make==make}.map(\.model).unique().sorted()}
    private var chassisOptions:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model}.compactMap(\.chassis).unique().sorted()}
    private var years:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis}.map{String($0.year)}.unique().sorted()}
    private var engines:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis && String($0.year)==year}.map(\.engine).unique().sorted()}
    private var ecus:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis && String($0.year)==year && $0.engine==engine}.compactMap(\.ecu).unique().sorted()}

    private func saveVehicle()async{let v=Vehicle(make:make,model:model,chassis:chassis,year:Int(year),engine:engine,fuel:usesCatalogFuel ? catalogFuel : [petrol ? "petrol":"",lpg ? "lpg":""].filter{!$0.isEmpty},ecu:ecu);if viewModel.session == nil{await viewModel.newSession(v)}else{await viewModel.updateVehicle(v)}}
    private func updateSymptomLocally(_ s:Symptom)async{await viewModel.updateSymptom(s,editText)}
    private func reset(){make="Mercedes-Benz";model="E-Class";chassis="W211";year="2006";engine="M272 E35 3.5";ecu="ME9.7";petrol=true;lpg=true;symptom="";dtc="";tab=0}
}

private struct PickerField:View{
    let title:String;@Binding var value:String;let options:[String]
    init(_ title:String,_ value:Binding<String>,_ options:[String]){self.title=title;self._value=value;self.options=options}
    var body:some View{Menu{ForEach(options,id:\.self){x in Button(x){value=x}}}label:{HStack{Text(title).foregroundStyle(.secondary);Spacer();Text(value);Image(systemName:"chevron.up.chevron.down").font(.caption)}.padding(12).modifier(AutomotiveCardStyle(compact:true))}}
}
private struct InputRow:View{
    let title:String;var subtitle="";let edit:()->Void;let delete:()->Void
    init(title:String,subtitle:String="",edit:@escaping()->Void,delete:@escaping()->Void={}){self.title=title;self.subtitle=subtitle;self.edit=edit;self.delete=delete}
    var body:some View{HStack{VStack(alignment:.leading){Text(title).bold();if !subtitle.isEmpty{Text(subtitle).font(.caption).foregroundStyle(.secondary)}};Spacer();Button("✎",action:edit);Button(role:.destructive,action:delete){Image(systemName:"trash")}}.padding(12).modifier(AutomotiveCardStyle(compact:true))}
}
private struct SectionCard<C:View>:View{
    let title:String;let content:C
    init(_ title:String,@ViewBuilder _ content:()->C){self.title=title;self.content=content()}
    var body:some View{VStack(alignment:.leading,spacing:8){Text(title).font(.headline);content}.frame(maxWidth:.infinity,alignment:.leading).padding(14).modifier(AutomotiveCardStyle())}
}
private struct StatusCard:View{let title:String;let value:String;var body:some View{HStack{Text(title);Spacer();Text(value).bold()}.padding(14).modifier(AutomotiveCardStyle())}}
private struct AnalysisDiagram: View {
    let session: DiagnosticSession
    let language: AppLanguage
    @State private var showResults = false
    private var t: T { T(language: language) }
    private var scoredHypotheses: [Hypothesis] {
        session.hypotheses.filter { $0.evidenceScore != nil }
    }
    private var latestResults: [String: TestResult] {
        session.test_results.reduce(into: [:]) { $0[$1.test_id] = $1 }
    }

    var body: some View {
        SectionCard(t.tr("Diagram", "Диаграмма", "Դիագրամ")) {
            Picker(t.tr("Diagram type", "Тип диаграммы", "Դիագրամի տեսակը"), selection: $showResults) {
                Text(t.hypotheses).tag(false)
                Text(t.tr("Results", "Результаты", "Արդյունքներ")).tag(true)
            }.pickerStyle(.segmented)
            if showResults {
                if latestResults.isEmpty {
                    Text(t.tr("No test results yet", "Результатов тестов пока нет", "Թեստերի արդյունքներ դեռ չկան"))
                        .foregroundStyle(.secondary)
                } else {
                    Chart(["PASS", "FAIL", "INCOMPLETE"], id: \.self) { code in
                        let count = latestResults.values.filter { $0.result.uppercased() == code }.count
                        BarMark(x: .value(t.tr("Count", "Количество", "Քանակ"), count),
                                y: .value(t.tr("Result", "Результат", "Արդյունք"), t.testResultLabel(code)))
                            .foregroundStyle(AutomotivePalette.resultColor(code))
                            .cornerRadius(5)
                            .annotation(position: .trailing) { Text(String(count)).font(.caption.bold()) }
                            .accessibilityLabel(t.testResultLabel(code))
                            .accessibilityValue(String(count))
                    }.chartXScale(domain: 0...max(1, latestResults.count))
                        .chartXAxis { AxisMarks(values: .stride(by: 1)) }
                        .frame(height: 170)
                }
            } else {
                if scoredHypotheses.isEmpty {
                    Text(t.tr("Analyze the session to get scored hypotheses.", "Выполните анализ для получения оценок гипотез.", "Վարկածների գնահատականները ստանալու համար վերլուծեք սեսիան։"))
                        .foregroundStyle(.secondary)
                } else {
                    Chart(Array(scoredHypotheses.enumerated()), id: \.element.id) { item in
                        if let score = item.element.evidenceScore {
                            BarMark(x: .value(t.tr("Evidence score", "Оценка обоснованности", "Հիմնավորվածության գնահատական"), score * 100),
                                    y: .value(t.hypotheses, String(item.offset + 1)))
                                .foregroundStyle(AutomotivePalette.cyan)
                                .cornerRadius(5)
                                .annotation(position: .trailing) { Text("\(Int((score * 100).rounded()))%").font(.caption.bold()) }
                                .accessibilityLabel(item.element.statement)
                                .accessibilityValue("\(Int((score * 100).rounded()))%")
                        }
                    }.chartXScale(domain: 0...100)
                        .frame(height: CGFloat(max(160, scoredHypotheses.count * 44)))
                    ForEach(Array(scoredHypotheses.enumerated()), id: \.element.id) { item in
                        Text("\(item.offset + 1). \(item.element.statement)").font(.caption)
                    }
                    Text(t.tr("Scores show supporting evidence, not confirmed failures.", "Оценки отражают обоснованность гипотез, а не подтверждённые неисправности.", "Գնահատականները ցույց են տալիս վարկածների հիմնավորվածությունը, ոչ թե հաստատված անսարքությունները։"))
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
        }
    }
}

private struct TestSheet: View {
    let test: Recommendation
    let language: AppLanguage
    let loading: Bool
    let error: String?
    private var t: T { T(language: language) }
    @Binding var result: String
    @Binding var notes: String
    let save: () -> Void

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text(test.name).font(.title2.bold())
                    Text(test.purpose)
                    if loading {
                        ProgressView(t.tr("Updating diagnosis…", "Обновление диагноза…", "Ախտորոշումը թարմացվում է…"))
                    }
                    if let error { Text(error).foregroundStyle(.red) }
                    ForEach(test.safety_notes, id: \.self) { Text($0).foregroundStyle(.orange) }
                    VStack(spacing: 10) {
                        ForEach(["PASS", "FAIL", "INCOMPLETE"], id: \.self) { code in
                            Button { result = code } label: {
                                HStack(spacing: 12) {
                                    Image(systemName: code == "PASS" ? "checkmark.shield.fill" : code == "FAIL" ? "exclamationmark.triangle.fill" : "shield.lefthalf.filled").font(.title)
                                    Text(t.testResultLabel(code)).font(.body.bold()).fixedSize(horizontal: false, vertical: true)
                                }.padding(.horizontal, 16).frame(maxWidth: .infinity, minHeight: 64)
                                    .foregroundStyle(AutomotivePalette.resultColor(code))
                                    .background(AutomotivePalette.resultColor(code).opacity(result == code ? 0.18 : 0.04))
                                    .clipShape(RoundedRectangle(cornerRadius: 14))
                                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(AutomotivePalette.resultColor(code).opacity(result == code ? 1 : 0.3)))
                            }.buttonStyle(.plain).disabled(loading).accessibilityAddTraits(result == code ? .isSelected : [])
                        }
                    }
                    TextField(t.tr("Diagnostic notes / measurements", "Заметки / измерения", "Ախտորոշման նշումներ / չափումներ"), text: $notes, axis: .vertical)
                        .lineLimit(4...9).padding(14).modifier(AutomotiveCardStyle()).disabled(loading)
                    Button(t.record, action: save).buttonStyle(.borderedProminent).frame(maxWidth: .infinity).disabled(loading)
                }.padding(16)
            }.navigationTitle(t.tr("Test result", "Результат теста", "Թեստի արդյունք"))
                .interactiveDismissDisabled(loading)
        }
    }
}

struct T{
    let language:AppLanguage
    func tr(_ e:String,_ r:String,_ h:String)->String{language == .en ? e : language == .ru ? r:h}
    func testResultLabel(_ code: String, fallback: String? = nil) -> String {
        switch code.uppercased() {
        case "PASS": return tr("PASS", "Норма", "Նորմալ")
        case "FAIL": return tr("FAIL", "Есть проблема", "Խնդիր կա")
        case "INCOMPLETE": return tr("INCOMPLETE", "Не завершён", "Անավարտ")
        default: return fallback ?? code
        }
    }
    func protocolLabel(_ value: String) -> String {
        switch value {
        case "CREATED": return tr("Created", "Создан", "Ստեղծված է")
        case "VEHICLE_IDENTIFIED": return tr("VEHICLE_IDENTIFIED", "АВТОМОБИЛЬ ИДЕНТИФИЦИРОВАН", "ՄԵՔԵՆԱՆ ՆՈՒՅՆԱԿԱՆԱՑՎԱԾ Է")
        case "SYMPTOMS_COLLECTED": return tr("SYMPTOMS_COLLECTED", "СИМПТОМЫ СОБРАНЫ", "ԱԽՏԱՆՇԱՆՆԵՐԸ ՀԱՎԱՔՎԱԾ ԵՆ")
        case "INITIAL_ANALYSIS": return tr("INITIAL_ANALYSIS", "ПЕРВИЧНЫЙ АНАЛИЗ", "ՍԿԶԲՆԱԿԱՆ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ")
        case "QUESTIONS_PENDING": return tr("QUESTIONS_PENDING", "ОЖИДАЮТСЯ УТОЧНЕНИЯ", "ՍՊԱՍՎՈՒՄ ԵՆ ՃՇՏՈՒՄՆԵՐ")
        case "DATA_COLLECTION": return tr("DATA_COLLECTION", "СБОР ДАННЫХ", "ՏՎՅԱԼՆԵՐԻ ՀԱՎԱՔԱԳՐՈՒՄ")
        case "TESTING": return tr("TESTING", "ТЕСТИРОВАНИЕ", "ԹԵՍՏԱՎՈՐՈՒՄ")
        case "HYPOTHESIS_VALIDATION": return tr("HYPOTHESIS_VALIDATION", "ПРОВЕРКА ГИПОТЕЗ", "ՎԱՐԿԱԾՆԵՐԻ ՍՏՈՒԳՈՒՄ")
        case "ROOT_CAUSE_FOUND": return tr("ROOT_CAUSE_FOUND", "ПРИЧИНА НАЙДЕНА", "ՊԱՏՃԱՌԸ ԳՏՆՎԱԾ Է")
        case "REPAIR": return tr("REPAIR", "РЕМОНТ", "ՎԵՐԱՆՈՐՈԳՈՒՄ")
        case "POST_REPAIR_VERIFICATION": return tr("POST_REPAIR_VERIFICATION", "ПРОВЕРКА ПОСЛЕ РЕМОНТА", "ՎԵՐԱՆՈՐՈԳՈՒՄԻՑ ՀԵՏՈ ՍՏՈՒԳՈՒՄ")
        case "CLOSED": return tr("CLOSED", "ЗАКРЫТО", "ՓԱԿՎԱԾ Է")
        case "USER_REPORTED": return tr("USER_REPORTED", "Сообщено пользователем", "Օգտատիրոջ հաղորդած")
        case "TECHNICIAN_OBSERVED": return tr("TECHNICIAN_OBSERVED", "Наблюдение механика", "Տեխնիկի դիտարկում")
        case "VEHICLE_MEASURED": return tr("VEHICLE_MEASURED", "Измерено автомобилем", "Մեքենայի չափում")
        case "ECU_REPORTED": return tr("ECU_REPORTED", "Сообщено ЭБУ", "ECU-ի հաղորդած")
        case "DATABASE": return tr("DATABASE", "База данных", "Տվյալների բազա")
        case "OEM_DOCUMENT": return tr("OEM_DOCUMENT", "Документ производителя", "Արտադրողի փաստաթուղթ")
        case "RULE": return tr("RULE", "Анализ по правилам", "Կանոնային վերլուծություն")
        case "ML_MODEL": return tr("ML_MODEL", "Модель машинного обучения", "Մեքենայական ուսուցման մոդել")
        case "LLM_INFERENCE": return tr("LLM_INFERENCE", "Вывод языковой модели", "Լեզվային մոդելի եզրակացություն")
        case "HISTORICAL_CASE": return tr("HISTORICAL_CASE", "Предыдущий случай", "Նախորդ դեպք")
        case "reported": return tr("reported", "сообщено", "հաղորդված")
        case "measured": return tr("measured", "измерено", "չափված")
        case "calculated": return tr("calculated", "рассчитано", "հաշվարկված")
        case "inferred": return tr("inferred", "предположено", "ենթադրված")
        case "confirmed": return tr("confirmed", "подтверждено", "հաստատված")
        case "rejected": return tr("rejected", "отклонено", "մերժված")
        default: return value
        }
    }
    var vehicle:String{tr("Vehicle","Автомобиль","Մեքենա")};var inputs:String{tr("Inputs","Ввод","Մուտքեր")};var analysis:String{tr("Analysis","Анализ","Վերլուծություն")};var obd:String{"OBD"};var activity:String{tr("Activity","Журнал","Գործունեություն")}
    var make:String{tr("Make","Марка","Մակնիշ")};var model:String{tr("Model","Модель","Մոդել")};var chassis:String{tr("Chassis","Кузов","Թափք")};var year:String{tr("Year","Год","Տարի")};var engine:String{tr("Engine","Двигатель","Շարժիչ")};var petrol:String{tr("Petrol","Бензин","Բենզին")};var lpg:String{tr("LPG","Газ","Գազ")}
    var create:String{tr("Create diagnostic session","Создать диагностическую сессию","Ստեղծել դիագնոստիկ սեսիա")};var save:String{tr("Save","Сохранить","Պահպանել")};var symptoms:String{tr("Symptoms","Симптомы","Ախտանիշներ")};var symptom:String{tr("Symptom","Симптом","Ախտանիշ")};var driverSymptom:String{tr("Driver symptom","Симптом водителя","Վարորդի ախտանիշը")};var analyze:String{tr("Analyze session","Анализировать","Վերլուծել սեսիան")}
    var evidence:String{tr("Evidence","Доказательства","Ապացույցներ")};var hypotheses:String{tr("Hypotheses","Гипотезы","Հիպոթեզներ")};var nextTests:String{tr("Next diagnostic tests","Следующие тесты","Հաջորդ թեստերը")};var record:String{tr("Record result","Записать результат","Գրանցել արդյունքը")};var state:String{tr("State","Состояние","Կարգավիճակ")};var noSession:String{tr("Create a session first.","Сначала создайте сессию.","Սկզբում ստեղծեք սեսիա։")};var activityEmpty:String{tr("No activity yet.","Журнал пуст.","Գործունեություն չկա։")}
    var settings:String{tr("Settings","Настройки","Կարգավորումներ")};var languageLabel:String{tr("Language","Язык","Լեզու")};var theme:String{tr("Theme","Тема","Թեմա")};var dark:String{tr("Dark","Тёмная","Մուգ")};var close:String{tr("Close","Закрыть","Փակել")};var newSession:String{tr("New session","Новая сессия","Նոր սեսիա")};var start:String{tr("Start","Начать","Սկսել")};var cancel:String{tr("Cancel","Отмена","Չեղարկել")};var confirm:String{tr("Current session data will be cleared from this screen.","Данные текущей сессии будут очищены с экрана.","Ընթացիկ սեսիայի տվյալները կմաքրվեն էկրանից։")};var scan:String{tr("Scan BLE adapters","Сканировать BLE","Սկանավորել BLE")};var editSymptom:String{tr("Edit symptom","Изменить симптом","Խմբագրել ախտանիշը")}
}
private extension Array where Element:Hashable{
    func unique()->[Element]{Array(Set(self))}
    func ifEmpty(_ x:[Element])->[Element]{isEmpty ? x:self}
}
