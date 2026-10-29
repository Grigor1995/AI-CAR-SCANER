# Monitoring And Alerts

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

PARTIALLY IMPLEMENTED. Owner can persist DAILY (default), WEEKLY or CUSTOM
schedule with timezone/hour, explicit consent, enabled state and next due time.
Timezones validated with ZoneInfo; custom interval >=60 min limits requested rate.
Dispatcher endpoint is owner-scoped and idempotent per schedule/due timestamp.
No configured gateway yields DEFERRED; >1 day overdue yields MISSED. It stores a
run and one in-app notice, no synthetic scan/report and no vehicle command.

No background daemon, connected gateway, battery/ECU polling policy integration
or automatic scan is shipped. FAILED/COMPLETED are reserved statuses and cannot
be client-asserted through the current API. After a deferred occurrence the
schedule remains due; operator/user must reconnect/reschedule. Do not claim daily
unattended diagnostics works. Mobile suspension/disconnection is never bypassed.
In-app notifications are durable/readable. Email/SMS/push and contact verification
are BLOCKED pending provider setup; quiet hours/frequency/severity preferences
persist but do not yet drive an external delivery worker. No false SENT status.
