import SwiftUI
import Charts

struct DisplaySignal {
    let name:String
    let unit:String
    let values:[Double]
    init(name:String,unit:String,values:[Double],us:Bool) {
        self.name=name
        let normalized=unit == "C" ? "°C" : unit
        if us && normalized == "km/h" { self.unit="mph";self.values=values.map {$0/1.609344} }
        else if us && normalized == "°C" { self.unit="°F";self.values=values.map {$0*1.8+32} }
        else { self.unit=normalized;self.values=values }
    }
    var bounds:ClosedRange<Double> {
        switch unit {
        case "rpm":return 0...8000
        case "km/h":return 0...260
        case "mph":return 0...160
        case "°C":return -40...160
        case "°F":return -40...320
        case "%" where name.lowercased().contains("trim") || ["stft","ltft"].contains(name.lowercased()):return -100...100
        case "%":return 0...100
        default:return 0...max(100,(values.max() ?? 0)*1.2)
        }
    }
    var bands:[(Double,Double,Color)] {
        let coolant=["coolant","coolant_temp","coolant_c","coolant temperature"].contains(name.lowercased())
        let boundaries:[Double]
        if coolant {
            boundaries=[60.0,92.0,102.0,110.0].map {unit == "°F" ? $0*1.8+32 : $0}
        } else {
            let span=bounds.upperBound-bounds.lowerBound
            boundaries=[0.25,0.45,0.7,0.85].map {bounds.lowerBound+span * $0}
        }
        let edges=[bounds.lowerBound]+boundaries+[bounds.upperBound]
        let colors:[Color]=[.blue,.cyan,.green,.orange,.red]
        return colors.indices.map {(edges[$0],edges[$0+1],colors[$0])}
    }
}

