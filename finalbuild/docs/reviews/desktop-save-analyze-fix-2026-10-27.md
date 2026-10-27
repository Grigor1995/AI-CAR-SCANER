# Desktop Save and analyze correction — 27 October 2026

The recorded symptom/DTC editor previously opened without a selected record.
Save silently returned when no item was selected; refreshing after a successful
save also cleared selection. No busy/completion state was shown, worker errors
were attached to the parent window rather than the modal editor, and the
recommended-test decision cache was not refreshed.

The editor now selects the first record, preserves identity/nearest selection
on refresh, disables duplicate submission while working, and shows inline
progress, success and retryable errors. An empty editor explains how to add
inputs and disables editing actions. Late completions cannot replace a different
active session. Successful saves refresh analysis and the decision plan, falling
back to the fresh analysis recommendations if only the plan request fails.
A completed save is distinguished from a subsequent analysis failure. DTC edits
preserve the recorded source and description. Analysis uses its own configurable
300-second request budget (`AI_CAR_ANALYSIS_TIMEOUT_S`); normal health/API calls
retain their short default timeout.

Validation: all five Desktop regression groups pass; source coverage 90.43%,
production-core coverage 90.83%. Seven focused Save/analyze cases pass, including
real Qt worker completion/failure, duplicate-click suppression, retry, session
ownership, empty state, preserved DTC metadata and recommendation refresh.
No physical OBD hardware, user-local server state or live GGUF inference was
claimed by these checks. No CI/CD was used.
