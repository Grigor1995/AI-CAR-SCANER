class ObdDeviceCapabilities {
  final bool obd, can, canFd, uds, ble, wifi, usb;
  const ObdDeviceCapabilities({this.obd=false,this.can=false,this.canFd=false,this.uds=false,this.ble=false,this.wifi=false,this.usb=false});
}

abstract interface class DiagnosticAdapter {
  Future<void> connect();
  Future<void> disconnect();
  Future<String?> readVin();
  Future<List<String>> readDtcs();
  Future<Map<String, double?>> readStandardLiveData();
  ObdDeviceCapabilities get capabilities;
}
