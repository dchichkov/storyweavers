# discovering_mistake interface notes

First-pass design only; coordinator relays and resolves these proposals. No peer
response is required to finish this assignment.

## discovering_mistake-01
- Recipient: observing; informing; coordinator
- Issue: acquiring contradictory evidence must not silently erase the belief
  whose revision the story needs to explain.
- Proposed resolution: versioned evidence acquisition returns an immutable,
  actor-accessible proposition with source, subject, scope/time, and event ID.
  Keep the prior belief revision available. Discovery explicitly supersedes it;
  receiving a claim alone does not prove that claim or compel acceptance.
- Affected stories/contracts: all three; evidence-to-revision handoff.
- First-pass reconciliation: observing-01 preserves conflicting priors and may
  initialize unknown beliefs; informing-01 delegates conflict revision here.
  Accept those boundaries provisionally. Acceptance of conflicting content must
  reference one revision, not execute a second independent belief overwrite.
- Status: proposed

## discovering_mistake-02
- Recipient: requesting; promising; refusing; coordinator
- Issue: recognizing an error is not repairing its consequences or discharging
  an obligation.
- Proposed resolution: discovery writes only epistemic state plus linked
  discrepancy/revision records. A subsequent choice may request help, refuse an
  unsafe task, inform someone, or leave the material problem unresolved. Each
  neighboring capability owns its own effects and outcome checks.
- Affected stories/contracts: harbor stop-work choice; library rescheduling;
  observatory withdrawal without replacement observation.
- Status: proposed

## discovering_mistake-03
- Recipient: observing; informing; coordinator
- Issue: trace-grounded QA can still expose hidden evidence or misclassify a
  changed world as a previously mistaken belief.
- Proposed resolution: compare propositions at matching subject, scope, and
  reference time; retain evidence/revision IDs and separately record rendered
  support spans. Distinguish disproved, unresolved, and outdated beliefs. QA
  abstains when the story omits the required support or a follow-up is ambiguous.
- Affected stories/contracts: library stale schedule versus wrong-day lookup;
  harbor ambiguous fault; observatory evidence-source retraction.
- First-pass reconciliation: observing-03 and informing-02 agree on separate
  observation/reference/delivery times. The library outline uses a wrong-day
  lookup, not a secretly changed schedule. COMPATIBILITY.md's unchanged-state
  rejection and pruning constraints are reflected in the proposal: actual test
  results/resources and meaningful revision records, never dummy failure flags.
- Status: proposed
