# Settings

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

PARTIALLY IMPLEMENTED target. Existing native theme/EN/HY/RU/EU-USA settings
retained. New account settings persist EN/HY/RU/FR, EU/USA, pressure and consumption
preferences, theme, IANA timezone, severity, delivery opt-ins, quiet hours and alert
frequency. French account preference is in Settings JSON; legacy /me language
remains its existing compatible enum. Full native French UI/report/AI translation
and automatic merging of local/account preferences remain unfinished.

Canonical engineering values unchanged. Tested boundary conversions support
km/h↔mph display, km→miles, C→F, kPa→bar/psi, L/100km→km/L/mpg_US,
Nm→lb-ft, kW→mechanical hp, L→US gallons. Inputs finite; consumption positive.
These domain helpers do not pretend every new unit selector exists in native UI.
Provider secrets never live in user settings JSON or account read output.
