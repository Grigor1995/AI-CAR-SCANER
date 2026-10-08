import SwiftUI

struct DiagnosticScreen: View {
    @ObservedObject var viewModel: DiagnosticViewModel
    @StateObject private var obd = OBDService()
    @State private var tab = 0
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
    @State private var editText=""
    @State private var test:Recommendation?
    @State private var testResult = "INCOMPLETE"
    @State private var testNotes = ""

    private var t:T { T(language:viewModel.settings.language) }

    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:12) {
                    HStack {
                        VStack(alignment:.leading) {
                            Text("AI CAR SCANER").font(.title2.bold())
                            if let id=viewModel.session?.session_id { Text("Session \(id.prefix(8))…").font(.caption).foregroundStyle(.secondary) }
                        }
                        Spacer()
                        Button("⚙"){settingsOpen=true}
                        if viewModel.session != nil { Button("＋"){newSessionOpen=true} }
                    }
                    Picker("",selection:$tab){
                        Text(t.vehicle).tag(0);Text(t.inputs).tag(1);Text(t.analysis).tag(2);Text(t.obd).tag(3);Text(t.activity).tag(4)
                    }.pickerStyle(.segmented)

                    if tab==0 { vehicleView } else if tab==1 { inputsView } else if tab==2 { analysisView } else if tab==3 { obdView } else { activityView }
                }.padding(16)
            }
            .overlay{if viewModel.loading{ProgressView().scaleEffect(1.3)}}
            .alert(t.newSession,isPresented:$newSessionOpen){
                Button(t.cancel,role:.cancel){}
                Button(t.start){viewModel.clearSession();reset()}
            }message:{Text(t.confirm)}
            .sheet(isPresented:$settingsOpen){settingsView}
            .sheet(item:$test){x in TestSheet(test:x,result:$testResult,notes:$testNotes){Task{await viewModel.recordTest(x,testResult,testNotes.isEmpty ? nil:testNotes);test=nil}}}
            .alert(t.editSymptom,isPresented:Binding(get:{editSymptom != nil},set:{if !$0{editSymptom=nil}})){
                TextField(t.symptom, text:$editText)
                Button(t.cancel,role:.cancel){editSymptom=nil}
                Button(t.save){ if let s=editSymptom { Task{ await updateSymptomLocally(s); editSymptom=nil } } }
            }
            .alert("Error",isPresented:Binding(get:{viewModel.error != nil},set:{if !$0{viewModel.error=nil}})){Button("OK"){}}
            .preferredColorScheme(viewModel.settings.darkTheme ? .dark:.light)
        }
    }

    private var vehicleView:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(t.vehicle).font(.title3.bold())
            PickerField(t.make,$make,makes);PickerField(t.model,$model,models);PickerField(t.chassis,$chassis,chassisOptions)
            PickerField(t.year,$year,years);PickerField(t.engine,$engine,engines);PickerField("ECU",$ecu,ecus)
            HStack{Toggle(t.petrol,isOn:$petrol);Toggle(t.lpg,isOn:$lpg)}
            Button(viewModel.session == nil ? t.create:t.save){Task{await saveVehicle()}}
                .buttonStyle(.borderedProminent).frame(maxWidth:.infinity)
        }
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
            ForEach(viewModel.session?.dtcs ?? []){x in InputRow(title:x.code,subtitle:x.description ?? x.source ?? "",edit:{},delete:{Task{await viewModel.deleteDTC(x)}})}
            Button(t.analyze){Task{await viewModel.analyze()}}.buttonStyle(.borderedProminent).frame(maxWidth:.infinity)
        }
    }

    private var analysisView:some View {
        VStack(alignment:.leading,spacing:10) {
            if let s=viewModel.session {
                StatusCard(title:t.state,value:s.state)
                SectionCard("\(t.evidence) (\(s.evidence.count))"){ForEach(s.evidence){x in Text("\(x.fact)\n\(x.status) • \(x.source)").font(.subheadline)}}
                SectionCard("\(t.hypotheses) (\(s.hypotheses.count))"){ForEach(s.hypotheses){x in VStack(alignment:.leading){Text(x.statement).bold();Text("\(x.category) • \(x.status)").font(.caption).foregroundStyle(.secondary)}}}
                SectionCard("\(t.nextTests) (\(s.recommendations.count))"){ForEach(s.recommendations){x in
                    VStack(alignment:.leading,spacing:5){Text(x.name).bold();Text(x.purpose);Text("Information gain: \(x.expected_information_gain,specifier:"%.2f") • Cost: \(x.estimated_cost,specifier:"%.2f")").font(.caption).foregroundStyle(.secondary)
                    Button(t.record){test=x}.buttonStyle(.bordered)}
                }}
            } else {Text(t.noSession)}
        }
    }

    private var obdView:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(t.obd).font(.title3.bold())
            SectionCard("BLE"){Text(obd.status).font(.subheadline);Button(t.scan){obd.scan()}.buttonStyle(.borderedProminent)
                ForEach(obd.devices,id:\.identifier){x in Text(x.name ?? "Unknown adapter")}}
            SectionCard("Wi-Fi OBD"){Text("TCP adapter transport is reserved for the native OBD service.").foregroundStyle(.secondary)}
            Text("USB on iOS requires an Apple-approved accessory path (MFi/ExternalAccessory).").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var activityView:some View {
        VStack(alignment:.leading,spacing:8){Text(t.activity).font(.title3.bold())
            ForEach(viewModel.session?.audit_log ?? []){x in SectionCard(x.event){if let h=x.hypotheses{Text("Hypotheses: \(h)")};if let e=x.evidence_count{Text("Evidence: \(e)")};if let q=x.questions{Text(q.joined(separator:"\n"))}}}
            if (viewModel.session?.audit_log ?? []).isEmpty{Text(t.activityEmpty)}
        }
    }

    private var settingsView:some View {
        NavigationStack{Form{
            Section(t.languageLabel){Picker(t.languageLabel,selection:Binding(get:{viewModel.settings.language},set:{viewModel.settings.language=$0;viewModel.saveSettings()})){ForEach(AppLanguage.allCases){Text($0.label).tag($0)}}}
            Section(t.theme){Toggle(t.dark,isOn:Binding(get:{viewModel.settings.darkTheme},set:{viewModel.settings.darkTheme=$0;viewModel.saveSettings()}))}
            Section("Backend"){TextField("API URL",text:Binding(get:{viewModel.settings.apiURL},set:{viewModel.settings.apiURL=$0;viewModel.saveSettings()})).textInputAutocapitalization(.never).autocorrectionDisabled()}
        }.navigationTitle(t.settings).toolbar{ToolbarItem(placement:.confirmationAction){Button(t.close){settingsOpen=false}}}}
    }

    private var makes:[String]{viewModel.catalog.map(\.make).unique().sorted().ifEmpty(["Mercedes-Benz","Toyota","Kia"])}
    private var models:[String]{viewModel.catalog.filter{$0.make==make}.map(\.model).unique().sorted().ifEmpty(["E-Class"])}
    private var chassisOptions:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model}.compactMap(\.chassis).unique().sorted().ifEmpty(["W211"])}
    private var years:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis}.map{String($0.year)}.unique().sorted().ifEmpty(["2006"])}
    private var engines:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis && String($0.year)==year}.map(\.engine).unique().sorted().ifEmpty(["M272 E35 3.5"])}
    private var ecus:[String]{viewModel.catalog.filter{$0.make==make && $0.model==model && $0.chassis==chassis && $0.engine==engine}.compactMap(\.ecu).unique().sorted().ifEmpty(["ME9.7"])}

    private func saveVehicle()async{let v=Vehicle(make:make,model:model,chassis:chassis,year:Int(year),engine:engine,fuel:[petrol ? "petrol":"",lpg ? "lpg":""].filter{!$0.isEmpty},ecu:ecu);if viewModel.session == nil{await viewModel.newSession(v)}else{await viewModel.updateVehicle(v)}}
    private func updateSymptomLocally(_ s:Symptom)async{await viewModel.updateSymptom(s,editText)}
    private func reset(){make="Mercedes-Benz";model="E-Class";chassis="W211";year="2006";engine="M272 E35 3.5";ecu="ME9.7";petrol=true;lpg=true;symptom="";dtc="";tab=0}
}

