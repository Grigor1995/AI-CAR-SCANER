# Phase 4 — Professional VCI

## Decision
Introduce a vendor-neutral device registry and adapter layer, plus a J2534 Pass-Thru seam. Vendor SDKs/DLLs remain optional plugins and are never embedded in the diagnostic domain.

## Why
Professional VCI hardware varies by transport, protocol and SDK. The application needs capability discovery and lifecycle management without coupling sessions to a manufacturer.

## Alternatives
- Direct vendor SDK in the diagnostic engine: rejected; creates lock-in.
- One universal hardware library: rejected; capability and licensing coverage varies.
- Microservice per vendor: rejected for MVP; unnecessary operational complexity.

## Added
- DeviceDescriptor / DeviceCapabilities / DeviceStatus
- DeviceRegistry
- DiagnosticAdapter lifecycle interface
- Generic VendorSdkAdapter
- J2534 Pass-Thru abstraction
- Windows J2534 DLL loader seam
- VCI simulator with professional capabilities
- Registry/J2534 lifecycle tests

## Safety
No ECU programming, flashing, security access or write operations are implemented. J2534 DLL calls are intentionally a configured integration seam.

## Next
Phase 5: custom Android diagnostic device, native device services, SDK packaging, offline synchronization, OTA architecture and hardware-in-the-loop lab.
