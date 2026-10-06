# Phase 16 Architecture — Live CAN / ISO-TP / UDS

## Design goals

1. Preserve one diagnostic protocol stack across desktop, Android and future custom Android hardware.
2. Record raw transport evidence before interpretation.
3. Keep ECU identification and DTC decoding separate from LLM reasoning.
4. Support multi-frame ISO-TP responses and flow control.
5. Keep write/programming functions outside the MVP safety boundary.

## Layers

```text
Device Adapter
   -> CAN Bus
      -> ISO-TP
         -> UDS Client
            -> Read-only Diagnostic Session
               -> DiagnosticSession evidence
                  -> Reasoning / RAG / AI
```

`ProtocolTraceRecorder` captures TX/RX CAN frames with session ID, timestamp, arbitration ID, payload, CAN/CAN-FD flags and metadata. This creates a durable debugging and regression artifact without forcing the reasoning engine to parse raw frames directly.

## ECU identification

Default DIDs are:
- `0xF190` VIN
- `0xF187` software version
- `0xF191` hardware version

They are configuration seams, not OEM assumptions. Unsupported DIDs are tolerated so one ECU-specific DID does not prevent the remainder of identity collection.

## DTCs

Read-only service `0x19` is supported through `ReadDTCInformation`. The decoded record retains both the display code and raw/status bytes so later knowledge models can reinterpret the evidence without losing source data.

## Testing

Phase 16 covers:
- UDS positive/negative handling
- UDS DID identity
- ISO-TP multi-frame response
- Flow Control handling
- DTC decoding
- trace capture
- disconnect/reconnect state
- API integration with DiagnosticSession evidence
- physical adapter boundary (HTTP server returns 501 instead of pretending a generic physical transport exists)
