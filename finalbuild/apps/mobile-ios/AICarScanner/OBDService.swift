import Foundation
import CoreBluetooth
import Combine

/// BLE byte transport for known UART profiles. All OBD commands/decoding come from Backend.
@MainActor
final class OBDService: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    @Published var status = "Not connected"
    @Published var devices: [CBPeripheral] = []
    @Published var connected = false
    private var central:CBCentralManager!
    private var peripheral:CBPeripheral?
    private var writer:CBCharacteristic?
    private var reader:CBCharacteristic?
    private var connectionWait:CheckedContinuation<Void,Error>?
    private var responseWait:CheckedContinuation<String,Error>?
    private var deadline:Task<Void,Never>?
    private var buffer=Data()
    private var initialized=false
    private var sessionID:String?
    private var liveCommands:[String]?
    private var capabilities:[String:String]=[:]
    private var busy=false
    // service : (write, notify), not inferred from a peripheral name.
    private let profiles:[String:(String,String)] = [
        "FFE0":("FFE1","FFE1"), "FFF0":("FFF2","FFF1"),
        "6E400001-B5A3-F393-E0A9-E50E24DCCA9E":("6E400002-B5A3-F393-E0A9-E50E24DCCA9E","6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    ]
    enum TransportError:LocalizedError {
        case unavailable, unsupported, timeout, disconnected, concurrent, oversized
        var errorDescription:String? {
            switch self {
            case .unavailable:return "Bluetooth unavailable"
            case .unsupported:return "Unsupported BLE UART profile"
            case .timeout:return "BLE adapter timed out"
            case .disconnected:return "BLE adapter disconnected"
            case .concurrent:return "An OBD read is already running"
            case .oversized:return "OBD response exceeded the transport limit"
            }
        }
    }
    override init() {super.init();central=CBCentralManager(delegate:self,queue:.main)}
    func centralManagerDidUpdateState(_ central:CBCentralManager) {
        status=central.state == .poweredOn ? "Bluetooth ready" : "Bluetooth unavailable"
        if central.state != .poweredOn {fail(TransportError.unavailable)}
    }
    func scan() {
        guard central.state == .poweredOn else {return}
        devices=[];status="Scanning…";central.scanForPeripherals(withServices:nil)
        Task {try? await Task.sleep(nanoseconds:5_000_000_000);central.stopScan();if !connected {status=devices.isEmpty ? "No BLE adapter found" : "Select BLE adapter"}}
    }
    func centralManager(_ central:CBCentralManager,didDiscover peripheral:CBPeripheral,advertisementData:[String:Any],rssi RSSI:NSNumber) {
        if !devices.contains(where:{$0.identifier==peripheral.identifier}) {devices.append(peripheral)}
    }
    func connect(_ target:CBPeripheral) async throws {
        if connected && peripheral === target {return}
        guard connectionWait==nil else {throw TransportError.concurrent}
        guard target.state != .disconnecting else {throw TransportError.disconnected}
        disconnect();central.stopScan()
        guard central.state == .poweredOn else {throw TransportError.unavailable}
        peripheral=target;target.delegate=self;status="Connecting…"
        try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { (wait:CheckedContinuation<Void,Error>) in
                connectionWait=wait;armTimeout(seconds:15);central.connect(target)
            }
        } onCancel:{Task { @MainActor in self.disconnect() }}
    }
    func centralManager(_ central:CBCentralManager,didConnect peripheral:CBPeripheral) {
        guard self.peripheral===peripheral else {return}
        peripheral.discoverServices(profiles.keys.map {CBUUID(string:$0)})
    }
    func centralManager(_ central:CBCentralManager,didFailToConnect peripheral:CBPeripheral,error:Error?) {if self.peripheral===peripheral {fail(error ?? TransportError.disconnected)}}
    func centralManager(_ central:CBCentralManager,didDisconnectPeripheral peripheral:CBPeripheral,error:Error?) {if self.peripheral===peripheral {fail(error ?? TransportError.disconnected)}}
    func peripheral(_ peripheral:CBPeripheral,didDiscoverServices error:Error?) {
        guard self.peripheral===peripheral else {return}
        if let error {fail(error);return}
        guard let service=peripheral.services?.first(where:{profiles[$0.uuid.uuidString] != nil}) else {fail(TransportError.unsupported);return}
        peripheral.discoverCharacteristics(nil,for:service)
    }
    func peripheral(_ peripheral:CBPeripheral,didDiscoverCharacteristicsFor service:CBService,error:Error?) {
        guard self.peripheral===peripheral else {return}
        if let error {fail(error);return}
        guard let profile=profiles[service.uuid.uuidString],
              let write=service.characteristics?.first(where:{$0.uuid==CBUUID(string:profile.0) && (!$0.properties.intersection([.write,.writeWithoutResponse]).isEmpty)}),
              let read=service.characteristics?.first(where:{$0.uuid==CBUUID(string:profile.1) && (!$0.properties.intersection([.notify,.indicate]).isEmpty)}) else {fail(TransportError.unsupported);return}
        writer=write;reader=read;peripheral.setNotifyValue(true,for:read)
    }
    func peripheral(_ peripheral:CBPeripheral,didUpdateNotificationStateFor characteristic:CBCharacteristic,error:Error?) {
        guard self.peripheral===peripheral,characteristic===reader else {return}
        if let error {fail(error);return}
        guard characteristic.isNotifying else {fail(TransportError.unsupported);return}
        deadline?.cancel();connected=true;status="Connected";let wait=connectionWait;connectionWait=nil;wait?.resume()
    }
    func peripheral(_ peripheral:CBPeripheral,didWriteValueFor characteristic:CBCharacteristic,error:Error?) {
        if self.peripheral===peripheral,let error {fail(error)}
    }
    func peripheral(_ peripheral:CBPeripheral,didUpdateValueFor characteristic:CBCharacteristic,error:Error?) {
        guard self.peripheral===peripheral,characteristic===reader,responseWait != nil else {return}
        if let error {fail(error);return}
        if let value=characteristic.value {buffer.append(value)}
        if buffer.count>16384 {fail(TransportError.oversized);return}
        if let end=buffer.firstIndex(of:62) {
            deadline?.cancel();let value=String(decoding:buffer[..<end],as:UTF8.self)
            let wait=responseWait;responseWait=nil;buffer=Data();wait?.resume(returning:value)
        }
    }
    private func armTimeout(seconds:UInt64) {
        deadline?.cancel();deadline=Task {do {try await Task.sleep(nanoseconds:seconds*1_000_000_000)} catch {return};fail(TransportError.timeout)}
    }
    private func fail(_ error:Error) {
        deadline?.cancel();let old=peripheral;peripheral=nil;writer=nil;reader=nil;connected=false;initialized=false;liveCommands=nil;capabilities=[:]
        if let old {central.cancelPeripheralConnection(old)}
        let connect=connectionWait;connectionWait=nil;let response=responseWait;responseWait=nil
        connect?.resume(throwing:error);response?.resume(throwing:error);status=error.localizedDescription
    }
    func disconnect() {central?.stopScan();fail(TransportError.disconnected);status="Not connected"}
    private func command(_ command:String) async throws -> String {
        guard let peripheral,let writer,connected else {throw TransportError.disconnected}
        guard responseWait==nil else {throw TransportError.concurrent}
        let data=Data((command+"\r").utf8)
        let type:CBCharacteristicWriteType=writer.properties.contains(.write) ? .withResponse : .withoutResponse
        guard data.count<=peripheral.maximumWriteValueLength(for:type) else {throw TransportError.oversized}
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { (wait:CheckedContinuation<String,Error>) in
                buffer=Data();responseWait=wait;armTimeout(seconds:35)
                peripheral.writeValue(data,for:writer,type:type)
            }
        } onCancel:{Task { @MainActor in self.disconnect() }}
    }
    func read(api:DiagnosticAPI,session:String?) async throws -> ObdDecodedSnapshot {
        guard !busy else {throw TransportError.concurrent};busy=true;defer {busy=false}
        do {
            if sessionID != session {sessionID=session;liveCommands=nil;capabilities=[:]}
            if liveCommands==nil {
                let plan=try await api.obdPlan()
                if !initialized {for step in plan.initialization {_ = try await command(step)};initialized=true}
                guard let steps=plan.discovery,!steps.isEmpty else {throw TransportError.unsupported}
                for step in steps {capabilities[step]=try await command(step)}
                let supported=try await api.supportedObdPlan(capabilities)
                guard !supported.commands.isEmpty else {throw TransportError.unsupported};liveCommands=supported.commands
            }
            var responses=capabilities
            for step in liveCommands ?? [] {responses[step]=try await command(step)}
            return try await api.decodeObd(responses,sessionID:session)
        } catch {fail(error);throw error}
    }
    func identify(api:DiagnosticAPI) async throws -> DiscoveryResult {
        guard !busy else {throw TransportError.concurrent};busy=true
        defer {busy=false;initialized=false;liveCommands=nil;capabilities=[:]}
        let boot=try await api.obdPlan();for step in boot.initialization {_ = try await command(step)}
        let plan=try await api.discoveryPlan();var responses:[String:String]=[:]
        do {for step in plan.commands {responses[step]=try await command(step)}}
        catch {for step in plan.restore {_ = try? await command(step)};throw error}
        for step in plan.restore {_ = try await command(step)}
        return try await api.decodeDiscovery(responses)
    }
}
