# Native icon parity and restored Main menu artwork

## Canonical installed app icon

The **installed application icon** is the same black/silver D&A TOOL vehicle
artwork on **Desktop, Android, and iOS**. It is a single **opaque, 1024×1024 RGB**
PNG, originally stored at `assets/ai-car-scanner-icon.png`.

The following app icon assets are tracked as the **exact same Git blob**:

| Platform | Asset | Usage |
| --- | --- | --- |
| Desktop | `assets/AI-Car-Scanner-master.png` | Windows build/release master |
| Desktop | `assets/AI-Car-Scanner-mobile.png` | PySide6 window/taskbar source icon |
| Android | `apps/mobile-android/app/src/main/res/drawable-nodpi/ic_launcher_foreground.png` | Adaptive installed app foreground, with 18dp safe-area inset |
| iOS | `apps/mobile-ios/AICarScanner/Assets.xcassets/AppIcon.appiconset/ai-car-scanner-icon.png` | Installed iOS app icon; opaque RGB, Xcode-compatible |

The old neon-blue car launcher is *not* selected as the installed icon.
Android `mipmap-anydpi-v26/ic_launcher.xml` loads the canonical image via
`ic_launcher_safezone.xml` and uses a black background. Android's
`minSdk=26` means this adaptive-icon path is available across supported
versions. The unrelated monochrome generic-car override was removed.

The Windows PyInstaller .spec now **stages PNG, WEBP and multi-resolution ICO
from the canonical master on every direct build**, without modifying tracked
artwork. The Git Bash and PowerShell release builders already stage/regenerate
from the master. The tracked legacy ICO/WEBP and Android density WEBPs may still
contain earlier artwork until regenerated; they are *not* the current v26
Android icon or the new Windows-build staged icon.

Before creating final platform releases, regenerate all tracked fallback files:

```bash
cd finalbuild
python scripts/regenerate_native_icons.py
python scripts/regenerate_native_icons.py --check
python -m pytest -q tests/test_native_app_icon_parity.py tests/test_issue_18_23_ui_contracts.py
```

After regeneration, review and commit the resulting PNG/ICO/WEBP updates.
Do not commit unreviewed user artwork or overwrite assets with a different
brand icon.

## Main menu

Each of the three clients again shows 3D page artwork **inside Main menu
cards**:

- Desktop: `MovableMenuTile(AdaptiveMenuTile)`, `_page_icon(page_id)`.
- Android: `LauncherTileContent` uses `DashboardIcon(id, 56.dp)`.
- iOS: `desktopMenu` uses `DesktopIcon(page:id)` at 64×64.

These are workflow icons from the shared 4×3 3D atlas; they are **different
in purpose** from the installed app icon. Top toolbar on Desktop still uses
compact sidebar-style icons on workflow pages and stays **hidden on Main menu**.
No Desktop left sidebar is reintroduced.

## Validation limitations

Git blob equality and source code were checked on the branch, but native
Windows icon embedding, Android emulator/icon masking and iOS installation
were not exercised on a device or emulator in this operation. Test the
built/installed icons (and launcher card rendering) before publishing.
