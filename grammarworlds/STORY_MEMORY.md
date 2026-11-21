# Reusable annotations on intact stories

`story_memory.annotate(row)` keeps a generated story's full text, sampled token
order, positional coordinates and probabilistic token attributes. It adds
source-memory annotations and indexes **references** into that stream. It does
not extract standalone prose fragments or replace the original story with a
list of event sentences.

The [original seven-world export](runs/story_memory_20261107_v2/report.md) contains 140
generated samples (20 per original world), not 140 new original story families.
All 119 registered, pack-qualified event kinds occur in these samples and are
exposed as searchable annotations. Nineteen kinds have reviewed executable
mappings, through 17 bank rules. Unsupported events remain available as source
context; matching annotations alone never authorizes copying their effects.

The [expanded pool](runs/seed_worlds_20261107_v4/report.md) adds the remaining
16 Luna seed adaptations. All 20 seeds are now covered, alongside rescue, kite
and key: 23 runtime worlds. New memory documents include the original seed path
and text hash. Six additional movement rules bring the bank to 23 rules; the
new compound events remain annotated even when they lack a portable mapping.
The continuation experiment now defaults to this expanded pool and also accepts
older directories with fewer annotated worlds. It loads the full
`stories.memory.jsonl.gz` archive when available, falling back to per-world
`.memory.json` files. A single preview can omit a useful branch: the kite sail
variant, for example, contains no mending event. The complete archive preserves
both variants for retrieval.

## Token representation

A document contains `text`, the unchanged ordered `tokens`, interned
`attributes`, source entity observations, and an `events` index. Token records
look conceptually like this (the real export also retains positions and rotary
coordinates):

```json
{
  "id": 42,
  "token": "tape",
  "candidates": [{"probability": 1.0, "attributes": "4:a3"}],
  "memory": {
    "event_id": 5,
    "event_name": "mend",
    "status": "observed_source",
    "scope": "source_event_boundaries",
    "entity_observations": [{
      "entity": "tool",
      "binding_probability": 1.0,
      "confirmed_in_source_event": true,
      "before": {"location": "hero"},
      "after": {"location": "hero"}
    }],
    "mapping_rules": ["repair.paper", "repair.kite"]
  }
}
```

This sketch abbreviates the observation objects. Actual records retain complete
carrier fields, tags and changes. Event names describe meaning; document ID,
event ID and token positions identify occurrences. No character-span annotations
need to be authored. The event index stores token IDs and semantic evidence, not
a second collection of detached text chunks.

Two scopes are intentionally separate:

- `candidates` retains exactly what the source generator predicted at that
  token, including ambiguity. It is not rewritten using the eventual ending.
- `memory` describes the already completed source story. Its before/after state
  is historical evidence at source-event boundaries, not a new fact about a
  receiving-world token or a precise word-by-word simulation.

Some short-form source stories omit routine physical operations. Such events
have **no invented tokens**: they are indexed at a silent token boundary, and
the following token records their `prior_silent_events`. Final silent events
remain at the end boundary. Of 309 supported event occurrences, 122 have visible
tokens and 187 are explicitly silent history annotations. Every world contributes
at least one visibly narrated supported event in the export.

## Query and reuse

```python
from grammarworlds.storytelling.runtime import generate
from grammarworlds.story_memory import annotate, query, retrieve, generate_retrieved

document = annotate(generate("kite", 3000, continuations="expanded",
                             symbolic_heads=True))
hits = query([document], event_kind="mend", entity="target")
# Each hit names the document, event and original token IDs. Full context stays
# available through document['text'] and document['tokens'].

choices = retrieve(documents, receiving_world, operations=["patch_paper"])
result = generate_retrieved(documents, receiving_world, operations=["patch_paper"],
                            bindings={"worker": "ada"}, seed=7)
```

Queries can filter event kind, participating entity, pre-event entity property,
candidate action lemma or mapping availability. An action-lemma match can occur
inside a quotation, intention or negation; it is a **candidate annotation match**,
not proof that the lexical action physically happened. The event's replayed
effects and reviewed mapping remain the execution evidence.

Retrieval looks up the original event annotations, infers compatible target
bindings, tests them through the existing mapping bank and real target guards,
and returns a distribution over feasible rule/binding candidates. After an
event commits, query again against the updated world. Repair is unavailable
before Ada fetches the tape and becomes available afterward.

Repeated source samples with the same target rule/binding do not multiply its
weight: references accumulate under one candidate. Different rules retain their
own authored weights. This is not learned frequency estimation. `rule_factors`
is the existing explicit context-weight hook; no new learned attention is added.

The original export demonstration supplies operation filters and limited role
hints. It does not select donor event IDs, copy a donor sentence, or copy source
entity state. The continuation loop below removes those per-step filters.

## Sampled continuation loop

`memory_continuation.continue_story(documents, world, ...)` repeatedly retrieves
legal mappings, samples one target event, generates its words and attributes,
commits its physical effects and queries the resulting world. `prefix` accepts
zero or more concrete target events, for example:

```python
from grammarworlds.event_line_replay import paper_world
from grammarworlds.memory_continuation import continue_story

result = continue_story(documents, paper_world(), seed=7,
    prefix=[dict(op='intent', actor='ada', item='book'),
            dict(op='offer', actor='omar', listener='ada')])
```

