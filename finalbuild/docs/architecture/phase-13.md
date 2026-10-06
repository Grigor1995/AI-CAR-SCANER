# Phase 13 — Diagnostic Decision Engine & Test Planning

Phase 13 turns the evidence/reasoning layer into a deterministic next-test planner.

## Design goals

- Keep DiagnosticSession as the central workflow object.
- Select the next diagnostic test using measurable criteria rather than LLM-only ranking.
- Prefer tests that can discriminate between current hypotheses.
- Include evidence fit, estimated information gain, cost, and safety risk.
- Preserve uncertainty; a test may support/disfavor a hypothesis without declaring a component failure.
- Require explicit safety confirmation for MEDIUM/HIGH risk test selection at the API boundary.

## Decision score

The current development implementation uses a transparent weighted score:

`0.50 * information_gain + 0.20 * evidence_fit + 0.15 * (1-cost_penalty) + 0.15 * (1-risk_penalty)`

Missing prerequisites introduce an additional penalty. The weights are configuration candidates for later empirical optimization.

## Information gain approximation

For the current hypothesis set, a candidate test is modeled as a binary discriminator between hypotheses it targets and the remaining hypotheses. Binary entropy is used as an inexpensive deterministic proxy. Production calibration should replace this proxy with empirical outcome probabilities from validated diagnostic cases.

## Safety model

Tests have a LOW/MEDIUM/HIGH risk label and safety notes. Medium/high selection requires an explicit API flag. The system does not authorize ECU programming or other unsafe write operations.

## Result feedback loop

`TestSelection -> TestResult -> Evidence -> HypothesisUpdate -> Re-analysis -> NewDecisionPlan`

A positive textual result may move a targeted hypothesis to `supported_by_test`; a negative/normal result may move it to `disfavored_by_test`. This is deliberately not equivalent to confirmed root cause.
