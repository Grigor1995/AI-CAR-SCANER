# Editable main menu

Main-menu tiles can be reordered while keeping the same workflow destinations.
No move buttons, resize sliders or edit-mode switch are added.

- Desktop: drag a tile onto the position you want. Small pointer movement stays
  a normal click; a completed drag does not also open the workflow. Keyboard
  users can focus a tile and use Ctrl+Left/Right to move it one position.
- Android: hold a tile and drag it onto another tile. Keep the pointer near the
  top/bottom of the screen to scroll while dragging. The destination receives a
  highlighted border. Release outside a tile to cancel the move.
- iOS: hold and drag a tile onto another tile using the native drag-and-drop
  interaction. VoiceOver and Android accessibility expose Move earlier/later
  actions without adding visible buttons.

For example, moving Diagnostics onto the first Symptoms tile results in
Diagnostics first and Symptoms second. A subsequent tap still opens Diagnostics.
Reordering changes the launcher only; sidebar/toolbars and diagnostic logic are
not reordered.

Preferences are local to each platform/device and are independent of the active
vehicle/session, theme and language. Desktop uses QSettings `launcher_order`,
Android uses the dedicated `ai_car_launcher_layout` preference file, and iOS
uses AppStorage `launcher_order`. They are not synchronized through the backend.
Unknown/duplicate stored IDs are discarded and newly added sections are appended,
so an older preference cannot remove a workflow introduced by an app update.

Validation includes Desktop click/drag/keyboard, persistence and recovery tests;
Android normalization/persistence JVM tests; and Android/iOS gesture/helper tests.
Android instrumentation is compiled locally but was not executed on a device in
this change. Swift syntax is checked; iOS requires Xcode validation on macOS.
