# Automatic monitoring — planned

No unattended diagnostic scheduler is implemented in the audited baseline or
first foundation slice. Daily is the product's default schedule, not a claim
that background scanning currently runs. Implement schedules only after scoped
vehicle/device access and explicit consent exist.

Proposed run states: scheduled -> running -> completed, or deferred / missed /
failed with a reason. Gateway must confirm adapter availability, ignition and
eligible read operations before collecting measurements. Absent hardware or
mobile background permission means deferred, never successful. Do not wake
ECUs repeatedly to satisfy a daily UI indicator.

Store timezone, next eligible UTC instant, daily/weekly/manual/custom rule,
quiet hours, severity threshold and cooldown. Required tests cover DST gaps and
folds, duplicate scheduler delivery, lost connections, revoked consent, expired
jobs and no-ignition availability. Use a supported local/backend gateway when
mobile OS restrictions prevent unattended work.
