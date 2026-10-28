# UI/UX parity and native extension plan

Foundation changes no existing screen, icon or navigation order. Keep Desktop
`ui.py`/`demo_ui.py`, Android presentation components, iOS AutomotiveTheme and
existing launcher/vehicle assets. USER/CUSTOMER/ADMIN selectors belong in the
existing account/workspace area; MARKET is a portal entry available only to an
authorized merchant. Do not add a competing dashboard template.

Native milestone screens: login/profile, allowed-mode selection, owned vehicles,
workshop invitations, read-scope/expiry approval and immediate revoke. Later
monitoring, work orders and seller/admin panels must reuse themed components.
Use OS secure token stores, native permission dialogs and accessible controls.

API permission failures must not be hidden by UI role checks. Translate every
new label and diagnostic/error message to Armenian, Russian and English. No
native account screens are delivered by the first backend-only foundation;
existing diagnostic visual parity is retained, not claimed for future screens.
