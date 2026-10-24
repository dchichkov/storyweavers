# Independent core boundary review

Reviewed 2026-10-22 against DECISIONS D01, D04, D07 and acceptance X1-X6.
Scope: `capabilities/core.py`, `codec.py`, `reading.py`. Changes by this reviewer
are limited to this report and `storyscenes/test_capability_boundaries.py`.
No infrastructure edits, commits, paid calls, or additional agents.

## Current result

The coordinator applied the fixes below. Rechecked the updated source and ran:

```bash
cd storyscenes
/opt/homebrew/bin/python3.12 -m unittest -v test_capability_boundaries test_capability_core test_capability_reading
```

**24 tests pass**, including all nine independent boundary tests and the 15
existing core/reading tests. No residual concrete failure was reproduced in
this recheck. This is not full X1-X6 acceptance or domain-family certification.

Before the fixes, the independent suite ran nine test methods and reported
15 assertion/subtest failures plus one replay error. The original 15 tests
already passed. Tests assert desired behavior directly; none are skipped or
marked expected-failure.

The system `/usr/bin/python3` is Python 3.9 and cannot import the existing
`dataclass(kw_only=True)` implementation. Use the Python 3.12 command above.

## Verified defects and fixes

Test identifiers below belong to
`test_capability_boundaries.CapabilityBoundaryTests`.

### R1: Rejection changed the declared action

Location: `core.Transaction.__init__`, `execute`. X2 / D04.

`test_rejected_handler_cannot_mutate_the_declared_action` initially returned
`None` after rejection but left `spec.actions[0].args['text']` changed. The
handler received the actual action through `tx.action`, bypassing staged writes.
This changed future execution/replay despite no committed event.

Small fix, now verified: isolate `tx.action` with a deep copy and check it for
untracked mutation on the successful path. Rejection now leaves the specification
unchanged. This deliberately faulty handler tests transaction isolation, not a
claim that a current domain handler was observed mutating its action.

### R2: Committed provenance was only shallowly frozen

Location: `core.Event`, event construction. X2 / D07.

`test_committed_event_payload_and_action_are_deeply_immutable` initially allowed
both appending an invented inspection to nested `event.data` and rewriting
`event.action.args['text']`. Both operations changed the committed event's
fingerprint without another event.

Small fix, now verified: recursively freeze committed mappings and sequences,
including the embedded action. Both mutation probes now leave history unchanged.

### R3: Change snapshots shared mutable record payloads

Location: `core.execute` change construction. X2 / D07.

`test_change_snapshots_do_not_alias_live_or_predecessor_records` initially changed
history by appending to either the predecessor state's record list or the new
state's record list. `Change.before` and `Change.after` held live record references.

Small fix, now verified: take independent frozen snapshots for both sides of a
change. The fixture uses a valid registered list-valued record to exercise the
general typed-record API; it is not evidence that a domain currently uses lists.

### R4: Selecting a repeated event lost its occurrence identity

Location: `core.execute` causes, `replay_selection`. X4-X5 / D07.

`test_pruning_second_event_only_use_preserves_its_identity` initially errored with
`CapabilityError: Selection changed event meaning; retain its missing dependencies`.
Two bounded event-only warnings produced `warning:1` and `warning:2`, but selecting
the latter retained no usage ancestry. Replay recreated it as `warning:1`.

Small fix, now verified: make each repeated use depend on its preceding use.
Retained replay now preserves the selected event, usage count, and exhaustion of
the finite budget. This does not require retaining unrelated events.

### R5: Intent access was validated only at initialization

Location: `core.Registry.initial`, `proposals`, `execute`. X3 / D07.

`test_intent_access_is_rechecked_after_access_changes` initially produced different
proposals after a registered access policy had denied the same query in both
branches. With hidden value zero the option was absent; with hidden value one it
was present and execution committed a warning. Both legal branches used identical
actions/counts. Initialization-time accessibility was treated as permanent.

Small fix, now verified: consult current intent validators before matching values
in both proposal and execution paths; retain the registry privately on state for
the proposal API. The fixture exercises dynamic policy callbacks, not a claim
that an existing immutable belief changed owners. It does not validate an agent
policy for omniscient author-side search.

### R6: Missing JSON version silently opted in

Location: `codec.world_from_data`, `WorldSpec.schema` default. X1 / D01.

`test_json_requires_an_explicit_schema_field` initially loaded an otherwise valid
JSON world after deleting its schema field. The Python constructor default silently
supplied the version, contradicting the explicit serialized version boundary.

Small fix, now verified: require the schema field with the supported exact value
at the JSON entry point. Explicit Python construction can retain its convenience
default without making unversioned JSON acceptable.

### R7: Top-level world metadata bypassed type checks

Location: `codec.world_from_data`, `core.Registry.initial`. X1-X2.

`test_json_world_metadata_is_strictly_typed` initially accepted all four malformed
values: `max_steps=true`, `max_steps=1.5`, `title=17`, and
`title=['not a string']`. Nested records were decoded strictly, but top-level
metadata was passed directly into a non-validating dataclass. A fractional step
budget could consequently permit more events than its declared numeric limit.

Small fix, now verified: require a string title and an exact integer step budget
in the shared initializer, in addition to existing nonempty/range checks.

### R8: Same-value writes fabricated empty enacted events

Location: `core.execute` meaningful-event guard. X2, X4 / D07.

`test_same_value_write_is_not_a_meaningful_enacted_event` initially committed
`noop:1` with `changes=()`, `data={}`, and an incremented usage count. A staged
replacement equal to the pre-state satisfied the guard before unchanged effects
were removed. There was no actual attempt, utterance, evidence, or state change.

Small fix, now verified: require an actual changed value or an explicit meaningful
event payload. Legitimate bounded event-only speech remains covered separately
by the original suite.

### R9: Follow-ups switched events and survived the wrong mask

Location: `reading.Reader.ask`, `follow_up`. X6 / D07.

`test_followup_preserves_the_explicitly_selected_event_not_first_support`
initially answered about `inspect:1` after an explicit question selecting
`inspect:2`. The selected statement supported both inspections, and `follow_up`
discarded the caller's selector in favor of `event_ids[0]`. Masking the second
inspection's reason still returned a supported answer about the first inspection.

Small fix, now verified: store the explicit event selector in conversation state
and carry it into follow-ups. The visible branch now uses only the second reason;
masking that reason now abstains instead of substituting the first event.

## Limits and remaining acceptance work

- These synthetic fixtures isolate shared infrastructure defects and do not
  replace physical/epistemic/social or frozen legacy tests. Full integration,
  domain postconditions, unchanged parent paths, and selected narrative motives
  still need the coordinator's broader acceptance evidence.
- Ordinary transitive support masking and exact spans pass in the existing
  reader suite. The independent regression adds masking under explicit event
  disambiguation, not duplicate normal support-chain tests.
- `reading.py` is a reader-support boundary, not an English entailment verifier.
  Rendered templates, natural full answers, causal second sentences, historical
  truth/lie wording, and manual prose/QA agreement still require inspection.
- No reader as-of/horizon behavior is certified here. `acquired_tick` metadata
  alone does not establish that a renderer excludes future evidence. This is
  remaining adapter/acceptance work, not a demand for generic NLP entailment or
  a demonstrated failure of the current reader-only API.
- The repaired boundaries support the memeplex north star by preserving embedded
  evidence, actor-accessible choices, immutable provenance, and compatible state
  transitions. This review does not claim those alone produce complete stories.
