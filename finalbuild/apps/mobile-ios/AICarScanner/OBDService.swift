import Foundation
import CoreBluetooth

final class OBDService: NSObject, ObservableObject, CBCentralManagerDelegate {
    @Published var status = "Not connected"
    @Published var devices: [CBPeripheral] = []

    private var central: CBCentralManager!

    override init() {
        super.init()
        central = CBCentralManager(delegate: self, queue: .main)
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        status = central.state == .poweredOn
            ? "Bluetooth ready"
            : "Bluetooth unavailable"
    }

    func scan() {
        guard central.state == .poweredOn else { return }

        devices = []
        status = "Scanning…"
        central.scanForPeripherals(withServices: nil)

        Task {
            try? await Task.sleep(for: .seconds(5))
            central.stopScan()
            status = devices.isEmpty
                ? "No BLE adapter found"
                : "\(devices.count) adapter(s) found"
        }
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        if !devices.contains(where: { $0.identifier == peripheral.identifier }) {
            devices.append(peripheral)
        }
    }
}
