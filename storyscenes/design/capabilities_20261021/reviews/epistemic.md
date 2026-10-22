# Bounded Epistemic Cross-Review

Design review only. Sources: the observing, informing and discovering_mistake
proposals, COMPATIBILITY.md, and INTEGRATION_GATES.md. No implementation or test
execution is claimed. Preserve the proposals and legacy interpretation.

## Top Semantic Findings

1. **Belief writes have three entry points, not yet one owner.** Observing's
   Reusable contract permits initialization and matching-support refresh;
   informing's Writes and recipient updates permits nonconflicting adoption;
   discovering_mistake's Two candidate operations installs revisions. The latter's
   Cross-capability composition accepts this division, but no shared writer
   prevents duplicate updates or defines matching across time. Recommend one
   belief-update operation, invoked by explicit acquisition/adoption/revision
   decisions. Capabilities own their decisions and evidence, not independent
   writes to belief heads. Matching support adds provenance; a newer reference
   interval is not automatically the same proposition.

2. **Several stories omit the epistemic transition they require.** In observing,
   Observatory beat 5 revises a "current-use belief," although the premise only
   declares a valid six-o'clock belief. discovering_mistake requires an active
   prior belief for RegisterMismatch. Declare an explicit present extrapolation,
   or make the fresh view initialize a current belief without mistake discovery.
   In informing, Harbor's no-fresh-report intervention says Pavel becomes
   uncertain although he initially believes the gate open. Deferring clearance
   does not withdraw that belief. Record a supported withdrawal of present
   applicability, or retain the belief while deferring action. Likewise,
   discovering_mistake's Harbor occluded-indicator intervention must not make an
   accepted diagnosis uncertain merely because an attempted test was unreadable.

3. **Inscription-to-truth remains an implicit authority bridge.** Observing's
   Reads and legality correctly distinguishes reading a label from accepting
   its assertion. discovering_mistake's Library beats 2-4 treats ledger rows as
   decisive reservation evidence. That needs an explicit domain rule establishing
   the ledger's authoritative, current booking status; seeing ink alone is
   insufficient. Observatory's matching exposure IDs similarly needs an authored
   identity rule and accessible source-validity evidence. These are narrow
   policies, not universal trust or automatic belief revision.

4. **Time must attach to propositions, not just records.** All three contracts
   distinguish acquisition from reference time, consistent with G2. Informing
   additionally distinguishes attributed source times from verified provenance;
   preserve that distinction when observing supplies evidence. A timestamp proves
   what the strip says, not necessarily when an exposure occurred. Observing's
   Observatory QA can call six o'clock correct because an earlier observation is
   explicitly rendered; without it, abstain about historical accuracy. Later
   disagreement establishes "outdated" only with support for changed conditions,
   not merely because a claim is old. Otherwise retain unresolved applicability.

5. **Event-only meaning and reader support need shared dependencies.** Observing
   allows temporal reinspection; informing allows repeated receipt; discovery
   makes duplicate revision idempotent. These are compatible if a fresh inspection
   records a new sampling occasion, repeated speech records a distinct utterance,
   and neither creates independent-source corroboration. COMPATIBILITY.md and G4
   require bounded event-aware replay, not dummy flags or narrated search
   rejection. Retain evidence, replies and stated motives used by explanations;
   retaining every unused event solely to manufacture QA would undermine pruning.

## Smallest Common Interface

Use one opt-in epistemic schema, with capability-specific operations. A
proposition has subject, predicate, typed value/result, scope and reference
interval; explicit unknown is not false. Evidence/claim records retain source,
observer or speaker, acquisition/emission/delivery times, actual provenance,
attributed provenance and immutable parent IDs. Receipts identify which actor
accessed what; comprehension and adoption remain distinct.

An acquisition or response produces a proposed belief disposition with policy
and basis IDs. One validated update operation retains predecessor history and
commits the head exactly once. Conflict classification/revision requires the
discovering_mistake decision; a receipt alone never triggers it. Rejecting a
claim does not assert its opposite. Lack of evidence does not withdraw an
accepted belief without a stated applicability/support rule.

Access witnesses reference event-time physical-parent paths from carrying plus
observing-owned exposure, channel and attention checks. Moving a closed container
never discloses its contents. Distinguish failure to obtain access from an exact
negative observation over a complete declared domain. Physical access and social
permission are separate facts.

Requests and commitments reference action specifications and evidence IDs, not
belief writes or physical effects. Observing's Noor commitment and informing's
fresh-check request require explicit speech-act records; quoted intention is not
performed opening/checking. Fulfillment needs the separately owned action event.

Reader QA references selected support spans, events, entities and proposition
times. Annotation presence alone does not establish English entailment. Follow-ups
retain the claim/revision and temporal focus; simulator-only truth remains debug
material, not comprehension evidence.

## Five Falsifying Tests

1. Deliver a correction and a direct percept for the same conflict in either
   order. Require one explicit resolution/update, retained predecessors and no
   last-writer-wins overwrite. An unknown-prior case initializes without claiming
   discovery of an earlier mistake.
2. Read a wrong or outdated ledger/strip. Its inscription is acquired, but its
   assertion is not accepted without policy. Acquire an accurate old report
   after a hidden move: no current refresh, historical lie label or timestamp
   laundering. Mask historical support and suppress historical-truth QA.
3. Inspect an obscured shelf or shaft indicator. Record bounded failure/partial
   evidence, not global absence, an opposite diagnosis or silent withdrawal.
   Complete visible coverage must distinguish exact absence from unknown.
4. Move a closed container; request and promise an inspection without performing
   it. No content belief or fulfilled commitment appears. Perform an accessible
   inspection afterward and cite its actual physical-path witness.
5. Repeat one warning and reinspect an unchanged signal. Preserve meaningful
   receipts/sampling times through replay without invented corroboration or
   duplicate revision. Remove the reply or motive sentence: linked QA abstains
   rather than borrowing hidden trace information.

## Coordinator Decisions Required

Freeze the single belief-writer interface and its acquisition/adoption/revision
authorization rules; reference-interval equality and present-applicability policy;
inscription/source authority rules; physical access-witness ownership; and bounded
event-only retention/replay. Require explicit story support for every QA premise.
Keep all changes versioned; do not retrofit legacy Observe/Tell or scalar state.
