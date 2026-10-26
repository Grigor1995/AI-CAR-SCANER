# OBD and Live Data development audit — 2026-10-26

Baseline: `9ff9c1b`. Reviewed the recent result/reanalysis changes and the
OBD path from native transport to backend decoding, acquisition and display.
This is a focused code review plus local regression testing, not a physical
vehicle certification or an assertion that every repository function ran.
No CI/CD was invoked.

## Findings corrected

| Finding | Resulting behavior | Evidence |
| --- | --- | --- |
| Normal Analyze recreated completed rule tests with fresh UUIDs | Exclude completed canonical names using the latest outcome; an INCOMPLETE correction may reopen a test | Reproduced a failing P0171 regression before the fix; API regression now passes |
| Android converted IO failures into successful NO DATA replies | Abort on transport failure; propagate cancellation; still forward genuine NO DATA ECU replies | Native bridge JVM tests distinguish these cases and verify no decode/further commands after disconnect |
| Polling could outlive its selected session | Capture the session and transport for the loop; cancel/restart when the selected session changes | Reviewed Compose lifecycle keys and transport callback |
| Failed local readings remained visible | Clear local snapshots/chart samples after failed polls; stop polling after adapter disconnect | Updated native UI path; stored server history remains separately labelled |
| Backend OBD polling swallowed disconnected-read failures | Forward the failure to AcquisitionManager so its existing reconnect policy runs | Injected disconnect, verified reconnect and recovered 2000 RPM sample |
| Stop awaited an indefinitely blocked read | Cancel the acquisition task and disconnect the source | Blocked-source test verifies bounded Stop and closed source |
| Discovery collected ATDPN but discarded it | Include negotiated protocol in discovery and display it on Desktop/Android | Tests cover automatic 11/29-bit CAN, ISO9141, invalid/unnegotiated responses and simulation |

## Automatic identification contract

- Vehicle identification starts with read-only Mode 09 PID 02 (VIN). VIN lookup
  uses NHTSA online; missing VIN or unavailable lookup leaves identity unknown.
  A catalog model name is never proof of an engine, ECU or protocol.
- Adapter setup defaults to ATSP0. Report the protocol from ATDPN only with a
  complete positive Mode 01 PID 00 ECU response; simulated data is not an
  observed physical protocol. Unknown protocol does not invent a result.
- Android transports are Bluetooth, Wi-Fi and the existing optional USB bridge.
  Desktop has Bluetooth/Wi-Fi/USB transports. An endpoint/address/port must still
  be selected or configured; a model-independent protocol does not discover an
  arbitrary Wi-Fi host. No subnet scanning was added.
- Native applications exchange bytes; formulas, parsing, identification and
  diagnostic reasoning stay in the backend/shared domain implementation.

## Validation

- Backend/domain: **851 passed, 2 skipped**.
- Desktop five-group local matrix: **PASS**; source coverage **90.99%**, core
  coverage **91.84%**. This matrix preceded the small protocol-display addition;
  the focused Desktop discovery test was rerun after that addition.
- Android debug APK, **102 JVM tests**, lint and instrumentation APK compilation:
  **PASS**, checked locally.
- Physical Bluetooth/Wi-Fi/USB adapters, vehicle VIN availability and sampling
  rates were not tested here. Android instrumentation was compiled, not run on
  an emulator. iOS/Xcode validation was not performed.

## Next development priorities

1. Use observed supported-PID bitmaps to build backend polling plans, instead of
   repeatedly querying every standard channel regardless of support.
2. Add native connection-state/retry UX and capture actual adapter transcripts
   for Bluetooth and Wi-Fi; validate Desktop COM/USB baud rates on Windows.
3. Verify VIN lookup failure, key-off, unplug/reconnect and session switching
   with real adapters. Preserve unsupported-PID versus transport-error semantics.
4. Return backend-computed test progress totals; current native progress can
   undercount completed tests after they leave the remaining recommendations.

Generic OBD responders are the discovery scope. ABS, airbags, OEM block names,
CAN FD, OBDonUDS and arbitrary manufacturer functions are not implied by the
presence of an ELM-compatible adapter or a VIN match.
