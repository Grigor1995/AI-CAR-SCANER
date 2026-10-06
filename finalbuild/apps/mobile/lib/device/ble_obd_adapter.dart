import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import '../obd/obd_device.dart';

/// BLE lifecycle adapter. UUIDs are supplied by the device profile; no vendor is hard-coded.
class BleObdAdapter implements DiagnosticAdapter {
  final BluetoothDevice device;
  final Guid txUuid;
  final Guid rxUuid;
  BleObdAdapter(this.device, {required this.txUuid, required this.rxUuid});
  @override
  ObdDeviceCapabilities get capabilities => const ObdDeviceCapabilities(obd: true, ble: true);
  @override
  Future<void> connect() => device.connect();
  @override
  Future<void> disconnect() => device.disconnect();
  @override
  Future<String?> readVin() async => null; // protocol bridge is completed with device profile.
  @override
  Future<List<String>> readDtcs() async => const [];
  @override
  Future<Map<String, double?>> readStandardLiveData() async => const {};
}