private struct PickerField:View{
    let title:String;@Binding var value:String;let options:[String]
    init(_ title:String,_ value:Binding<String>,_ options:[String]){self.title=title;self._value=value;self.options=options}
    var body:some View{Menu{ForEach(options,id:\.self){x in Button(x){value=x}}}label:{HStack{Text(title).foregroundStyle(.secondary);Spacer();Text(value);Image(systemName:"chevron.up.chevron.down").font(.caption)}.padding(12).background(RoundedRectangle(cornerRadius:12).fill(Color.secondary.opacity(0.12)))}}
}
private struct InputRow:View{
    let title:String;var subtitle="";let edit:()->Void;let delete:()->Void
    init(title:String,subtitle:String="",edit:@escaping()->Void,delete:@escaping()->Void={}){self.title=title;self.subtitle=subtitle;self.edit=edit;self.delete=delete}
    var body:some View{HStack{VStack(alignment:.leading){Text(title).bold();if !subtitle.isEmpty{Text(subtitle).font(.caption).foregroundStyle(.secondary)}};Spacer();Button("✎",action:edit);Button(role:.destructive,action:delete){Image(systemName:"trash")}}.padding(12).background(RoundedRectangle(cornerRadius:12).fill(Color.secondary.opacity(0.1)))}
}
private struct SectionCard<C:View>:View{
    let title:String;let content:C
    init(_ title:String,@ViewBuilder _ content:()->C){self.title=title;self.content=content()}
    var body:some View{VStack(alignment:.leading,spacing:8){Text(title).font(.headline);content}.frame(maxWidth:.infinity,alignment:.leading).padding(14).background(RoundedRectangle(cornerRadius:16).fill(Color.secondary.opacity(0.1)))}
}
private struct StatusCard:View{let title:String;let value:String;var body:some View{HStack{Text(title);Spacer();Text(value).bold()}.padding(14).background(RoundedRectangle(cornerRadius:14).fill(Color.secondary.opacity(0.12)))}}
private struct TestSheet:View{
    let test:Recommendation;@Binding var result:String;@Binding var notes:String;let save:()->Void
    var body:some View{NavigationStack{Form{Text(test.name).font(.headline);Picker("Result",selection:$result){Text("PASS").tag("PASS");Text("FAIL").tag("FAIL");Text("INCOMPLETE").tag("INCOMPLETE")};TextField("Diagnostic notes",text:$notes,axis:.vertical).lineLimit(3...7)}.navigationTitle("Test result").toolbar{ToolbarItem(placement:.confirmationAction){Button("Record",action:save)}}}}
}
private struct T{
    let language:AppLanguage
    func tr(_ e:String,_ r:String,_ h:String)->String{language == .en ? e : language == .ru ? r:h}
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