struct LiveDashboard:View {
    @ObservedObject var model:DiagnosticViewModel
    @AppStorage("hidden_live_channels") private var hidden=""
    private var t:T {T(language:model.settings.language)}
    private var keys:[String] {Array(Set(model.liveRecords.map(\.pid))).sorted()}
    private func isHidden(_ id:String)->Bool { hidden.split(separator:"|").contains(Substring(id)) }
    var body:some View {
        VStack(alignment:.leading,spacing:12) {
            Menu {
                ForEach(keys,id:\.self) { id in
                    Toggle(isOn:Binding(get:{!isHidden(id)},set:{show in
                        var set=Set(hidden.split(separator:"|").map(String.init));if show {set.remove(id)} else {set.insert(id)};hidden=set.sorted().joined(separator:"|")
                    })) {Text(model.liveRecords.last(where:{$0.pid==id})?.display_name ?? id)}
                }
            } label: {Label(t.tr("Visible channels","Видимые каналы","Տեսանելի ալիքներ"),systemImage:"square.grid.2x2")}
            ForEach(keys.filter {!isHidden($0)},id:\.self) { id in
                let rows=model.liveRecords.filter {$0.pid==id}
                let signal=DisplaySignal(name:id,unit:rows.last?.unit ?? "",values:rows.compactMap(\.numeric_value),us:model.settings.usUnits)
                LiveSignalCard(signal:signal,title:t.signalName(id, fallback:rows.last?.display_name ?? id),analog:model.settings.analogDisplay)
                Text(rows.last?.sourceLabel ?? "—").font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

private struct LiveSignalCard:View {
    let signal:DisplaySignal
    let title:String
    let analog:Bool
    @State private var height:Double=240
    @State private var initialHeight:Double?
    var body:some View {
        VStack(alignment:.leading,spacing:10) {
            Text(title).font(.headline)
            Text(signal.values.last.map {String(format:"%.1f %@",$0,signal.unit)} ?? "—").font(.title2.bold())
            if analog {
                Canvas {context,size in
                    let center=CGPoint(x:size.width/2,y:size.height*0.62)
                    let radius=min(size.width*0.38,size.height*0.57)
                    let lower=signal.bounds.lowerBound;let span=signal.bounds.upperBound-lower
                    func angle(_ v:Double)->Double {150+(min(max(v,lower),signal.bounds.upperBound)-lower)/span*240}
                    for (lo,hi,color) in signal.bands {
                        var path=Path();path.addArc(center:center,radius:radius,startAngle:.degrees(angle(lo)),endAngle:.degrees(angle(hi)),clockwise:false)
                        context.stroke(path,with:.color(color),style:StrokeStyle(lineWidth:12,lineCap:.round))
                    }
                    for i in 0...4 {
                        let v=lower+Double(i)/4*span;let a=angle(v)*Double.pi/180
                        let point=CGPoint(x:center.x+cos(a)*(radius+19),y:center.y+sin(a)*(radius+19))
                        context.draw(Text(String(format:"%.0f",v)).font(.caption2).foregroundColor(.secondary),at:point)
                    }
                    if let value=signal.values.last {
                        let a=angle(value)*Double.pi/180
                        var needle=Path();needle.move(to:center);needle.addLine(to:CGPoint(x:center.x+cos(a)*radius*0.8,y:center.y+sin(a)*radius*0.8))
                        context.stroke(needle,with:.color(.primary),style:StrokeStyle(lineWidth:3,lineCap:.round))
                    }
                }.frame(height:max(170,height-80))
            } else {
                Chart(Array(signal.values.enumerated()),id:\.offset) { item in
                    LineMark(x:.value("Sample",item.offset),y:.value("Value",item.element)).foregroundStyle(AutomotivePalette.cyan)
                }.frame(height:max(100,height-80))
            }
            Color.clear.frame(height:14).contentShape(Rectangle()).gesture(DragGesture(minimumDistance:2).onChanged { value in
                if initialHeight==nil {initialHeight=height}
                height=min(500,max(190,(initialHeight ?? height)+value.translation.height))
            }.onEnded {_ in initialHeight=nil;UserDefaults.standard.set(height,forKey:"live-height-"+signal.name)})
                .accessibilityLabel("Resize widget")
        }.padding(16).modifier(AutomotiveCardStyle())
            .onAppear {height=UserDefaults.standard.object(forKey:"live-height-"+signal.name) as? Double ?? 240}
    }
}

extension T {
    func signalName(_ key:String,fallback:String)->String {
        switch key.lowercased() {
        case "rpm","engine_rpm":return tr("Engine speed","Обороты двигателя","Շարժիչի պտույտներ")
        case "coolant_temp","coolant_c","coolant":return tr("Coolant temperature","Температура охлаждения","Հովացուցիչի ջերմաստիճան")
        case "vehicle_speed","speed_kmh","speed":return tr("Vehicle speed","Скорость автомобиля","Մեքենայի արագություն")
        case "throttle","throttle_percent":return tr("Throttle position","Положение дросселя","Դրոսելի դիրք")
        case "map","map_kpa":return tr("MAP pressure","Давление MAP","MAP ճնշում")
        case "maf","maf_gps":return tr("Mass air flow","Массовый расход воздуха","Օդի զանգվածային հոսք")
        case "stft","short_fuel_trim_percent":return tr("Short fuel trim","Краткосрочная коррекция топлива","Վառելիքի կարճաժամկետ շտկում")
        case "ltft","long_fuel_trim_percent":return tr("Long fuel trim","Долгосрочная коррекция топлива","Վառելիքի երկարաժամկետ շտկում")
        case "engine_load_percent","engine_load":return tr("Engine load","Нагрузка двигателя","Շարժիչի բեռնվածություն")
        case "intake_air_c","intake_air_temp":return tr("Intake air temperature","Температура впуска","Ներմուծվող օդի ջերմաստիճան")
        default:return fallback
        }
    }
    func obdMessage(_ text:String)->String {
        switch text {
        case "Not connected":return tr(text,"Не подключено","Միացված չէ")
        case "Bluetooth ready":return tr(text,"Bluetooth готов","Bluetooth-ը պատրաստ է")
        case "Bluetooth unavailable":return tr(text,"Bluetooth недоступен","Bluetooth-ը հասանելի չէ")
        case "Scanning…":return tr(text,"Поиск…","Որոնում…")
        case "Connecting…":return tr(text,"Подключение…","Միացում…")
        case "Connected":return tr(text,"Подключено","Միացված է")
        case "No BLE adapter found":return tr(text,"BLE адаптер не найден","BLE ադապտեր չի գտնվել")
        case "Select BLE adapter":return tr(text,"Выберите BLE адаптер","Ընտրեք BLE ադապտերը")
        case "Unsupported BLE UART profile":return tr(text,"Неподдерживаемый BLE UART профиль","BLE UART պրոֆիլը չի աջակցվում")
        case "BLE adapter timed out":return tr(text,"Истекло время ожидания BLE","BLE սպասման ժամանակը սպառվել է")
        case "BLE adapter disconnected":return tr(text,"BLE адаптер отключён","BLE ադապտերն անջատվել է")
        case "identified":return tr("Vehicle identified","Автомобиль определён","Մեքենան նույնականացված է")
        case "incomplete":return tr("Vehicle identification incomplete","Автомобиль определён частично","Մեքենայի նույնականացումը մասնակի է")
        case "vin_unavailable":return tr("VIN unavailable","VIN недоступен","VIN-ը հասանելի չէ")
        case "lookup_unavailable":return tr("VIN lookup unavailable","Сервис VIN недоступен","VIN-ի որոնումը հասանելի չէ")
        default:return text
        }
    }
}
