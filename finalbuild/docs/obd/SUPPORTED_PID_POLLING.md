# Capability-based live polling

The backend selects live commands from observed Mode 01 PID 00 bitmaps. Vehicle
make/model hints never enable a PID. This covers the ten currently implemented
Mode 01 channels, all within PID page 01–20 hexadecimal; it does not implement
all possible standard/OEM PIDs or claim physical adapter verification.

## Native bridge flow

1. `GET /api/v1/obd/plan` supplies adapter initialization and the capability
   discovery commands (`0100`, `ATDPN`). Initialize the adapter once.
2. Send discovery commands through the selected native transport. Forward the
   raw responses to `POST /api/v1/obd/plan`:

```json
{"responses":{"0100":"41 00 00 10 00 00","ATDPN":"A6"}}
```

The example advertises RPM only. The backend returns:

```json
{
  "schema_version": 2,
  "initialization": [],
  "discovery": [],
  "commands": ["010C"],
  "supported_pids": [12],
  "capabilities_observed": true,
  "read_only": true
}
```

The response also includes `unsupported_commands` and transport framing metadata.

3. Poll only the returned `commands`. Include the cached discovery responses
   alongside live responses when calling `POST /api/v1/obd/decode`, preserving
   the observed protocol metadata. The backend performs all numeric scaling.
4. Reuse the selected commands for that active connection/polling session. Reopen
   discovery after disconnect, reconnect, failed negotiation or a native session
   change. A failed transport read must not become a successful NO DATA frame.

Android's `LivePollingSession` holds connection-local planning state. The iOS
Wi-Fi actor holds the plan with its connection and invalidates it on session
changes. Native clients do not inspect bit positions or select sensor commands.

## Server-local/Desktop adapters

`GenericObdClient` reuses the initial `0100` reply after adapter initialization,
then calls the same backend plan function. Successful capabilities are cached
until reconnect. An invalid initial capability may be retried when the ECU wakes
up. `ObdPollingSource` intersects its requested channels with the observed plan;
no remaining channels causes a clear error and closes the source connection.

The simulator explicitly advertises its four synthetic channels. It is not
used as a fallback for a missing real ECU bitmap.

## Validation and compatibility

- Complete 32-bit positive `41 00` responses are required. Complete responses
  from multiple 11/29-bit CAN responders are combined using a bitmap union.
- Missing, truncated, wrong-service or malformed capability input returns HTTP
  422. There is no fallback to polling every known sensor.
- An all-zero bitmap is a valid observed response with an empty command list;
  native/server-local callers report that no implemented live channel is
  available rather than inventing readings.
- Current live channels need only the first supported-PID page. The continuation
  bit does not cause unnecessary page scans. Expanding the decoder catalog above
  PID 20 hexadecimal will require extending capability discovery accordingly.
- The legacy GET `commands` list remains for old API consumers. Current native
  bridges use `discovery` plus the new POST negotiation, and server-local polling
  uses the shared selector. Update backend and native apps together; an older
  backend without POST negotiation cannot provide the new behavior.

Tests cover bitmap boundaries, multiple ECUs, invalid/no support, cached polling,
reconnect, cancellation, adapter wake-up and raw native request contracts. Swift
syntax parsing is separate from iOS compilation; Xcode and actual vehicle tests
remain required for native hardware validation. No CI/CD is used for this change.