The caller supplies annotated documents as before. An intent prefix implies a
`repaired` state goal through an explicit small rule, not English interpretation.
Alternatively, `goals` supplies `{entity, field: state|location, value}` predicates;
`goals=[]` disables goal inference. A goal is a desired world condition, not an
operation sequence. Prefix guards are checked, and failed prefixes raise without
changing the caller's world. `max_events` limits sampled events after the prefix.

`policy='plain'` samples using mapping weights and a fixed STOP weight.
`policy='contextual'` adds hand-authored multiplicative factors: state changes,
goal progress, one-step goal enabling, actor continuity, repeated actions and
revisited physical states. Placement goals are deferred while that object's
requested state transformation is unfinished. These are inspectable symbolic
attention features; there are no learned weights or source-order statistics.
The one-step lookahead simulates legal successor events; it cannot solve an
arbitrary long prerequisite chain.

Equivalent bound target actions are grouped across source mappings. Their base
weight is the maximum matching rule weight; references and matching rule IDs
are retained. Repeating a source example or adding synonymous mapping rules
does not multiply an action's vote. STOP is another normalized candidate, with
larger mass after the requested predicates are satisfied. It can still be
sampled early. `sampled_stop`, `exhausted` and `limit` are separate outcomes;
`goals_satisfied` records actual predicates, and STOP does not mark the world
solved. Without goals, stopping depends on whether any state progress occurred.

Event selection happens before conditional word/attribute generation. Each
decision records every candidate, probability, feature multiplier and source
reference. Each segment preserves its transfer audit and is independently
replay-verified. The combined token stream has fresh global positions and scene
indices into combined attribute tables. Semantic ambiguity remains inside the
selected event's word generation; unchosen event meanings are not maintained as
a whole-story posterior. Existing word heads read the current world/history;
this does not add attention over the full prior token-attribute stream.

```sh
.venv/bin/python -m grammarworlds.memory_continuation_experiment \
  --out /tmp/memory-continuation --count 20
.venv/bin/python -m unittest grammarworlds.test_memory_continuation -q
```

The experiment uses one intact seed-3000 document from each world and tests
plain/contextual sampling, dialogue prefixes, an ending predicate, no prefix,
and a richer craft fixture. See [samples and distributions](runs/memory_continuation_20261107_v2/report.md).
Missing entities/capabilities still are not imported. Activity selection in an
unconstrained craft world can remain disjointed; successful repair is not proof
of a developed story or satisfying ending.

## Expanded executable coverage

The default bank combines `mapping_bank/core.json`,
[`mapping_bank/story_tokens.json`](mapping_bank/story_tokens.json) and
[`mapping_bank/seed_stories.json`](mapping_bank/seed_stories.json). The original expansion's
rules cover typed fetching, placing and handoffs, support preparation, clay
shaping, a practiced drum solo, fixture repair and a moon drawing.

`reusable_operations.ReusableLines` adds five guarded target operations to the
existing catalog driver. Target capabilities, holder/location, material and
state constraints must be declared and satisfied. It never grants a source
character's skills to an existing target character. The drawing mapping matches
the source's Joy change and paper-to-drawing rename, but target execution keeps
the target's emotions/name and applies its declared drawing state. The full
source effects remain in the transfer audit.

The original seven-world coverage is:

| World | Annotated event kinds | Kinds with mapping support |
|---|---:|---:|
| Rescue | 13 | 1 |
| Kite | 13 | 3 |
| Key | 13 | 2 |
| Music | 16 | 3 |
| Greenhouse | 17 | 2 |
| Library | 21 | 4 |
| Pottery | 26 | 4 |

Water allocation, compound rescues, consent, checkout/reservation obligations,
and many transformations/endings remain annotated but not generally portable.
They are not reduced to simple transfers to manufacture coverage. The original
seven world implementations and their generated prose are unchanged.

## Validation and next work

Export replays every source, checks its text hash, reconstructs the full original
text from the token stream, and validates token/event references. Tests preserve
the original attribute posteriors, handle silent boundaries, exercise all seven
worlds, re-query after target state changes, reject missing capabilities and
prevent duplicated samples from inflating mapping mass.

The next useful additions are reviewed visible-event mappings, richer causal
continuation features and endings grounded in changed state. Existing token-label limitations
(embedded-object syntax roles and nominal-only place references) remain; this
layer does not pretend to repair them. No new Luna quality evaluation is claimed.

```sh
.venv/bin/python -m grammarworlds.story_memory_export \
  --out /tmp/story-memory --seed 3000 --count 20
.venv/bin/python -m unittest grammarworlds.test_story_memory -q
```

This follows the memeplex north star: reused meaning is attached to physical
target carriers and only compatible target operations affect persistent state.
The full memeplex algebra is still outside this prototype.

## Native mechanics transfer across the twenty-world pool

The [native-transfer adapter](NATIVE_TRANSFER.md) can now retrieve a compound
source event, bring its physical prerequisites and local mechanics into a
receiver, and generate through the existing annotated grammar. It complements
the strict mapping rules. Source-specific companions and character attributes
may leak deliberately, with an explicit import ledger; existing object state
is not reset. [Coverage and examples](runs/joined_transfer_20261107_v3/report.md).
